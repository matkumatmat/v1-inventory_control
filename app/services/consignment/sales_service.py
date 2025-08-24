"""
Consignment Sales Service
=========================

Service untuk Consignment Sales management
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ..base import CRUDService, transactional, audit_log
from ..exceptions import ValidationError, BusinessRuleError, ConsignmentError, NotFoundError
from ...models import ConsignmentSale, Consignment, ConsignmentItem
from ...schemas import ConsignmentSaleSchema, ConsignmentSaleCreateSchema, ConsignmentSaleUpdateSchema

class ConsignmentSalesService(CRUDService):
    """Service untuk Consignment Sales management"""
    
    model_class = ConsignmentSale
    create_schema = ConsignmentSaleCreateSchema
    update_schema = ConsignmentSaleUpdateSchema
    response_schema = ConsignmentSaleSchema
    search_fields = ['sale_number', 'end_customer_name', 'invoice_number']
    
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)
    
    @transactional
    @audit_log('CREATE', 'ConsignmentSale')
    def record_sale(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Record consignment sale"""
        # Validate consignment item exists
        consignment_item = self._get_or_404(ConsignmentItem, data['consignment_item_id'])
        consignment = consignment_item.consignment
        
        # Validate sale quantity
        quantity_sold = data['quantity_sold']
        available_qty = consignment_item.quantity_shipped - consignment_item.quantity_sold
        
        if quantity_sold > available_qty:
            raise ConsignmentError(f"Cannot sell {quantity_sold}. Available: {available_qty}")
        
        # Calculate commission
        unit_price = data['unit_price']
        total_value = quantity_sold * unit_price
        commission_rate = data.get('commission_rate') or consignment.commission_rate or 0
        commission_amount = total_value * (commission_rate / 100)
        net_amount = total_value - commission_amount
        
        # Update data dengan calculated values
        data.update({
            'consignment_id': consignment.id,
            'sale_number': self._generate_sale_number(),
            'total_value': total_value,
            'commission_rate': commission_rate,
            'commission_amount': commission_amount,
            'net_amount': net_amount,
            'reported_by': self.current_user,
            'reported_date': datetime.utcnow()
        })
        
        # Create sale
        sale_data = super().create(data)
        
        # Update consignment item
        consignment_item.quantity_sold += quantity_sold
        
        # Update item status
        if consignment_item.quantity_sold >= consignment_item.quantity_shipped:
            consignment_item.status = 'SOLD'
        elif consignment_item.quantity_sold > 0:
            consignment_item.status = 'PARTIALLY_SOLD'
        
        self._set_audit_fields(consignment_item, is_update=True)
        
        # Update consignment status
        self._update_consignment_status(consignment.id)
        
        # Send notification
        self._send_notification('CONSIGNMENT_SALE_RECORDED', ['sales_team'], {
            'sale_id': sale_data['id'],
            'sale_number': data['sale_number'],
            'consignment_number': consignment.consignment_number,
            'quantity_sold': quantity_sold,
            'total_value': total_value
        })
        
        return sale_data
    
    @transactional
    @audit_log('VERIFY', 'ConsignmentSale')
    def verify_sale(self, sale_id: int, verification_notes: str = None) -> Dict[str, Any]:
        """Verify consignment sale"""
        sale = self._get_or_404(ConsignmentSale, sale_id)
        
        if sale.status != 'PENDING':
            raise ConsignmentError(f"Can only verify pending sales. Current status: {sale.status}")
        
        # Verify sale
        sale.status = 'CONFIRMED'
        sale.verified_by = self.current_user
        sale.verified_date = datetime.utcnow()
        
        if verification_notes:
            sale.notes = f"Verified: {verification_notes}. {sale.notes or ''}"
        
        self._set_audit_fields(sale, is_update=True)
        
        return self.response_schema().dump(sale)
    
    @transactional
    @audit_log('CANCEL', 'ConsignmentSale')
    def cancel_sale(self, sale_id: int, reason: str) -> Dict[str, Any]:
        """Cancel consignment sale"""
        sale = self._get_or_404(ConsignmentSale, sale_id)
        
        if sale.status == 'PAID':
            raise ConsignmentError("Cannot cancel paid sales")
        
        # Revert consignment item quantities
        consignment_item = sale.consignment_item
        consignment_item.quantity_sold -= sale.quantity_sold
        
        # Update item status
        if consignment_item.quantity_sold == 0:
            consignment_item.status = 'SHIPPED'
        elif consignment_item.quantity_sold < consignment_item.quantity_shipped:
            consignment_item.status = 'PARTIALLY_SOLD'
        
        self._set_audit_fields(consignment_item, is_update=True)
        
        # Cancel sale
        sale.status = 'CANCELLED'
        sale.notes = f"Cancelled: {reason}. {sale.notes or ''}"
        self._set_audit_fields(sale, is_update=True)
        
        # Update consignment status
        self._update_consignment_status(sale.consignment_id)
        
        return self.response_schema().dump(sale)
    
    def get_sales_by_consignment(self, consignment_id: int) -> List[Dict[str, Any]]:
        """Get all sales untuk consignment"""
        sales = self.db_session.query(ConsignmentSale).filter(
            ConsignmentSale.consignment_id == consignment_id
        ).order_by(ConsignmentSale.sale_date.desc()).all()
        
        return self.response_schema(many=True).dump(sales)
    
    def get_sales_summary(self, consignment_id: int = None, 
                         start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """Get sales summary"""
        query = self.db_session.query(ConsignmentSale)
        
        if consignment_id:
            query = query.filter(ConsignmentSale.consignment_id == consignment_id)
        
        if start_date:
            query = query.filter(ConsignmentSale.sale_date >= start_date)
        if end_date:
            query = query.filter(ConsignmentSale.sale_date <= end_date)
        
        sales = query.all()
        
        # Calculate summary
        total_sales = len(sales)
        total_quantity = sum(sale.quantity_sold for sale in sales)
        total_value = sum(sale.total_value for sale in sales)
        total_commission = sum(sale.commission_amount for sale in sales)
        total_net = sum(sale.net_amount for sale in sales)
        
        # By status
        by_status = {}
        for sale in sales:
            status = sale.status
            if status not in by_status:
                by_status[status] = {'count': 0, 'total_value': 0}
            by_status[status]['count'] += 1
            by_status[status]['total_value'] += sale.total_value
        
        return {
            'summary': {
                'total_sales': total_sales,
                'total_quantity': total_quantity,
                'total_value': total_value,
                'total_commission': total_commission,
                'total_net': total_net,
                'average_sale_value': total_value / total_sales if total_sales > 0 else 0
            },
            'by_status': by_status
        }
    
    def _generate_sale_number(self) -> str:
        """Generate unique sale number"""
        today = date.today()
        prefix = f"CSL{today.strftime('%y%m%d')}"
        
        last_sale = self.db_session.query(ConsignmentSale).filter(
            ConsignmentSale.sale_number.like(f"{prefix}%")
        ).order_by(ConsignmentSale.id.desc()).first()
        
        if last_sale:
            last_seq = int(last_sale.sale_number[-4:])
            next_seq = last_seq + 1
        else:
            next_seq = 1
        
        return f"{prefix}{next_seq:04d}"
    
    def _update_consignment_status(self, consignment_id: int):
        """Update consignment status berdasarkan item sales"""
        consignment = self._get_or_404(Consignment, consignment_id)
        
        items = self.db_session.query(ConsignmentItem).filter(
            ConsignmentItem.consignment_id == consignment_id
        ).all()
        
        total_shipped = sum(item.quantity_shipped for item in items)
        total_sold = sum(item.quantity_sold for item in items)
        
        # Update consignment totals
        consignment.total_quantity_sold = total_sold
        
        # Update status
        if total_sold == 0:
            if consignment.status == 'RECEIVED_BY_CUSTOMER':
                pass  # Keep current status
        elif total_sold >= total_shipped:
            consignment.status = 'FULLY_SOLD'
        else:
            consignment.status = 'PARTIALLY_SOLD'
        
        self._set_audit_fields(consignment, is_update=True)