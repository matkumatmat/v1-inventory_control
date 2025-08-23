"""
Batch Service
=============

Service untuk mengelola Batch dan QC operations
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date,timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, select, func

from ..base import CRUDService, transactional, audit_log
from ..exceptions import ValidationError, BusinessRuleError, NotFoundError
from ...models import Batch, Product, Allocation
from ...schemas import BatchSchema, BatchCreateSchema, BatchUpdateSchema

class BatchService(CRUDService):
    """Service untuk Batch management"""
    
    model_class = Batch
    create_schema = BatchCreateSchema
    update_schema = BatchUpdateSchema
    response_schema = BatchSchema
    search_fields = ['batch_number', 'lot_number', 'supplier_name']
    
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None, allocation_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)
        self.allocation_service = allocation_service
    
    @transactional
    @audit_log('CREATE', 'Batch')
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new batch with validation"""
        # Validate product exists
        product_id = data.get('product_id')
        product = await self._get_or_404(Product, product_id)
        
        # Validate batch number uniqueness per product
        batch_number = data.get('batch_number')
        result = await self.db_session.execute(select(Batch).filter(
            and_(Batch.product_id == product_id, Batch.batch_number == batch_number)
        ))
        existing_batch = result.scalars().first()
        
        if existing_batch:
            raise ValidationError(f"Batch number '{batch_number}' already exists for this product")
        
        # Validate dates
        self._validate_batch_dates(data)
        
        # Create batch
        batch_data = await super().create(data)
        
        # Send notification for new batch
        await self._send_notification('BATCH_CREATED', ['warehouse_team'], {
            'batch_id': batch_data['id'],
            'product_name': product.name,
            'batch_number': batch_number,
            'received_quantity': data.get('received_quantity')
        })
        
        return batch_data
    
    @transactional
    @audit_log('UPDATE', 'Batch')
    async def update(self, entity_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update batch with validation"""
        batch = await self._get_or_404(Batch, entity_id)
        
        # Check if batch has allocations - restrict some updates
        if await self._batch_has_allocations(entity_id):
            restricted_fields = ['product_id', 'batch_number', 'received_quantity']
            for field in restricted_fields:
                if field in data:
                    raise BusinessRuleError(f"Cannot update {field} - batch has active allocations")
        
        # Validate dates if provided
        if any(key in data for key in ['manufacturing_date', 'expiry_date', 'received_date']):
            self._validate_batch_dates(data, existing_batch=batch)
        
        return await super().update(entity_id, data)
    
    @transactional
    @audit_log('QC_UPDATE', 'Batch')
    async def update_qc_status(self, batch_id: int, qc_status: str, qc_notes: str = None) -> Dict[str, Any]:
        """Update QC status untuk batch"""
        valid_statuses = ['PENDING', 'PASSED', 'FAILED', 'QUARANTINE']
        if qc_status not in valid_statuses:
            raise ValidationError(f"Invalid QC status. Must be one of: {valid_statuses}")
        
        batch = await self._get_or_404(Batch, batch_id)
        
        # Update QC fields
        batch.qc_status = qc_status
        batch.qc_date = datetime.utcnow()
        batch.qc_by = self.current_user
        batch.qc_notes = qc_notes
        
        self._set_audit_fields(batch, is_update=True)
        
        # Handle QC status changes
        if qc_status == 'FAILED':
            # Mark batch as unusable
            batch.status = 'RECALLED'
            
            # Notify relevant teams
            await self._send_notification('BATCH_QC_FAILED', ['quality_team', 'warehouse_team'], {
                'batch_id': batch_id,
                'batch_number': batch.batch_number,
                'qc_notes': qc_notes
            })
        
        elif qc_status == 'PASSED':
            # Batch ready for allocation
            await self._send_notification('BATCH_QC_PASSED', ['warehouse_team'], {
                'batch_id': batch_id,
                'batch_number': batch.batch_number,
                'received_quantity': batch.received_quantity
            })
        
        return self.response_schema().dump(batch)
    
    async def get_expiring_batches(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Get batches yang akan expire dalam days_ahead"""
        cutoff_date = date.today() + timedelta(days=days_ahead)
        
        query = select(Batch).filter(
            and_(
                Batch.expiry_date <= cutoff_date,
                Batch.expiry_date >= date.today(),
                Batch.status == 'ACTIVE',
                Batch.qc_status == 'PASSED'
            )
        ).order_by(Batch.expiry_date.asc())
        
        result = await self.db_session.execute(query)
        batches = result.scalars().all()
        return self.response_schema(many=True).dump(batches)
    
    async def get_batches_by_product(self, product_id: int, include_consumed: bool = False) -> List[Dict[str, Any]]:
        """Get all batches untuk specific product"""
        query = select(Batch).filter(Batch.product_id == product_id)
        
        if not include_consumed:
            query = query.filter(Batch.status != 'CONSUMED')
        
        query = query.order_by(Batch.received_date.desc())
        
        result = await self.db_session.execute(query)
        batches = result.scalars().all()
        return self.response_schema(many=True).dump(batches)
    
    async def get_available_batches_for_allocation(self, product_id: int, 
                                           min_quantity: int = None) -> List[Dict[str, Any]]:
        """Get batches yang available untuk allocation"""
        from ...models import Allocation
        
        # Subquery untuk menghitung allocated quantity per batch
        allocated_subquery = select(
            Allocation.batch_id,
            func.sum(Allocation.allocated_quantity - Allocation.shipped_quantity).label('allocated_qty')
        ).filter(Allocation.status == 'active').group_by(Allocation.batch_id).subquery()
        
        # Main query
        query = select(Batch).outerjoin(
            allocated_subquery, Batch.id == allocated_subquery.c.batch_id
        ).filter(
            and_(
                Batch.product_id == product_id,
                Batch.status == 'ACTIVE',
                Batch.qc_status == 'PASSED'
            )
        )
        
        # Add available quantity filter
        if min_quantity:
            query = query.filter(
                (Batch.received_quantity - 
                 func.coalesce(allocated_subquery.c.allocated_qty, 0)) >= min_quantity
            )
        
        # Order by FEFO (First Expired, First Out)
        query = query.order_by(Batch.expiry_date.asc(), Batch.received_date.asc())
        
        result = await self.db_session.execute(query)
        batches = result.scalars().all()
        
        # Calculate available quantity for each batch
        result_data = []
        for batch in batches:
            batch_data = self.response_schema().dump(batch)
            
            # Calculate available quantity
            total_allocated_result = await self.db_session.execute(
                select(func.sum(Allocation.allocated_quantity - Allocation.shipped_quantity)).filter(
                    and_(Allocation.batch_id == batch.id, Allocation.status == 'active')
                )
            )
            total_allocated = total_allocated_result.scalar() or 0
            
            batch_data['available_quantity'] = batch.received_quantity - total_allocated
            result_data.append(batch_data)
        
        return result_data
    
    def _validate_batch_dates(self, data: Dict[str, Any], existing_batch: Batch = None):
        """Validate batch date relationships"""
        manufacturing_date = data.get('manufacturing_date') or (existing_batch.manufacturing_date if existing_batch else None)
        expiry_date = data.get('expiry_date') or (existing_batch.expiry_date if existing_batch else None)
        received_date = data.get('received_date') or (existing_batch.received_date if existing_batch else None)
        
        # Manufacturing date validation
        if manufacturing_date and manufacturing_date > date.today():
            raise ValidationError("Manufacturing date cannot be in the future")
        
        # Expiry date validation
        if expiry_date and expiry_date <= date.today():
            raise ValidationError("Expiry date must be in the future")
        
        # Date relationship validation
        if manufacturing_date and expiry_date and manufacturing_date >= expiry_date:
            raise ValidationError("Manufacturing date must be before expiry date")
        
        if manufacturing_date and received_date and manufacturing_date > received_date:
            raise ValidationError("Manufacturing date cannot be after received date")
    
    async def _batch_has_allocations(self, batch_id: int) -> bool:
        """Check if batch has any allocations"""
        result = await self.db_session.execute(
            select(func.count(Allocation.id)).filter(
                and_(Allocation.batch_id == batch_id, Allocation.status == 'active')
            )
        )
        return result.scalar() > 0