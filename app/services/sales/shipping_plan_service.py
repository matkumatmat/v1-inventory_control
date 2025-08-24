"""
Shipping Plan Service
=====================

Service untuk Shipping Plan management dan planning logic
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ..base import CRUDService, transactional, audit_log
from ..exceptions import ValidationError, BusinessRuleError, NotFoundError
from ...models import (
    ShippingPlan, ShippingPlanItem, SalesOrder, SalesOrderItem, 
    Customer, Product
)
from ...schemas import (
    ShippingPlanSchema, ShippingPlanCreateSchema, ShippingPlanUpdateSchema,
    ShippingPlanItemSchema, ShippingPlanItemCreateSchema, ShippingPlanItemUpdateSchema
)

class ShippingPlanService(CRUDService):
    """Service untuk Shipping Plan management"""
    
    model_class = ShippingPlan
    create_schema = ShippingPlanCreateSchema
    update_schema = ShippingPlanUpdateSchema
    response_schema = ShippingPlanSchema
    search_fields = ['plan_number', 'notes']
    
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None, allocation_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)
        self.allocation_service = allocation_service
    
    @transactional
    @audit_log('CREATE', 'ShippingPlan')
    def create_shipping_plan(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create shipping plan dengan auto-generated plan number"""
        # Validate SO exists
        so = self._get_or_404(SalesOrder, data['sales_order_id'])
        
        if so.status not in ['CONFIRMED', 'PROCESSING']:
            raise BusinessRuleError(f"Cannot create shipping plan for SO with status {so.status}")
        
        # Generate plan number
        data['plan_number'] = self._generate_plan_number()
        
        # Validate dates
        self._validate_plan_dates(data)
        
        # Create plan
        plan_data = super().create(data)
        
        # Send notification
        self._send_notification('SHIPPING_PLAN_CREATED', ['warehouse_team', 'logistics_team'], {
            'plan_id': plan_data['id'],
            'plan_number': data['plan_number'],
            'so_number': so.so_number,
            'customer_name': so.customer.name,
            'planned_delivery_date': data.get('planned_delivery_date')
        })
        
        return plan_data
    
    @transactional
    @audit_log('ADD_ITEMS', 'ShippingPlan')
    def add_items_from_so(self, plan_id: int, so_id: int, 
                         item_ids: List[int] = None) -> List[Dict[str, Any]]:
        """Add items from SO ke shipping plan"""
        plan = self._get_or_404(ShippingPlan, plan_id)
        so = self._get_or_404(SalesOrder, so_id)
        
        # Validate plan can be modified
        if plan.status not in ['DRAFT', 'PLANNING']:
            raise BusinessRuleError(f"Cannot modify plan with status {plan.status}")
        
        # Get SO items
        query = self.db_session.query(SalesOrderItem).filter(
            SalesOrderItem.sales_order_id == so_id
        )
        
        if item_ids:
            query = query.filter(SalesOrderItem.id.in_(item_ids))
        
        so_items = query.all()
        
        created_items = []
        for so_item in so_items:
            # Check if item already in plan
            existing_item = self.db_session.query(ShippingPlanItem).filter(
                and_(
                    ShippingPlanItem.shipping_plan_id == plan_id,
                    ShippingPlanItem.sales_order_item_id == so_item.id
                )
            ).first()
            
            if existing_item:
                continue  # Skip if already added
            
            # Calculate pending quantity
            pending_qty = so_item.quantity_ordered - so_item.quantity_shipped
            
            if pending_qty <= 0:
                continue  # Skip if nothing to ship
            
            # Create shipping plan item
            plan_item_data = {
                'shipping_plan_id': plan_id,
                'sales_order_item_id': so_item.id,
                'product_id': so_item.product_id,
                'planned_quantity': pending_qty,
                'priority_level': plan.priority_level,
                'special_instructions': so_item.special_instructions
            }
            
            validated_data = ShippingPlanItemCreateSchema().load(plan_item_data)
            plan_item = ShippingPlanItem(**validated_data)
            self._set_audit_fields(plan_item)
            
            self.db_session.add(plan_item)
            self.db_session.flush()
            
            created_items.append(ShippingPlanItemSchema().dump(plan_item))
        
        # Update plan totals
        self._update_plan_totals(plan_id)
        
        return created_items
    
    @transactional
    @audit_log('CONFIRM', 'ShippingPlan')
    def confirm_plan(self, plan_id: int) -> Dict[str, Any]:
        """Confirm shipping plan dan trigger allocations"""
        plan = self._get_or_404(ShippingPlan, plan_id)
        
        if plan.status != 'DRAFT':
            raise BusinessRuleError(f"Only draft plans can be confirmed. Current status: {plan.status}")
        
        # Validate plan has items
        items_count = self.db_session.query(ShippingPlanItem).filter(
            ShippingPlanItem.shipping_plan_id == plan_id
        ).count()
        
        if items_count == 0:
            raise BusinessRuleError("Cannot confirm plan without items")
        
        # Confirm plan
        plan.status = 'CONFIRMED'
        plan.confirmed_by = self.current_user
        plan.confirmed_date = datetime.utcnow()
        self._set_audit_fields(plan, is_update=True)
        
        # Auto-allocate stock for items if allocation service available
        if self.allocation_service:
            self._auto_allocate_plan_items(plan_id)
        
        # Send notification
        self._send_notification('SHIPPING_PLAN_CONFIRMED', ['warehouse_team', 'logistics_team'], {
            'plan_id': plan_id,
            'plan_number': plan.plan_number,
            'total_items': items_count
        })
        
        return self.response_schema().dump(plan)
    
    @transactional
    @audit_log('ALLOCATE', 'ShippingPlan')
    def allocate_plan_items(self, plan_id: int, allocation_strategy: str = 'FEFO') -> Dict[str, Any]:
        """Allocate stock untuk all items dalam plan"""
        plan = self._get_or_404(ShippingPlan, plan_id)
        
        if plan.status != 'CONFIRMED':
            raise BusinessRuleError("Only confirmed plans can be allocated")
        
        # Get plan items yang belum allocated
        plan_items = self.db_session.query(ShippingPlanItem).filter(
            and_(
                ShippingPlanItem.shipping_plan_id == plan_id,
                ShippingPlanItem.allocated_quantity < ShippingPlanItem.planned_quantity
            )
        ).all()
        
        allocation_results = []
        total_allocated = 0
        
        for item in plan_items:
            try:
                pending_qty = item.planned_quantity - item.allocated_quantity
                
                if pending_qty <= 0:
                    continue
                
                # Auto-allocate using allocation service
                if self.allocation_service:
                    allocations = self.allocation_service.auto_allocate_by_strategy(
                        product_id=item.product_id,
                        quantity=pending_qty,
                        allocation_type_id=1,  # Regular allocation
                        customer_id=plan.sales_order.customer_id,
                        strategy=allocation_strategy
                    )
                    
                    # Update allocated quantity
                    allocated_qty = sum(alloc['allocated_quantity'] for alloc in allocations)
                    item.allocated_quantity += allocated_qty
                    self._set_audit_fields(item, is_update=True)
                    
                    allocation_results.append({
                        'item_id': item.id,
                        'product_id': item.product_id,
                        'requested_quantity': pending_qty,
                        'allocated_quantity': allocated_qty,
                        'allocations': allocations
                    })
                    
                    total_allocated += allocated_qty
                    
            except Exception as e:
                allocation_results.append({
                    'item_id': item.id,
                    'product_id': item.product_id,
                    'requested_quantity': pending_qty,
                    'allocated_quantity': 0,
                    'error': str(e)
                })
        
        # Update plan status if fully allocated
        if self._is_plan_fully_allocated(plan_id):
            plan.status = 'ALLOCATED'
            self._set_audit_fields(plan, is_update=True)
        
        return {
            'plan_id': plan_id,
            'total_allocated': total_allocated,
            'allocation_results': allocation_results
        }
    
    def get_plan_with_items(self, plan_id: int) -> Dict[str, Any]:
        """Get plan dengan all items"""
        plan = self._get_or_404(ShippingPlan, plan_id)
        
        items = self.db_session.query(ShippingPlanItem).filter(
            ShippingPlanItem.shipping_plan_id == plan_id
        ).all()
        
        plan_data = self.response_schema().dump(plan)
        plan_data['items'] = ShippingPlanItemSchema(many=True).dump(items)
        
        return plan_data
    
    def get_pending_plans(self, customer_id: int = None) -> List[Dict[str, Any]]:
        """Get pending shipping plans"""
        query = self.db_session.query(ShippingPlan).filter(
            ShippingPlan.status.in_(['CONFIRMED', 'ALLOCATED'])
        )
        
        if customer_id:
            query = query.join(SalesOrder).filter(SalesOrder.customer_id == customer_id)
        
        query = query.order_by(ShippingPlan.planned_delivery_date.asc())
        
        plans = query.all()
        return self.response_schema(many=True).dump(plans)
    
    def get_overdue_plans(self) -> List[Dict[str, Any]]:
        """Get overdue shipping plans"""
        today = date.today()
        
        query = self.db_session.query(ShippingPlan).filter(
            and_(
                ShippingPlan.status.in_(['CONFIRMED', 'ALLOCATED', 'PROCESSING']),
                ShippingPlan.planned_delivery_date < today
            )
        ).order_by(ShippingPlan.planned_delivery_date.asc())
        
        plans = query.all()
        
        result = []
        for plan in plans:
            plan_data = self.response_schema().dump(plan)
            plan_data['days_overdue'] = (today - plan.planned_delivery_date).days
            result.append(plan_data)
        
        return result
    
    def _generate_plan_number(self) -> str:
        """Generate unique plan number"""
        today = date.today()
        prefix = f"SP{today.strftime('%y%m%d')}"
        
        # Get next sequence number
        last_plan = self.db_session.query(ShippingPlan).filter(
            ShippingPlan.plan_number.like(f"{prefix}%")
        ).order_by(ShippingPlan.id.desc()).first()
        
        if last_plan:
            last_seq = int(last_plan.plan_number[-4:])
            next_seq = last_seq + 1
        else:
            next_seq = 1
        
        return f"{prefix}{next_seq:04d}"
    
    def _validate_plan_dates(self, data: Dict[str, Any]):
        """Validate plan date relationships"""
        plan_date = data.get('plan_date', date.today())
        planned_delivery = data.get('planned_delivery_date')
        
        if planned_delivery and planned_delivery <= plan_date:
            raise ValidationError("Planned delivery date must be after plan date")
    
    def _update_plan_totals(self, plan_id: int):
        """Update plan total quantities"""
        plan = self._get_or_404(ShippingPlan, plan_id)
        
        items = self.db_session.query(ShippingPlanItem).filter(
            ShippingPlanItem.shipping_plan_id == plan_id
        ).all()
        
        total_items = len(items)
        total_planned_qty = sum(item.planned_quantity for item in items)
        total_allocated_qty = sum(item.allocated_quantity for item in items)
        
        plan.total_items = total_items
        plan.total_planned_quantity = total_planned_qty
        plan.total_allocated_quantity = total_allocated_qty
        self._set_audit_fields(plan, is_update=True)
    
    def _auto_allocate_plan_items(self, plan_id: int):
        """Auto-allocate items ketika plan confirmed"""
        try:
            self.allocate_plan_items(plan_id, allocation_strategy='FEFO')
        except Exception as e:
            self.logger.warning(f"Auto-allocation failed for plan {plan_id}: {str(e)}")
    
    def _is_plan_fully_allocated(self, plan_id: int) -> bool:
        """Check if plan fully allocated"""
        unallocated_items = self.db_session.query(ShippingPlanItem).filter(
            and_(
                ShippingPlanItem.shipping_plan_id == plan_id,
                ShippingPlanItem.allocated_quantity < ShippingPlanItem.planned_quantity
            )
        ).count()
        
        return unallocated_items == 0