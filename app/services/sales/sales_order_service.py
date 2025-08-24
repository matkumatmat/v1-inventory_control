"""
Sales Order Service
===================

CRITICAL SERVICE untuk Sales Order processing dan workflow
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from ..base import CRUDService, transactional, audit_log
from ..exceptions import ValidationError, BusinessRuleError, NotFoundError
from ...models import (
    SalesOrder, SalesOrderItem, Customer, Product, TenderContract,
    PackingSlip, ShippingPlan, ShippingPlanItem
)
from ...schemas import (
    SalesOrderSchema, SalesOrderCreateSchema, SalesOrderUpdateSchema,
    SalesOrderItemSchema, SalesOrderItemCreateSchema, SalesOrderItemUpdateSchema
)

class SalesOrderService(CRUDService):
    """CRITICAL SERVICE untuk Sales Order management"""
    
    model_class = SalesOrder
    create_schema = SalesOrderCreateSchema
    update_schema = SalesOrderUpdateSchema
    response_schema = SalesOrderSchema
    search_fields = ['so_number', 'notes']
    
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None, 
                 allocation_service=None, shipping_plan_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)
        self.allocation_service = allocation_service
        self.shipping_plan_service = shipping_plan_service
    
    @transactional
    @audit_log('CREATE', 'SalesOrder')
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create sales order dengan validation"""
        # Validate SO number uniqueness
        so_number = data.get('so_number')
        if so_number:
            self._validate_unique_field(SalesOrder, 'so_number', so_number,
                                      error_message=f"SO number '{so_number}' already exists")
        
        # Validate customer exists dan active
        customer = self._validate_customer(data['customer_id'])
        
        # Validate tender contract if provided
        if data.get('tender_contract_id'):
            self._validate_tender_contract(data['tender_contract_id'], customer.id)
        
        # Set SO type based on tender contract
        data['is_tender_so'] = bool(data.get('tender_contract_id'))
        
        # Validate dates
        self._validate_so_dates(data)
        
        # Create SO
        so_data = super().create(data)
        
        # Send notification
        self._send_notification('SALES_ORDER_CREATED', ['sales_team', 'warehouse_team'], {
            'so_id': so_data['id'],
            'so_number': so_number,
            'customer_name': customer.name,
            'total_quantity': data.get('total_quantity', 0),
            'is_tender': data.get('is_tender_so', False)
        })
        
        return so_data
    
    @transactional
    @audit_log('ADD_ITEM', 'SalesOrder')
    def add_item(self, so_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add item ke sales order"""
        so = self._get_or_404(SalesOrder, so_id)
        
        # Validate SO can be modified
        if so.status not in ['PENDING', 'CONFIRMED']:
            raise BusinessRuleError(f"Cannot add items to SO with status {so.status}")
        
        # Validate product exists
        product = self._get_or_404(Product, item_data['product_id'])
        
        # Validate line number uniqueness
        line_number = item_data.get('line_number')
        if line_number:
            existing_item = self.db_session.query(SalesOrderItem).filter(
                and_(
                    SalesOrderItem.sales_order_id == so_id,
                    SalesOrderItem.line_number == line_number
                )
            ).first()
            
            if existing_item:
                raise ValidationError(f"Line number {line_number} already exists")
        
        # Set SO ID
        item_data['sales_order_id'] = so_id
        
        # Validate item data
        validated_data = SalesOrderItemCreateSchema().load(item_data)
        
        # Create item
        item = SalesOrderItem(**validated_data)
        self._set_audit_fields(item)
        
        self.db_session.add(item)
        self.db_session.flush()
        
        # Update SO totals
        self._update_so_totals(so_id)
        
        return SalesOrderItemSchema().dump(item)
    
    @transactional
    @audit_log('UPDATE_ITEM', 'SalesOrder')
    def update_item(self, item_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update sales order item"""
        item = self._get_or_404(SalesOrderItem, item_id)
        so = item.sales_order
        
        # Validate SO can be modified
        if so.status not in ['PENDING', 'CONFIRMED']:
            raise BusinessRuleError(f"Cannot update items in SO with status {so.status}")
        
        # Validate shipping constraint
        if item.quantity_shipped > 0:
            restricted_fields = ['product_id', 'quantity_ordered']
            for field in restricted_fields:
                if field in data:
                    raise BusinessRuleError(f"Cannot update {field} - item has been shipped")
        
        # Update item
        validated_data = SalesOrderItemUpdateSchema().load(data)
        for key, value in validated_data.items():
            setattr(item, key, value)
        
        self._set_audit_fields(item, is_update=True)
        
        # Update SO totals
        self._update_so_totals(so.id)
        
        return SalesOrderItemSchema().dump(item)
    
    @transactional
    @audit_log('CONFIRM', 'SalesOrder')
    def confirm_order(self, so_id: int) -> Dict[str, Any]:
        """Confirm sales order dan trigger allocation"""
        so = self._get_or_404(SalesOrder, so_id)
        
        if so.status != 'PENDING':
            raise BusinessRuleError(f"Only pending orders can be confirmed. Current status: {so.status}")
        
        # Validate SO has items
        items_count = self.db_session.query(SalesOrderItem).filter(
            SalesOrderItem.sales_order_id == so_id
        ).count()
        
        if items_count == 0:
            raise BusinessRuleError("Cannot confirm order without items")
        
        # Confirm order
        so.status = 'CONFIRMED'
        so.confirmed_by = self.current_user
        so.confirmed_date = datetime.utcnow()
        self._set_audit_fields(so, is_update=True)
        
        # Auto-create shipping plan
        if self.shipping_plan_service:
            shipping_plan_data = {
                'sales_order_id': so_id,
                'plan_date': date.today(),
                'planned_delivery_date': so.requested_delivery_date or (date.today() + timedelta(days=7)),
                'priority_level': so.priority_level,
                'is_express': so.is_urgent
            }
            
            shipping_plan = self.shipping_plan_service.create_shipping_plan(shipping_plan_data)
            
            # Auto-add all SO items to shipping plan
            self.shipping_plan_service.add_items_from_so(shipping_plan['id'], so_id)
        
        # Send notification
        self._send_notification('SALES_ORDER_CONFIRMED', ['warehouse_team', 'sales_team'], {
            'so_id': so_id,
            'so_number': so.so_number,
            'customer_name': so.customer.name,
            'total_items': items_count
        })
        
        return self.response_schema().dump(so)

    @transactional
    @audit_log('CANCEL', 'SalesOrder')
    def cancel_order(self, so_id: int, reason: str = None) -> Dict[str, Any]:
        """Cancel sales order"""
        so = self._get_or_404(SalesOrder, so_id)
        
        if so.status == 'CANCELLED':
            raise BusinessRuleError("Order is already cancelled")
        
        if so.status == 'COMPLETED':
            raise BusinessRuleError("Cannot cancel completed order")
        
        # Check if any items have been shipped
        shipped_items = self.db_session.query(SalesOrderItem).filter(
            and_(
                SalesOrderItem.sales_order_id == so_id,
                SalesOrderItem.quantity_shipped > 0
            )
        ).count()
        
        if shipped_items > 0:
            raise BusinessRuleError("Cannot cancel order with shipped items")
        
        # Cancel order
        so.status = 'CANCELLED'
        so.cancelled_by = self.current_user
        so.cancelled_date = datetime.utcnow()
        if reason:
            so.notes = f"Cancelled: {reason}. {so.notes or ''}"
        
        self._set_audit_fields(so, is_update=True)
        
        # Release any allocations (this would be implemented when you have allocations)
        # TODO: Release allocations for this SO
        
        # Send notification
        self._send_notification('SALES_ORDER_CANCELLED', ['sales_team', 'warehouse_team'], {
            'so_id': so_id,
            'so_number': so.so_number,
            'customer_name': so.customer.name,
            'reason': reason
        })
        
        return self.response_schema().dump(so)
    
    def get_by_so_number(self, so_number: str) -> Dict[str, Any]:
        """Get SO by SO number"""
        so = self.db_session.query(SalesOrder).filter(
            SalesOrder.so_number == so_number
        ).first()
        
        if not so:
            raise NotFoundError('SalesOrder', so_number)
        
        return self.response_schema().dump(so)
    
    def get_so_with_items(self, so_id: int) -> Dict[str, Any]:
        """Get SO dengan all items"""
        so = self._get_or_404(SalesOrder, so_id)
        
        items = self.db_session.query(SalesOrderItem).filter(
            SalesOrderItem.sales_order_id == so_id
        ).order_by(SalesOrderItem.line_number.asc()).all()
        
        so_data = self.response_schema().dump(so)
        so_data['items'] = SalesOrderItemSchema(many=True).dump(items)
        
        return so_data
    
    def get_pending_orders(self, customer_id: int = None) -> List[Dict[str, Any]]:
        """Get pending sales orders"""
        query = self.db_session.query(SalesOrder).filter(
            SalesOrder.status.in_(['PENDING', 'CONFIRMED'])
        )
        
        if customer_id:
            query = query.filter(SalesOrder.customer_id == customer_id)
        
        query = query.order_by(SalesOrder.so_date.desc())
        
        orders = query.all()
        return self.response_schema(many=True).dump(orders)
    
    def get_overdue_orders(self, days_overdue: int = 0) -> List[Dict[str, Any]]:
        """Get overdue sales orders"""
        cutoff_date = date.today() - timedelta(days=days_overdue)
        
        query = self.db_session.query(SalesOrder).filter(
            and_(
                SalesOrder.status.in_(['CONFIRMED', 'PROCESSING']),
                SalesOrder.requested_delivery_date <= cutoff_date
            )
        ).order_by(SalesOrder.requested_delivery_date.asc())
        
        orders = query.all()
        
        result = []
        for order in orders:
            order_data = self.response_schema().dump(order)
            order_data['days_overdue'] = (date.today() - order.requested_delivery_date).days
            result.append(order_data)
        
        return result
    
    def get_so_summary_report(self, start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """Get SO summary report"""
        query = self.db_session.query(SalesOrder)
        
        if start_date:
            query = query.filter(SalesOrder.so_date >= start_date)
        if end_date:
            query = query.filter(SalesOrder.so_date <= end_date)
        
        orders = query.all()
        
        # Calculate summary
        summary = {
            'total_orders': len(orders),
            'by_status': {},
            'by_customer': {},
            'by_date': {},
            'tender_orders': 0,
            'regular_orders': 0,
            'total_value': 0
        }
        
        for order in orders:
            # By status
            status = order.status
            if status not in summary['by_status']:
                summary['by_status'][status] = {'count': 0, 'total_value': 0}
            summary['by_status'][status]['count'] += 1
            summary['by_status'][status]['total_value'] += order.total_amount or 0
            
            # By customer
            customer_key = f"{order.customer_id}_{order.customer.name}"
            if customer_key not in summary['by_customer']:
                summary['by_customer'][customer_key] = {'count': 0, 'total_value': 0}
            summary['by_customer'][customer_key]['count'] += 1
            summary['by_customer'][customer_key]['total_value'] += order.total_amount or 0
            
            # By date
            date_key = order.so_date.isoformat()
            if date_key not in summary['by_date']:
                summary['by_date'][date_key] = {'count': 0, 'total_value': 0}
            summary['by_date'][date_key]['count'] += 1
            summary['by_date'][date_key]['total_value'] += order.total_amount or 0
            
            # Tender vs Regular
            if order.is_tender_so:
                summary['tender_orders'] += 1
            else:
                summary['regular_orders'] += 1
            
            summary['total_value'] += order.total_amount or 0
        
        return summary
    
    def _validate_customer(self, customer_id: int) -> Customer:
        """Validate customer exists dan active"""
        customer = self._get_or_404(Customer, customer_id)
        
        if not customer.is_active:
            raise ValidationError(f"Customer {customer.name} is not active")
        
        if customer.status != 'ACTIVE':
            raise ValidationError(f"Customer {customer.name} is not in active status")
        
        return customer
    
    def _validate_tender_contract(self, contract_id: int, customer_id: int):
        """Validate tender contract"""
        contract = self._get_or_404(TenderContract, contract_id)
        
        if contract.status != 'ACTIVE':
            raise ValidationError(f"Tender contract {contract.contract_number} is not active")
        
        if contract.end_date and contract.end_date <= date.today():
            raise ValidationError(f"Tender contract {contract.contract_number} has expired")
        
        # Additional validation for customer eligibility could be added here
    
    def _validate_so_dates(self, data: Dict[str, Any]):
        """Validate SO date relationships"""
        so_date = data.get('so_date', date.today())
        requested_delivery = data.get('requested_delivery_date')
        
        if requested_delivery and requested_delivery <= so_date:
            raise ValidationError("Requested delivery date must be after SO date")
    
    def _update_so_totals(self, so_id: int):
        """Update SO total quantities dan amounts"""
        so = self._get_or_404(SalesOrder, so_id)
        
        # Calculate totals from items
        items = self.db_session.query(SalesOrderItem).filter(
            SalesOrderItem.sales_order_id == so_id
        ).all()
        
        total_quantity = sum(item.quantity_ordered for item in items)
        total_amount = sum((item.quantity_ordered * (item.unit_price or 0)) for item in items)
        
        so.total_quantity = total_quantity
        so.total_amount = total_amount
        self._set_audit_fields(so, is_update=True)


class SalesOrderItemService(CRUDService):
    """Service untuk Sales Order Item management"""
    
    model_class = SalesOrderItem
    create_schema = SalesOrderItemCreateSchema
    update_schema = SalesOrderItemUpdateSchema
    response_schema = SalesOrderItemSchema
    
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)
    
    def get_items_by_so(self, so_id: int) -> List[Dict[str, Any]]:
        """Get all items untuk SO"""
        items = self.db_session.query(SalesOrderItem).filter(
            SalesOrderItem.sales_order_id == so_id
        ).order_by(SalesOrderItem.line_number.asc()).all()
        
        return self.response_schema(many=True).dump(items)
    
    def get_pending_items_for_shipping(self, so_id: int = None) -> List[Dict[str, Any]]:
        """Get items yang pending untuk shipping"""
        query = self.db_session.query(SalesOrderItem).join(SalesOrder).filter(
            and_(
                SalesOrder.status.in_(['CONFIRMED', 'PROCESSING']),
                SalesOrderItem.quantity_shipped < SalesOrderItem.quantity_ordered
            )
        )
        
        if so_id:
            query = query.filter(SalesOrderItem.sales_order_id == so_id)
        
        items = query.all()
        
        result = []
        for item in items:
            item_data = self.response_schema().dump(item)
            item_data['pending_quantity'] = item.quantity_ordered - item.quantity_shipped
            result.append(item_data)
        
        return result