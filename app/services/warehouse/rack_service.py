"""
Rack Service
============

Service untuk Rack management dan stock placement
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import datetime

from ..base import CRUDService, transactional, audit_log
from ..exceptions import ValidationError, BusinessRuleError, NotFoundError
from ...models import Rack, Warehouse, RackAllocation, Allocation
from ...schemas import RackSchema, RackCreateSchema, RackUpdateSchema, RackAllocationSchema

class RackService(CRUDService):
    """Service untuk Rack management"""
    
    model_class = Rack
    create_schema = RackCreateSchema
    update_schema = RackUpdateSchema
    response_schema = RackSchema
    search_fields = ['rack_code', 'zone', 'aisle', 'section']
    
    @transactional
    @audit_log('CREATE', 'Rack')
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create rack dengan validation"""
        # Validate warehouse exists
        warehouse_id = data.get('warehouse_id')
        warehouse = self._get_or_404(Warehouse, warehouse_id)
        
        # Validate rack code uniqueness within warehouse
        rack_code = data.get('rack_code')
        existing_rack = self.db.query(Rack).filter(
            and_(Rack.warehouse_id == warehouse_id, Rack.rack_code == rack_code)
        ).first()
        
        if existing_rack:
            raise ValidationError(f"Rack code '{rack_code}' already exists in this warehouse")
        
        return super().create(data)
    
    @transactional
    @audit_log('UPDATE', 'Rack')
    def update(self, entity_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update rack dengan validation"""
        rack = self._get_or_404(Rack, entity_id)
        
        # Validate rack code uniqueness if changed
        rack_code = data.get('rack_code')
        if rack_code and rack_code != rack.rack_code:
            existing_rack = self.db.query(Rack).filter(
                and_(
                    Rack.warehouse_id == rack.warehouse_id,
                    Rack.rack_code == rack_code,
                    Rack.id != entity_id
                )
            ).first()
            
            if existing_rack:
                raise ValidationError(f"Rack code '{rack_code}' already exists in this warehouse")
        
        # Validate capacity reduction
        new_max_capacity = data.get('max_capacity')
        if new_max_capacity and new_max_capacity < rack.current_quantity:
            raise BusinessRuleError(
                f"Cannot reduce capacity below current usage. Current: {rack.current_quantity}, New: {new_max_capacity}"
            )
        
        return super().update(entity_id, data)
    
    @transactional
    def allocate_to_rack(self, rack_id: int, allocation_id: int, 
                        quantity: int, position_details: str = None) -> Dict[str, Any]:
        """Allocate stock ke specific rack"""
        rack = self._get_or_404(Rack, rack_id)
        allocation = self._get_or_404(Allocation, allocation_id)
        
        # Validate capacity
        if rack.max_capacity and (rack.current_quantity + quantity) > rack.max_capacity:
            available_capacity = rack.max_capacity - rack.current_quantity
            raise BusinessRuleError(
                f"Insufficient rack capacity. Available: {available_capacity}, Requested: {quantity}"
            )
        
        # Check if allocation already placed in another rack
        existing_placement = self.db.query(RackAllocation).filter(
            RackAllocation.allocation_id == allocation_id
        ).first()
        
        if existing_placement:
            raise BusinessRuleError("Allocation already placed in another rack")
        
        # Create rack allocation
        rack_allocation = RackAllocation(
            allocation_id=allocation_id,
            rack_id=rack_id,
            quantity=quantity,
            position_details=position_details,
            placement_date=datetime.utcnow(),
            placed_by=self.current_user
        )
        
        self.db.add(rack_allocation)
        
        # Update rack current quantity
        rack.current_quantity += quantity
        self._set_audit_fields(rack, is_update=True)
        
        self.db.flush()
        
        return RackAllocationSchema().dump(rack_allocation)
    
    @transactional
    def remove_from_rack(self, rack_id: int, allocation_id: int, 
                        quantity: int = None) -> bool:
        """Remove stock dari rack"""
        rack = self._get_or_404(Rack, rack_id)
        
        rack_allocation = self.db.query(RackAllocation).filter(
            and_(
                RackAllocation.rack_id == rack_id,
                RackAllocation.allocation_id == allocation_id
            )
        ).first()
        
        if not rack_allocation:
            raise NotFoundError('RackAllocation', f'rack_id: {rack_id}, allocation_id: {allocation_id}')
        
        remove_qty = quantity or rack_allocation.quantity
        
        if remove_qty > rack_allocation.quantity:
            raise BusinessRuleError(f"Cannot remove {remove_qty}. Only {rack_allocation.quantity} available")
        
        # Update quantities
        rack_allocation.quantity -= remove_qty
        rack.current_quantity -= remove_qty
        
        # Remove allocation if quantity becomes 0
        if rack_allocation.quantity <= 0:
            self.db.delete(rack_allocation)
        
        self._set_audit_fields(rack, is_update=True)
        
        return True
    
    @transactional
    def transfer_between_racks(self, source_rack_id: int, destination_rack_id: int,
                             allocation_id: int, quantity: int, 
                             transfer_reason: str = None) -> Dict[str, Any]:
        """Transfer stock between racks"""
        source_rack = self._get_or_404(Rack, source_rack_id)
        dest_rack = self._get_or_404(Rack, destination_rack_id)
        
        # Validate destination capacity
        if dest_rack.max_capacity and (dest_rack.current_quantity + quantity) > dest_rack.max_capacity:
            available_capacity = dest_rack.max_capacity - dest_rack.current_quantity
            raise BusinessRuleError(
                f"Insufficient destination rack capacity. Available: {available_capacity}, Requested: {quantity}"
            )
        
        # Remove from source
        self.remove_from_rack(source_rack_id, allocation_id, quantity)
        
        # Add to destination
        self.allocate_to_rack(destination_rack_id, allocation_id, quantity, 
                            position_details=f"Transferred from {source_rack.rack_code}. Reason: {transfer_reason}")
        
        return {
            'source_rack': self.response_schema().dump(source_rack),
            'destination_rack': self.response_schema().dump(dest_rack),
            'transfer_quantity': quantity,
            'transfer_reason': transfer_reason
        }
    
    def get_racks_by_warehouse(self, warehouse_id: int, 
                              include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Get all racks dalam warehouse"""
        query = self.db.query(Rack).filter(Rack.warehouse_id == warehouse_id)
        
        if not include_inactive:
            query = query.filter(Rack.is_active == True)
        
        query = query.order_by(Rack.zone.asc(), Rack.aisle.asc(), Rack.section.asc())
        
        racks = query.all()
        
        # Add calculated fields
        result = []
        for rack in racks:
            rack_data = self.response_schema().dump(rack)
            rack_data['available_capacity'] = (rack.max_capacity or 0) - (rack.current_quantity or 0)
            rack_data['utilization_percentage'] = (
                (rack.current_quantity / rack.max_capacity * 100) 
                if rack.max_capacity and rack.max_capacity > 0 else 0
            )
            result.append(rack_data)
        
        return result
    
    def get_available_racks_for_allocation(self, warehouse_id: int, 
                                         min_capacity: int = None) -> List[Dict[str, Any]]:
        """Get racks yang available untuk allocation baru"""
        query = self.db.query(Rack).filter(
            and_(
                Rack.warehouse_id == warehouse_id,
                Rack.is_active == True,
                Rack.access_level != 'RESTRICTED'
            )
        )
        
        racks = query.all()
        
        # Filter by available capacity
        available_racks = []
        for rack in racks:
            available_capacity = (rack.max_capacity or 0) - (rack.current_quantity or 0)
            
            if min_capacity is None or available_capacity >= min_capacity:
                rack_data = self.response_schema().dump(rack)
                rack_data['available_capacity'] = available_capacity
                available_racks.append(rack_data)
        
        # Sort by available capacity (most space first)
        available_racks.sort(key=lambda x: x['available_capacity'], reverse=True)
        
        return available_racks
    
    def get_rack_allocations(self, rack_id: int) -> List[Dict[str, Any]]:
        """Get all allocations dalam rack"""
        rack_allocations = self.db.query(RackAllocation).filter(
            RackAllocation.rack_id == rack_id
        ).all()
        
        return RackAllocationSchema(many=True).dump(rack_allocations)
    
    def get_rack_utilization_report(self, warehouse_id: int = None) -> Dict[str, Any]:
        """Get rack utilization report"""
        query = self.db.query(Rack).filter(Rack.is_active == True)
        
        if warehouse_id:
            query = query.filter(Rack.warehouse_id == warehouse_id)
        
        racks = query.all()
        
        total_racks = len(racks)
        total_capacity = sum(rack.max_capacity or 0 for rack in racks)
        total_usage = sum(rack.current_quantity or 0 for rack in racks)
        
        # Categorize by utilization
        empty_racks = len([r for r in racks if (r.current_quantity or 0) == 0])
        low_util_racks = len([r for r in racks if 0 < (r.current_quantity or 0) / (r.max_capacity or 1) <= 0.5])
        medium_util_racks = len([r for r in racks if 0.5 < (r.current_quantity or 0) / (r.max_capacity or 1) <= 0.8])
        high_util_racks = len([r for r in racks if 0.8 < (r.current_quantity or 0) / (r.max_capacity or 1) < 1.0])
        full_racks = len([r for r in racks if (r.current_quantity or 0) >= (r.max_capacity or 1)])
        
        return {
            'summary': {
                'total_racks': total_racks,
                'total_capacity': total_capacity,
                'total_usage': total_usage,
                'available_capacity': total_capacity - total_usage,
                'overall_utilization_percentage': (total_usage / total_capacity * 100) if total_capacity > 0 else 0
            },
            'utilization_breakdown': {
                'empty_racks': empty_racks,
                'low_utilization': low_util_racks,
                'medium_utilization': medium_util_racks,
                'high_utilization': high_util_racks,
                'full_racks': full_racks
            }
        }