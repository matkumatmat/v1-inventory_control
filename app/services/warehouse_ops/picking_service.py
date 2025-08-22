"""
Picking Services
================

CRITICAL SERVICES untuk Picking operations - core warehouse workflow
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from ..base import CRUDService, transactional, audit_log
from ..exceptions import ValidationError, BusinessRuleError, PickingError, NotFoundError
from ...models import (
    PickingList, PickingListItem, PickingOrder, PickingOrderItem,
    ShippingPlan, ShippingPlanItem, Allocation, RackAllocation, Rack
)
from ...schemas import (
    PickingListSchema, PickingListCreateSchema, PickingListUpdateSchema,
    PickingListItemSchema, PickingListItemCreateSchema,
    PickingOrderSchema, PickingOrderCreateSchema, PickingOrderUpdateSchema,
    PickingOrderItemSchema, PickingOrderItemCreateSchema
)

class PickingListService(CRUDService):
    """CRITICAL SERVICE untuk Picking List management"""
    
    model_class = PickingList
    create_schema = PickingListCreateSchema
    update_schema = PickingListUpdateSchema
    response_schema = PickingListSchema
    search_fields = ['picking_list_number', 'notes']
    
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None, 
                 allocation_service=None, movement_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)
        self.allocation_service = allocation_service
        self.movement_service = movement_service
    
    @transactional
    @audit_log('CREATE', 'PickingList')
    def create_from_shipping_plan(self, shipping_plan_id: int, 
                                 picker_user_id: str = None) -> Dict[str, Any]:
        """Create picking list dari shipping plan"""
        shipping_plan = self._get_or_404(ShippingPlan, shipping_plan_id)
        
        if shipping_plan.status != 'ALLOCATED':
            raise BusinessRuleError(f"Shipping plan must be allocated. Current status: {shipping_plan.status}")
        
        # Generate picking list number
        picking_list_number = self._generate_picking_list_number()
        
        # Create picking list
        picking_list_data = {
            'picking_list_number': picking_list_number,
            'shipping_plan_id': shipping_plan_id,
            'picker_user_id': picker_user_id,
            'picking_date': date.today(),
            'priority_level': shipping_plan.priority_level,
            'is_express': shipping_plan.is_express,
            'status': 'PENDING'
        }
        
        validated_data = self.create_schema().load(picking_list_data)
        picking_list = PickingList(**validated_data)
        self._set_audit_fields(picking_list)
        
        self.db.add(picking_list)
        self.db.flush()
        
        # Create picking list items dari shipping plan items
        shipping_plan_items = self.db.query(ShippingPlanItem).filter(
            ShippingPlanItem.shipping_plan_id == shipping_plan_id
        ).all()
        
        created_items = []
        for sp_item in shipping_plan_items:
            # Get rack locations untuk product
            rack_locations = self._get_rack_locations_for_product(
                sp_item.product_id, sp_item.planned_quantity
            )
            
            for rack_location in rack_locations:
                if sp_item.planned_quantity <= 0:
                    break
                
                pick_qty = min(sp_item.planned_quantity, rack_location['available_quantity'])
                
                # Create picking list item
                picking_item_data = {
                    'picking_list_id': picking_list.id,
                    'shipping_plan_item_id': sp_item.id,
                    'product_id': sp_item.product_id,
                    'rack_id': rack_location['rack_id'],
                    'allocation_id': rack_location['allocation_id'],
                    'quantity_to_pick': pick_qty,
                    'rack_location': rack_location['rack_code'],
                    'position_details': rack_location['position_details']
                }
                
                validated_item_data = PickingListItemCreateSchema().load(picking_item_data)
                picking_item = PickingListItem(**validated_item_data)
                self._set_audit_fields(picking_item)
                
                self.db.add(picking_item)
                created_items.append(picking_item)
                
                sp_item.planned_quantity -= pick_qty
        
        self.db.flush()
        
        # Update picking list totals
        self._update_picking_list_totals(picking_list.id)
        
        # Send notification
        self._send_notification('PICKING_LIST_CREATED', ['warehouse_team'], {
            'picking_list_id': picking_list.id,
            'picking_list_number': picking_list_number,
            'total_items': len(created_items),
            'picker_user_id': picker_user_id
        })
        
        return self.response_schema().dump(picking_list)
    
    @transactional
    @audit_log('ASSIGN', 'PickingList')
    def assign_picker(self, picking_list_id: int, picker_user_id: str) -> Dict[str, Any]:
        """Assign picker ke picking list"""
        picking_list = self._get_or_404(PickingList, picking_list_id)
        
        if picking_list.status not in ['PENDING', 'ASSIGNED']:
            raise PickingError(f"Cannot assign picker to list with status {picking_list.status}")
        
        # Assign picker
        picking_list.picker_user_id = picker_user_id
        picking_list.status = 'ASSIGNED'
        picking_list.assigned_date = datetime.utcnow()
        self._set_audit_fields(picking_list, is_update=True)
        
        # Send notification
        self._send_notification('PICKING_LIST_ASSIGNED', [picker_user_id], {
            'picking_list_id': picking_list_id,
            'picking_list_number': picking_list.picking_list_number,
            'total_items': picking_list.total_items
        })
        
        return self.response_schema().dump(picking_list)
    
    @transactional
    @audit_log('START', 'PickingList')
    def start_picking(self, picking_list_id: int) -> Dict[str, Any]:
        """Start picking process"""
        picking_list = self._get_or_404(PickingList, picking_list_id)
        
        if picking_list.status != 'ASSIGNED':
            raise PickingError(f"Can only start assigned picking lists. Current status: {picking_list.status}")
        
        # Start picking
        picking_list.status = 'IN_PROGRESS'
        picking_list.started_date = datetime.utcnow()
        self._set_audit_fields(picking_list, is_update=True)
        
        # Reserve stock untuk all items
        if self.allocation_service:
            self._reserve_stock_for_picking(picking_list_id)
        
        return self.response_schema().dump(picking_list)
    
    @transactional
    @audit_log('COMPLETE', 'PickingList')
    def complete_picking(self, picking_list_id: int, 
                        completion_notes: str = None) -> Dict[str, Any]:
        """Complete picking list"""
        picking_list = self._get_or_404(PickingList, picking_list_id)
        
        if picking_list.status != 'IN_PROGRESS':
            raise PickingError(f"Can only complete in-progress picking lists. Current status: {picking_list.status}")
        
        # Validate all items are picked
        unpicked_items = self.db.query(PickingListItem).filter(
            and_(
                PickingListItem.picking_list_id == picking_list_id,
                PickingListItem.quantity_picked < PickingListItem.quantity_to_pick
            )
        ).count()
        
        if unpicked_items > 0:
            raise PickingError(f"Cannot complete picking list with {unpicked_items} unpicked items")
        
        # Complete picking
        picking_list.status = 'COMPLETED'
        picking_list.completed_date = datetime.utcnow()
        picking_list.completion_notes = completion_notes
        self._set_audit_fields(picking_list, is_update=True)
        
        # Auto-create packing order
        packing_order_data = self._create_packing_order_from_picking(picking_list_id)
        
        # Send notification
        self._send_notification('PICKING_LIST_COMPLETED', ['warehouse_team', 'packing_team'], {
            'picking_list_id': picking_list_id,
            'picking_list_number': picking_list.picking_list_number,
            'picker_user_id': picking_list.picker_user_id,
            'packing_order_id': packing_order_data.get('id') if packing_order_data else None
        })
        
        return self.response_schema().dump(picking_list)
    
    def get_picking_list_with_items(self, picking_list_id: int) -> Dict[str, Any]:
        """Get picking list dengan all items"""
        picking_list = self._get_or_404(PickingList, picking_list_id)
        
        items = self.db.query(PickingListItem).filter(
            PickingListItem.picking_list_id == picking_list_id
        ).order_by(PickingListItem.rack_location.asc()).all()
        
        picking_list_data = self.response_schema().dump(picking_list)
        picking_list_data['items'] = PickingListItemSchema(many=True).dump(items)
        
        return picking_list_data
    
    def get_pending_picking_lists(self, picker_user_id: str = None) -> List[Dict[str, Any]]:
        """Get pending picking lists"""
        query = self.db.query(PickingList).filter(
            PickingList.status.in_(['PENDING', 'ASSIGNED'])
        )
        
        if picker_user_id:
            query = query.filter(PickingList.picker_user_id == picker_user_id)
        
        query = query.order_by(PickingList.priority_level.desc(), PickingList.picking_date.asc())
        
        picking_lists = query.all()
        return self.response_schema(many=True).dump(picking_lists)
    
    def get_picker_workload(self, picker_user_id: str) -> Dict[str, Any]:
        """Get workload untuk picker"""
        # Current active picking lists
        active_lists = self.db.query(PickingList).filter(
            and_(
                PickingList.picker_user_id == picker_user_id,
                PickingList.status.in_(['ASSIGNED', 'IN_PROGRESS'])
            )
        ).all()
        
        # Completed today
        today = date.today()
        completed_today = self.db.query(PickingList).filter(
            and_(
                PickingList.picker_user_id == picker_user_id,
                PickingList.status == 'COMPLETED',
                func.date(PickingList.completed_date) == today
            )
        ).count()
        
        # Performance metrics
        total_items_active = sum(pl.total_items for pl in active_lists)
        
        return {
            'picker_user_id': picker_user_id,
            'active_picking_lists': len(active_lists),
            'total_items_pending': total_items_active,
            'completed_today': completed_today,
            'workload_status': 'HIGH' if len(active_lists) > 3 else 'NORMAL'
        }
    
    def _generate_picking_list_number(self) -> str:
        """Generate unique picking list number"""
        today = date.today()
        prefix = f"PL{today.strftime('%y%m%d')}"
        
        last_picking_list = self.db.query(PickingList).filter(
            PickingList.picking_list_number.like(f"{prefix}%")
        ).order_by(PickingList.id.desc()).first()
        
        if last_picking_list:
            last_seq = int(last_picking_list.picking_list_number[-4:])
            next_seq = last_seq + 1
        else:
            next_seq = 1
        
        return f"{prefix}{next_seq:04d}"
    
    def _get_rack_locations_for_product(self, product_id: int, 
                                       required_quantity: int) -> List[Dict[str, Any]]:
        """Get rack locations untuk product dengan FEFO strategy"""
        # Get rack allocations untuk product dengan available stock
        from ...models import Batch
        
        query = self.db.query(RackAllocation).join(Allocation).join(Batch).join(Rack).filter(
            and_(
                Batch.product_id == product_id,
                Allocation.status == 'active',
                (Allocation.allocated_quantity - Allocation.shipped_quantity) > 0
            )
        ).order_by(Batch.expiry_date.asc(), Batch.received_date.asc())
        
        rack_allocations = query.all()
        
        locations = []
        for rack_alloc in rack_allocations:
            allocation = rack_alloc.allocation
            available_qty = allocation.allocated_quantity - allocation.shipped_quantity
            
            if available_qty > 0:
                locations.append({
                    'rack_id': rack_alloc.rack_id,
                    'rack_code': rack_alloc.rack.rack_code,
                    'allocation_id': allocation.id,
                    'available_quantity': available_qty,
                    'position_details': rack_alloc.position_details,
                    'expiry_date': allocation.batch.expiry_date
                })
        
        return locations
    
    def _reserve_stock_for_picking(self, picking_list_id: int):
        """Reserve stock untuk picking"""
        items = self.db.query(PickingListItem).filter(
            PickingListItem.picking_list_id == picking_list_id
        ).all()
        
        for item in items:
            if self.allocation_service:
                try:
                    self.allocation_service.reserve_for_picking(
                        allocation_id=item.allocation_id,
                        quantity=item.quantity_to_pick
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to reserve stock for item {item.id}: {str(e)}")
    
    def _update_picking_list_totals(self, picking_list_id: int):
        """Update picking list totals"""
        picking_list = self._get_or_404(PickingList, picking_list_id)
        
        items = self.db.query(PickingListItem).filter(
            PickingListItem.picking_list_id == picking_list_id
        ).all()
        
        total_items = len(items)
        total_quantity_to_pick = sum(item.quantity_to_pick for item in items)
        total_quantity_picked = sum(item.quantity_picked for item in items)
        
        picking_list.total_items = total_items
        picking_list.total_quantity_to_pick = total_quantity_to_pick
        picking_list.total_quantity_picked = total_quantity_picked
        self._set_audit_fields(picking_list, is_update=True)
    
    def _create_packing_order_from_picking(self, picking_list_id: int) -> Optional[Dict[str, Any]]:
        """Create packing order dari completed picking list"""
        # This would be implemented when PackingOrderService is available
        # For now, return None
        return None


class PickingOrderService(CRUDService):
    """Service untuk Picking Order management (individual picker tasks)"""
    
    model_class = PickingOrder
    create_schema = PickingOrderCreateSchema
    update_schema = PickingOrderUpdateSchema
    response_schema = PickingOrderSchema
    search_fields = ['picking_order_number']
    
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None, movement_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)
        self.movement_service = movement_service
    
    @transactional
    @audit_log('PICK_ITEM', 'PickingOrder')
    def pick_item(self, picking_order_item_id: int, quantity_picked: int,
                 picker_notes: str = None) -> Dict[str, Any]:
        """Record picked quantity untuk item"""
        item = self._get_or_404(PickingOrderItem, picking_order_item_id)
        picking_order = item.picking_order
        
        if picking_order.status != 'IN_PROGRESS':
            raise PickingError(f"Cannot pick from order with status {picking_order.status}")
        
        # Validate quantity
        if quantity_picked > item.quantity_to_pick:
            raise PickingError(f"Cannot pick {quantity_picked}. Max pickable: {item.quantity_to_pick}")
        
        if quantity_picked < 0:
            raise ValidationError("Picked quantity cannot be negative")
        
        # Update picked quantity
        item.quantity_picked = quantity_picked
        item.picked_date = datetime.utcnow()
        item.picker_notes = picker_notes
        self._set_audit_fields(item, is_update=True)
        
        # Create movement record
        if self.movement_service and item.allocation_id:
            self.movement_service.create_picking_movement(
                allocation_id=item.allocation_id,
                quantity=quantity_picked,
                picking_order_id=picking_order.id,
                source_rack_id=item.rack_id
            )
        
        # Update picking order progress
        self._update_picking_order_progress(picking_order.id)
        
        return PickingOrderItemSchema().dump(item)
    
    @transactional
    @audit_log('COMPLETE', 'PickingOrder')
    def complete_picking_order(self, picking_order_id: int) -> Dict[str, Any]:
        """Complete picking order"""
        picking_order = self._get_or_404(PickingOrder, picking_order_id)
        
        if picking_order.status != 'IN_PROGRESS':
            raise PickingError(f"Can only complete in-progress orders. Current status: {picking_order.status}")
        
        # Validate all items are processed
        unprocessed_items = self.db.query(PickingOrderItem).filter(
            and_(
                PickingOrderItem.picking_order_id == picking_order_id,
                PickingOrderItem.quantity_picked == 0
            )
        ).count()
        
        if unprocessed_items > 0:
            raise PickingError(f"Cannot complete order with {unprocessed_items} unprocessed items")
        
        # Complete order
        picking_order.status = 'COMPLETED'
        picking_order.completed_date = datetime.utcnow()
        self._set_audit_fields(picking_order, is_update=True)
        
        return self.response_schema().dump(picking_order)
    
    def _update_picking_order_progress(self, picking_order_id: int):
        """Update picking order progress"""
        picking_order = self._get_or_404(PickingOrder, picking_order_id)
        
        items = self.db.query(PickingOrderItem).filter(
            PickingOrderItem.picking_order_id == picking_order_id
        ).all()
        
        total_items = len(items)
        completed_items = len([item for item in items if item.quantity_picked > 0])
        
        picking_order.total_items = total_items
        picking_order.completed_items = completed_items
        
        # Auto-complete if all items done
        if completed_items == total_items and picking_order.status == 'IN_PROGRESS':
            picking_order.status = 'COMPLETED'
            picking_order.completed_date = datetime.utcnow()
        
        self._set_audit_fields(picking_order, is_update=True)