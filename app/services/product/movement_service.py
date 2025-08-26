"""
Stock Movement Service
======================

Service untuk tracking semua stock movements dan audit trail
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, func, desc, select

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
    
    def __init__(self, db_session: AsyncSession, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)
    
    @transactional
    @audit_log('CREATE', 'StockMovement')
    async def create_movement(self, allocation_id: int, movement_type_code: str,
                       quantity: int, reference_type: str = None, 
                       reference_id: int = None, reference_number: str = None,
                       source_rack_id: int = None, destination_rack_id: int = None,
                       notes: str = None) -> Dict[str, Any]:
        """Create stock movement record"""
        
        # Validate allocation exists
        allocation = await self._get_or_404(Allocation, allocation_id)
        
        # Get movement type
        result = await self.db_session.execute(
            select(MovementType).filter(MovementType.code == movement_type_code)
        )
        movement_type = result.scalars().first()
        
        if not movement_type:
            raise ValidationError(f"Movement type '{movement_type_code}' not found")
        
        # Generate movement number
        movement_number = await self._generate_movement_number(movement_type_code)
        
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
        
        return await super().create(movement_data)
    
    @transactional
    async def create_allocation_movement(self, allocation_id: int, quantity: int, 
                                 movement_type: str = 'ALLOCATE') -> Dict[str, Any]:
        """Create movement record untuk allocation"""
        return await self.create_movement(
            allocation_id=allocation_id,
            movement_type_code=movement_type,
            quantity=quantity,
            reference_type='Allocation',
            reference_id=allocation_id,
            notes=f"Stock allocated - {quantity} units"
        )
    
    @transactional
    async def create_picking_movement(self, allocation_id: int, quantity: int,
                              picking_order_id: int, source_rack_id: int) -> Dict[str, Any]:
        """Create movement record untuk picking"""
        return await self.create_movement(
            allocation_id=allocation_id,
            movement_type_code='PICK',
            quantity=-quantity,  # Negative untuk OUT movement
            reference_type='PickingOrder',
            reference_id=picking_order_id,
            source_rack_id=source_rack_id,
            notes=f"Stock picked for shipment - {quantity} units"
        )
    
    @transactional
    async def create_transfer_movement(self, allocation_id: int, quantity: int,
                               source_rack_id: int, destination_rack_id: int,
                               transfer_reason: str = None) -> Dict[str, Any]:
        """Create movement record untuk rack transfer"""
        return await self.create_movement(
            allocation_id=allocation_id,
            movement_type_code='TRANSFER',
            quantity=0,  # Transfer doesn't change total quantity
            reference_type='Transfer',
            source_rack_id=source_rack_id,
            destination_rack_id=destination_rack_id,
            notes=f"Stock transferred between racks - {quantity} units. Reason: {transfer_reason}"
        )
    
    async def get_movements_by_allocation(self, allocation_id: int) -> List[Dict[str, Any]]:
        """Get all movements untuk specific allocation"""
        query = select(StockMovement).filter(
            StockMovement.allocation_id == allocation_id
        ).order_by(StockMovement.movement_date.desc())
        
        result = await self.db_session.execute(query)
        movements = result.scalars().all()
        return self.response_schema(many=True).dump(movements)
    
    async def get_movements_by_product(self, product_id: int, 
                               start_date: date = None, end_date: date = None) -> List[Dict[str, Any]]:
        """Get all movements untuk product dalam date range"""
        from ...models import Batch
        
        query = select(StockMovement).join(Allocation).join(Batch).filter(
            Batch.product_id == product_id
        )
        
        if start_date:
            query = query.filter(StockMovement.movement_date >= start_date)
        if end_date:
            query = query.filter(StockMovement.movement_date <= end_date)
        
        query = query.order_by(StockMovement.movement_date.desc())
        
        result = await self.db_session.execute(query)
        movements = result.scalars().all()
        return self.response_schema(many=True).dump(movements)
    
    async def get_movement_summary(self, start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """Get movement summary untuk reporting"""
        query = select(StockMovement)
        
        if start_date:
            query = query.filter(StockMovement.movement_date >= start_date)
        if end_date:
            query = query.filter(StockMovement.movement_date <= end_date)
        
        result = await self.db_session.execute(query)
        movements = result.scalars().all()
        
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
    
    async def _generate_movement_number(self, movement_type_code: str) -> str:
        """Generate unique movement number"""
        today = date.today()
        prefix = f"MV{movement_type_code[:2]}{today.strftime('%y%m%d')}"
        
        # Get next sequence number
        result = await self.db_session.execute(
            select(StockMovement).filter(
                StockMovement.movement_number.like(f"{prefix}%")
            ).order_by(StockMovement.id.desc())
        )
        last_movement = result.scalars().first()
        
        if last_movement:
            last_seq = int(last_movement.movement_number[-4:])
            next_seq = last_seq + 1
        else:
            next_seq = 1
        
        return f"{prefix}{next_seq:04d}"