"""
Stock Movement Service
======================

Service untuk tracking semua stock movements dan audit trail
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from ..base import CRUDService, transactional, audit_log
from ..exceptions import ValidationError, NotFoundError
from ...models import StockMovement, MovementType, Allocation, Rack
from ...schemas import StockMovementSchema, StockMovementCreateSchema, StockMovementUpdateSchema

class StockMovementService(CRUDService):
    """Service untuk Stock Movement tracking"""
    
    model_class = StockMovement
    create_schema = StockMovementCreateSchema
    update_schema = StockMovementUpdateSchema
    response_schema = StockMovementSchema
    search_fields = ['movement_number', 'reference_number']
    
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)
    
    @transactional
    @audit_log('CREATE', 'StockMovement')
    def create_movement(self, allocation_id: int, movement_type_code: str,
                       quantity: int, reference_type: str = None, 
                       reference_id: int = None, reference_number: str = None,
                       source_rack_id: int = None, destination_rack_id: int = None,
                       notes: str = None) -> Dict[str, Any]:
        """Create stock movement record"""
        
        # Validate allocation exists
        allocation = self._get_or_404(Allocation, allocation_id)
        
        # Get movement type
        movement_type = self.db.query(MovementType).filter(
            MovementType.code == movement_type_code
        ).first()
        
        if not movement_type:
            raise ValidationError(f"Movement type '{movement_type_code}' not found")
        
        # Generate movement number
        movement_number = self._generate_movement_number(movement_type_code)
        
        # Create movement data
        movement_data = {
            'movement_number': movement_number,
            'allocation_id': allocation_id,
            'movement_type_id': movement_type.id,
            'quantity': quantity,
            'movement_date': datetime.utcnow(),
            'reference_type': reference_type,
            'reference_id': reference_id,
            'reference_number': reference_number,
            'source_rack_id': source_rack_id,
            'destination_rack_id': destination_rack_id,
            'notes': notes,
            'executed_by': self.current_user,
            'status': 'COMPLETED'
        }
        
        return super().create(movement_data)
    
    @transactional
    def create_allocation_movement(self, allocation_id: int, quantity: int, 
                                 movement_type: str = 'ALLOCATE') -> Dict[str, Any]:
        """Create movement record untuk allocation"""
        return self.create_movement(
            allocation_id=allocation_id,
            movement_type_code=movement_type,
            quantity=quantity,
            reference_type='Allocation',
            reference_id=allocation_id,
            notes=f"Stock allocated - {quantity} units"
        )
    
    @transactional
    def create_picking_movement(self, allocation_id: int, quantity: int,
                              picking_order_id: int, source_rack_id: int) -> Dict[str, Any]:
        """Create movement record untuk picking"""
        return self.create_movement(
            allocation_id=allocation_id,
            movement_type_code='PICK',
            quantity=-quantity,  # Negative untuk OUT movement
            reference_type='PickingOrder',
            reference_id=picking_order_id,
            source_rack_id=source_rack_id,
            notes=f"Stock picked for shipment - {quantity} units"
        )
    
    @transactional
    def create_transfer_movement(self, allocation_id: int, quantity: int,
                               source_rack_id: int, destination_rack_id: int,
                               transfer_reason: str = None) -> Dict[str, Any]:
        """Create movement record untuk rack transfer"""
        return self.create_movement(
            allocation_id=allocation_id,
            movement_type_code='TRANSFER',
            quantity=0,  # Transfer doesn't change total quantity
            reference_type='Transfer',
            source_rack_id=source_rack_id,
            destination_rack_id=destination_rack_id,
            notes=f"Stock transferred between racks - {quantity} units. Reason: {transfer_reason}"
        )
    
    def get_movements_by_allocation(self, allocation_id: int) -> List[Dict[str, Any]]:
        """Get all movements untuk specific allocation"""
        query = self.db.query(StockMovement).filter(
            StockMovement.allocation_id == allocation_id
        ).order_by(StockMovement.movement_date.desc())
        
        movements = query.all()
        return self.response_schema(many=True).dump(movements)
    
    def get_movements_by_product(self, product_id: int, 
                               start_date: date = None, end_date: date = None) -> List[Dict[str, Any]]:
        """Get all movements untuk product dalam date range"""
        from ...models import Batch
        
        query = self.db.query(StockMovement).join(Allocation).join(Batch).filter(
            Batch.product_id == product_id
        )
        
        if start_date:
            query = query.filter(StockMovement.movement_date >= start_date)
        if end_date:
            query = query.filter(StockMovement.movement_date <= end_date)
        
        query = query.order_by(StockMovement.movement_date.desc())
        
        movements = query.all()
        return self.response_schema(many=True).dump(movements)
    
    def get_movement_summary(self, start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """Get movement summary untuk reporting"""
        query = self.db.query(StockMovement)
        
        if start_date:
            query = query.filter(StockMovement.movement_date >= start_date)
        if end_date:
            query = query.filter(StockMovement.movement_date <= end_date)
        
        movements = query.all()
        
        summary = {
            'total_movements': len(movements),
            'by_type': {},
            'by_date': {},
            'total_quantity_in': 0,
            'total_quantity_out': 0
        }
        
        for movement in movements:
            # By type
            type_code = movement.movement_type.code
            if type_code not in summary['by_type']:
                summary['by_type'][type_code] = {'count': 0, 'total_quantity': 0}
            
            summary['by_type'][type_code]['count'] += 1
            summary['by_type'][type_code]['total_quantity'] += abs(movement.quantity)
            
            # By date
            date_key = movement.movement_date.date().isoformat()
            if date_key not in summary['by_date']:
                summary['by_date'][date_key] = {'count': 0, 'total_quantity': 0}
            
            summary['by_date'][date_key]['count'] += 1
            summary['by_date'][date_key]['total_quantity'] += abs(movement.quantity)
            
            # Total in/out
            if movement.quantity > 0:
                summary['total_quantity_in'] += movement.quantity
            else:
                summary['total_quantity_out'] += abs(movement.quantity)
        
        return summary
    
    def _generate_movement_number(self, movement_type_code: str) -> str:
        """Generate unique movement number"""
        today = date.today()
        prefix = f"MV{movement_type_code[:2]}{today.strftime('%y%m%d')}"
        
        # Get next sequence number
        last_movement = self.db.query(StockMovement).filter(
            StockMovement.movement_number.like(f"{prefix}%")
        ).order_by(StockMovement.id.desc()).first()
        
        if last_movement:
            last_seq = int(last_movement.movement_number[-4:])
            next_seq = last_seq + 1
        else:
            next_seq = 1
        
        return f"{prefix}{next_seq:04d}"