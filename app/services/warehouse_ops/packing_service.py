"""
Packing Services
================

CRITICAL SERVICES untuk Packing operations
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ..base import CRUDService, transactional, audit_log
from ..exceptions import ValidationError, BusinessRuleError, PackingError, NotFoundError
from ...models import (
    PackingOrder, PackingBox, PackingBoxItem, PickingList, 
    PickingListItem, Allocation
)
from ...schemas import (
    PackingOrderSchema, PackingOrderCreateSchema, PackingOrderUpdateSchema,
    PackingBoxSchema, PackingBoxCreateSchema, PackingBoxUpdateSchema,
    PackingBoxItemSchema, PackingBoxItemCreateSchema
)

class PackingOrderService(CRUDService):
    """CRITICAL SERVICE untuk Packing Order management"""
    
    model_class = PackingOrder
    create_schema = PackingOrderCreateSchema
    update_schema = PackingOrderUpdateSchema
    response_schema = PackingOrderSchema
    search_fields = ['packing_order_number', 'notes']
    
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None, 
                 allocation_service=None, movement_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)
        self.allocation_service = allocation_service
        self.movement_service = movement_service
    
    @transactional
    @audit_log('CREATE', 'PackingOrder')
    def create_from_picking_list(self, picking_list_id: int, 
                               packer_user_id: str = None) -> Dict[str, Any]:
        """Create packing order dari completed picking list"""
        picking_list = self._get_or_404(PickingList, picking_list_id)
        
        if picking_list.status != 'COMPLETED':
            raise BusinessRuleError(f"Picking list must be completed. Current status: {picking_list.status}")
        
        # Generate packing order number
        packing_order_number = self._generate_packing_order_number()
        
        # Create packing order
        packing_order_data = {
            'packing_order_number': packing_order_number,
            'picking_list_id': picking_list_id,
            'shipping_plan_id': picking_list.shipping_plan_id,
            'packer_user_id': packer_user_id,
            'packing_date': date.today(),
            'priority_level': picking_list.priority_level,
            'is_express': picking_list.is_express,
            'status': 'PENDING'
        }
        
        validated_data = self.create_schema().load(packing_order_data)
        packing_order = PackingOrder(**validated_data)
        self._set_audit_fields(packing_order)
        
        self.db_session.add(packing_order)
        self.db_session.flush()
        
        # Update picking list status
        picking_list.status = 'PACKED'
        self._set_audit_fields(picking_list, is_update=True)
        
        # Send notification
        self._send_notification('PACKING_ORDER_CREATED', ['packing_team'], {
            'packing_order_id': packing_order.id,
            'packing_order_number': packing_order_number,
            'picking_list_number': picking_list.picking_list_number,
            'packer_user_id': packer_user_id
        })
        
        return self.response_schema().dump(packing_order)
    
    @transactional
    @audit_log('ASSIGN', 'PackingOrder')
    def assign_packer(self, packing_order_id: int, packer_user_id: str) -> Dict[str, Any]:
        """Assign packer ke packing order"""
        packing_order = self._get_or_404(PackingOrder, packing_order_id)
        
        if packing_order.status not in ['PENDING', 'ASSIGNED']:
            raise PackingError(f"Cannot assign packer to order with status {packing_order.status}")
        
        # Assign packer
        packing_order.packer_user_id = packer_user_id
        packing_order.status = 'ASSIGNED'
        packing_order.assigned_date = datetime.utcnow()
        self._set_audit_fields(packing_order, is_update=True)
        
        # Send notification
        self._send_notification('PACKING_ORDER_ASSIGNED', [packer_user_id], {
            'packing_order_id': packing_order_id,
            'packing_order_number': packing_order.packing_order_number
        })
        
        return self.response_schema().dump(packing_order)
    
    @transactional
    @audit_log('START', 'PackingOrder')
    def start_packing(self, packing_order_id: int) -> Dict[str, Any]:
        """Start packing process"""
        packing_order = self._get_or_404(PackingOrder, packing_order_id)
        
        if packing_order.status != 'ASSIGNED':
            raise PackingError(f"Can only start assigned orders. Current status: {packing_order.status}")
        
        # Start packing
        packing_order.status = 'IN_PROGRESS'
        packing_order.started_date = datetime.utcnow()
        self._set_audit_fields(packing_order, is_update=True)
        
        return self.response_schema().dump(packing_order)
    
    @transactional
    @audit_log('COMPLETE', 'PackingOrder')
    def complete_packing(self, packing_order_id: int, 
                        completion_notes: str = None) -> Dict[str, Any]:
        """Complete packing order"""
        packing_order = self._get_or_404(PackingOrder, packing_order_id)
        
        if packing_order.status != 'IN_PROGRESS':
            raise PackingError(f"Can only complete in-progress orders. Current status: {packing_order.status}")
        
        # Validate has packing boxes
        boxes_count = self.db_session.query(PackingBox).filter(
            PackingBox.packing_order_id == packing_order_id
        ).count()
        
        if boxes_count == 0:
            raise PackingError("Cannot complete packing order without boxes")
        
        # Complete packing
        packing_order.status = 'COMPLETED'
        packing_order.completed_date = datetime.utcnow()
        packing_order.completion_notes = completion_notes
        self._set_audit_fields(packing_order, is_update=True)
        
        # Update total boxes
        packing_order.total_boxes = boxes_count
        
        # Auto-update allocation shipped quantities
        self._update_shipped_quantities(packing_order_id)
        
        # Send notification
        self._send_notification('PACKING_ORDER_COMPLETED', ['warehouse_team', 'shipping_team'], {
            'packing_order_id': packing_order_id,
            'packing_order_number': packing_order.packing_order_number,
            'total_boxes': boxes_count,
            'packer_user_id': packing_order.packer_user_id
        })
        
        return self.response_schema().dump(packing_order)
    
    def get_packing_order_with_boxes(self, packing_order_id: int) -> Dict[str, Any]:
        """Get packing order dengan all boxes"""
        packing_order = self._get_or_404(PackingOrder, packing_order_id)
        
        boxes = self.db_session.query(PackingBox).filter(
            PackingBox.packing_order_id == packing_order_id
        ).order_by(PackingBox.box_number.asc()).all()
        
        packing_order_data = self.response_schema().dump(packing_order)
        packing_order_data['boxes'] = PackingBoxSchema(many=True).dump(boxes)
        
        return packing_order_data
    
    def get_pending_packing_orders(self, packer_user_id: str = None) -> List[Dict[str, Any]]:
        """Get pending packing orders"""
        query = self.db_session.query(PackingOrder).filter(
            PackingOrder.status.in_(['PENDING', 'ASSIGNED'])
        )
        
        if packer_user_id:
            query = query.filter(PackingOrder.packer_user_id == packer_user_id)
        
        query = query.order_by(PackingOrder.priority_level.desc(), PackingOrder.packing_date.asc())
        
        packing_orders = query.all()
        return self.response_schema(many=True).dump(packing_orders)
    
    def get_ready_for_shipment(self) -> List[Dict[str, Any]]:
        """Get packing orders yang ready untuk shipment"""
        query = self.db_session.query(PackingOrder).filter(
            PackingOrder.status == 'COMPLETED'
        ).order_by(PackingOrder.completed_date.asc())
        
        packing_orders = query.all()
        return self.response_schema(many=True).dump(packing_orders)
    
    def _generate_packing_order_number(self) -> str:
        """Generate unique packing order number"""
        today = date.today()
        prefix = f"PO{today.strftime('%y%m%d')}"
        
        last_order = self.db_session.query(PackingOrder).filter(
            PackingOrder.packing_order_number.like(f"{prefix}%")
        ).order_by(PackingOrder.id.desc()).first()
        
        if last_order:
            last_seq = int(last_order.packing_order_number[-4:])
            next_seq = last_seq + 1
        else:
            next_seq = 1
        
        return f"{prefix}{next_seq:04d}"
    
    def _update_shipped_quantities(self, packing_order_id: int):
        """Update shipped quantities untuk allocations"""
        # Get all items dalam boxes
        box_items = self.db_session.query(PackingBoxItem).join(PackingBox).filter(
            PackingBox.packing_order_id == packing_order_id
        ).all()
        
        # Group by allocation
        allocation_quantities = {}
        for item in box_items:
            allocation_id = item.allocation_id
            if allocation_id not in allocation_quantities:
                allocation_quantities[allocation_id] = 0
            allocation_quantities[allocation_id] += item.quantity_packed
        
        # Update allocations
        for allocation_id, shipped_qty in allocation_quantities.items():
            if self.allocation_service:
                try:
                    self.allocation_service.ship_allocation(
                        allocation_id=allocation_id,
                        quantity=shipped_qty,
                        reference_type='PackingOrder',
                        reference_id=packing_order_id
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to update shipped quantity for allocation {allocation_id}: {str(e)}")


class PackingBoxService(CRUDService):
    """Service untuk Packing Box management"""
    
    model_class = PackingBox
    create_schema = PackingBoxCreateSchema
    update_schema = PackingBoxUpdateSchema
    response_schema = PackingBoxSchema
    search_fields = ['box_barcode', 'tracking_number']
    
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)
    
    @transactional
    @audit_log('CREATE', 'PackingBox')
    def create_box(self, packing_order_id: int, box_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create packing box"""
        packing_order = self._get_or_404(PackingOrder, packing_order_id)
        
        if packing_order.status != 'IN_PROGRESS':
            raise PackingError(f"Can only create boxes for in-progress orders. Current status: {packing_order.status}")
        
        # Generate box number
        box_number = self._get_next_box_number(packing_order_id)
        
        # Generate box barcode
        box_barcode = self._generate_box_barcode(packing_order_id, box_number)
        
        # Create box
        box_data.update({
            'packing_order_id': packing_order_id,
            'box_number': box_number,
            'box_barcode': box_barcode,
            'packed_by': self.current_user,
            'packed_date': datetime.utcnow()
        })
        
        return super().create(box_data)
    
    @transactional
    @audit_log('ADD_ITEM', 'PackingBox')
    def add_item_to_box(self, box_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add item ke packing box"""
        box = self._get_or_404(PackingBox, box_id)
        
        # Validate allocation exists
        allocation = self._get_or_404(Allocation, item_data['allocation_id'])
        
        # Validate quantity
        available_qty = allocation.allocated_quantity - allocation.shipped_quantity
        if item_data['quantity_packed'] > available_qty:
            raise PackingError(f"Cannot pack {item_data['quantity_packed']}. Available: {available_qty}")
        
        # Create box item
        item_data['packing_box_id'] = box_id
        item_data['product_id'] = allocation.batch.product_id
        
        validated_data = PackingBoxItemCreateSchema().load(item_data)
        box_item = PackingBoxItem(**validated_data)
        self._set_audit_fields(box_item)
        
        self.db_session.add(box_item)
        self.db_session.flush()
        
        # Update box totals
        self._update_box_totals(box_id)
        
        return PackingBoxItemSchema().dump(box_item)
    
    @transactional
    @audit_log('SEAL', 'PackingBox')
    def seal_box(self, box_id: int, final_weight: float = None) -> Dict[str, Any]:
        """Seal packing box"""
        box = self._get_or_404(PackingBox, box_id)
        
        if box.is_sealed:
            raise PackingError("Box is already sealed")
        
        # Validate box has items
        items_count = self.db_session.query(PackingBoxItem).filter(
            PackingBoxItem.packing_box_id == box_id
        ).count()
        
        if items_count == 0:
            raise PackingError("Cannot seal empty box")
        
        # Seal box
        box.is_sealed = True
        box.sealed_date = datetime.utcnow()
        box.sealed_by = self.current_user
        if final_weight:
            box.actual_weight = final_weight
        
        self._set_audit_fields(box, is_update=True)
        
        return self.response_schema().dump(box)
    
    def get_box_with_items(self, box_id: int) -> Dict[str, Any]:
        """Get box dengan all items"""
        box = self._get_or_404(PackingBox, box_id)
        
        items = self.db_session.query(PackingBoxItem).filter(
            PackingBoxItem.packing_box_id == box_id
        ).all()
        
        box_data = self.response_schema().dump(box)
        box_data['items'] = PackingBoxItemSchema(many=True).dump(items)
        
        return box_data
    
    def get_boxes_by_packing_order(self, packing_order_id: int) -> List[Dict[str, Any]]:
        """Get all boxes untuk packing order"""
        boxes = self.db_session.query(PackingBox).filter(
            PackingBox.packing_order_id == packing_order_id
        ).order_by(PackingBox.box_number.asc()).all()
        
        return self.response_schema(many=True).dump(boxes)
    
    def _get_next_box_number(self, packing_order_id: int) -> int:
        """Get next box number untuk packing order"""
        last_box = self.db_session.query(PackingBox).filter(
            PackingBox.packing_order_id == packing_order_id
        ).order_by(PackingBox.box_number.desc()).first()
        
        return (last_box.box_number + 1) if last_box else 1
    
    def _generate_box_barcode(self, packing_order_id: int, box_number: int) -> str:
        """Generate box barcode"""
        packing_order = self._get_or_404(PackingOrder, packing_order_id)
        order_number_suffix = packing_order.packing_order_number[-6:]
        return f"BOX{order_number_suffix}{box_number:03d}"
    
    def _update_box_totals(self, box_id: int):
        """Update box totals"""
        box = self._get_or_404(PackingBox, box_id)
        
        items = self.db_session.query(PackingBoxItem).filter(
            PackingBoxItem.packing_box_id == box_id
        ).all()
        
        total_items = len(items)
        total_quantity = sum(item.quantity_packed for item in items)
        
        box.total_items = total_items
        box.total_quantity = total_quantity
        self._set_audit_fields(box, is_update=True)