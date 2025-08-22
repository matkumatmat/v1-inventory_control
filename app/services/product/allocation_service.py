"""
Allocation Service
==================

CORE SERVICE untuk stock allocation logic - Paling critical dalam WMS
Menangani FIFO/FEFO, Tender vs Regular allocation, Stock reservation
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from enum import Enum

from ..base import CRUDService, transactional, audit_log
from ..exceptions import (
    ValidationError, BusinessRuleError, InsufficientStockError, 
    AllocationError, ContractError, NotFoundError
)
from ...models import (
    Allocation, Batch, Product, AllocationType, Customer,
    TenderContract, ContractReservation, Rack
)
from ...schemas import AllocationSchema, AllocationCreateSchema, AllocationUpdateSchema

class AllocationStrategy(Enum):
    """Allocation strategies"""
    FIFO = "FIFO"  # First In, First Out
    FEFO = "FEFO"  # First Expired, First Out
    LIFO = "LIFO"  # Last In, First Out
    SPECIFIC = "SPECIFIC"  # Specific batch

class AllocationService(CRUDService):
    """CORE SERVICE untuk stock allocation management"""
    
    model_class = Allocation
    create_schema = AllocationCreateSchema
    update_schema = AllocationUpdateSchema
    response_schema = AllocationSchema
    search_fields = ['allocation_number']
    
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None, 
                 movement_service=None, rack_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)
        self.movement_service = movement_service
        self.rack_service = rack_service
    
    @transactional
    @audit_log('CREATE', 'Allocation')
    def create_allocation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create allocation dengan business logic validation"""
        # Validate batch exists dan available
        batch = self._validate_batch_for_allocation(data['batch_id'])
        
        # Validate allocation type
        allocation_type = self._validate_allocation_type(data['allocation_type_id'])
        
        # Validate customer requirement
        self._validate_customer_requirement(allocation_type, data.get('customer_id'))
        
        # Check stock availability
        available_qty = self._get_available_stock(batch.id)
        requested_qty = data['allocated_quantity']
        
        if available_qty < requested_qty:
            raise InsufficientStockError(
                product_id=batch.product_id,
                required_qty=requested_qty,
                available_qty=available_qty,
                details={'batch_id': batch.id}
            )
        
        # Generate allocation number
        data['allocation_number'] = self._generate_allocation_number(allocation_type.code)
        
        # Set expiry date from batch
        if batch.expiry_date:
            data['expiry_date'] = batch.expiry_date
        
        # Create allocation
        allocation_data = super().create(data)
        allocation_id = allocation_data['id']
        
        # Handle different allocation types
        if allocation_type.code == 'TENDER':
            self._handle_tender_allocation(allocation_id, data)
        
        # Create stock movement record
        if self.movement_service:
            self.movement_service.create_allocation_movement(
                allocation_id=allocation_id,
                quantity=requested_qty,
                movement_type='ALLOCATE'
            )
        
        # Send notification
        self._send_notification('ALLOCATION_CREATED', ['warehouse_team'], {
            'allocation_id': allocation_id,
            'allocation_number': data['allocation_number'],
            'product_name': batch.product.name,
            'quantity': requested_qty
        })
        
        return allocation_data
    
    @transactional
    @audit_log('AUTO_ALLOCATE', 'Allocation')
    def auto_allocate_by_strategy(self, product_id: int, quantity: int, 
                                 allocation_type_id: int, customer_id: int = None,
                                 strategy: AllocationStrategy = AllocationStrategy.FEFO,
                                 specific_batch_id: int = None) -> List[Dict[str, Any]]:
        """Auto allocate stock dengan strategy tertentu"""
        
        # Validate input
        product = self._get_or_404(Product, product_id)
        allocation_type = self._validate_allocation_type(allocation_type_id)
        
        if customer_id:
            customer = self._get_or_404(Customer, customer_id)
        
        # Get available batches berdasarkan strategy
        available_batches = self._get_available_batches_by_strategy(
            product_id, strategy, specific_batch_id
        )
        
        if not available_batches:
            raise InsufficientStockError(product_id, quantity, 0)
        
        # Calculate total available
        total_available = sum(batch['available_quantity'] for batch in available_batches)
        if total_available < quantity:
            raise InsufficientStockError(product_id, quantity, total_available)
        
        # Create allocations
        allocations = []
        remaining_qty = quantity
        
        for batch_data in available_batches:
            if remaining_qty <= 0:
                break
            
            batch_available = batch_data['available_quantity']
            allocate_qty = min(remaining_qty, batch_available)
            
            allocation_data = {
                'batch_id': batch_data['id'],
                'allocation_type_id': allocation_type_id,
                'customer_id': customer_id,
                'allocated_quantity': allocate_qty,
                'allocation_date': date.today()
            }
            
            allocation = self.create_allocation(allocation_data)
            allocations.append(allocation)
            
            remaining_qty -= allocate_qty
        
        return allocations
    
    @transactional
    @audit_log('RESERVE', 'Allocation')
    def reserve_for_picking(self, allocation_id: int, quantity: int) -> Dict[str, Any]:
        """Reserve quantity untuk picking process"""
        allocation = self._get_or_404(Allocation, allocation_id)
        
        # Validate reservation
        max_reservable = allocation.allocated_quantity - allocation.shipped_quantity
        if allocation.reserved_quantity + quantity > max_reservable:
            raise AllocationError(
                f"Cannot reserve {quantity}. Max reservable: {max_reservable - allocation.reserved_quantity}",
                allocation_id=allocation_id
            )
        
        # Update reserved quantity
        allocation.reserved_quantity += quantity
        self._set_audit_fields(allocation, is_update=True)
        
        # Create movement record
        if self.movement_service:
            self.movement_service.create_movement(
                allocation_id=allocation_id,
                movement_type_code='RESERVE',
                quantity=quantity,
                reference_type='Picking'
            )
        
        return self.response_schema().dump(allocation)
    
    @transactional
    @audit_log('RELEASE', 'Allocation')
    def release_reservation(self, allocation_id: int, quantity: int) -> Dict[str, Any]:
        """Release reserved quantity"""
        allocation = self._get_or_404(Allocation, allocation_id)
        
        if allocation.reserved_quantity < quantity:
            raise AllocationError(
                f"Cannot release {quantity}. Only {allocation.reserved_quantity} reserved",
                allocation_id=allocation_id
            )
        
        # Update reserved quantity
        allocation.reserved_quantity -= quantity
        self._set_audit_fields(allocation, is_update=True)
        
        # Create movement record
        if self.movement_service:
            self.movement_service.create_movement(
                allocation_id=allocation_id,
                movement_type_code='RELEASE',
                quantity=-quantity,  # Negative untuk release
                reference_type='Picking'
            )
        
        return self.response_schema().dump(allocation)
    
    @transactional
    @audit_log('SHIP', 'Allocation')
    def ship_allocation(self, allocation_id: int, quantity: int, 
                       reference_type: str = None, reference_id: int = None) -> Dict[str, Any]:
        """Mark allocation as shipped"""
        allocation = self._get_or_404(Allocation, allocation_id)
        
        # Validate shipment
        max_shippable = allocation.allocated_quantity - allocation.shipped_quantity
        if quantity > max_shippable:
            raise AllocationError(
                f"Cannot ship {quantity}. Max shippable: {max_shippable}",
                allocation_id=allocation_id
            )
        
        # Update shipped quantity
        allocation.shipped_quantity += quantity
        
        # Release reservation if applicable
        if allocation.reserved_quantity >= quantity:
            allocation.reserved_quantity -= quantity
        else:
            # Ship more than reserved - this should be handled carefully
            allocation.reserved_quantity = 0
        
        # Update status if fully shipped
        if allocation.shipped_quantity >= allocation.allocated_quantity:
            allocation.status = 'shipped'
        
        self._set_audit_fields(allocation, is_update=True)
        
        # Create movement record
        if self.movement_service:
            self.movement_service.create_movement(
                allocation_id=allocation_id,
                movement_type_code='SHIP',
                quantity=quantity,
                reference_type=reference_type,
                reference_id=reference_id
            )
        
        # Update tender contract if applicable
        if allocation.tender_contract_id:
            self._update_contract_allocation(allocation, quantity)
        
        return self.response_schema().dump(allocation)
    
    def get_allocation_summary_by_product(self, product_id: int) -> Dict[str, Any]:
        """Get allocation summary untuk product"""
        query = self.db.query(Allocation).join(Batch).filter(
            and_(Batch.product_id == product_id, Allocation.status == 'active')
        )
        
        allocations = query.all()
        
        summary = {
            'product_id': product_id,
            'total_allocated': sum(a.allocated_quantity for a in allocations),
            'total_shipped': sum(a.shipped_quantity for a in allocations),
            'total_reserved': sum(a.reserved_quantity for a in allocations),
            'total_available': sum(a.allocated_quantity - a.shipped_quantity for a in allocations),
            'by_type': {},
            'by_customer': {},
            'expiring_soon': []
        }
        
        # Group by allocation type
        for allocation in allocations:
            type_code = allocation.allocation_type.code
            if type_code not in summary['by_type']:
                summary['by_type'][type_code] = {
                    'allocated': 0, 'shipped': 0, 'available': 0
                }
            
            summary['by_type'][type_code]['allocated'] += allocation.allocated_quantity
            summary['by_type'][type_code]['shipped'] += allocation.shipped_quantity
            summary['by_type'][type_code]['available'] += (allocation.allocated_quantity - allocation.shipped_quantity)
        
        # Group by customer
        for allocation in allocations:
            if allocation.customer_id:
                customer_key = f"{allocation.customer_id}_{allocation.customer.name}"
                if customer_key not in summary['by_customer']:
                    summary['by_customer'][customer_key] = {
                        'allocated': 0, 'shipped': 0, 'available': 0
                    }
                
                summary['by_customer'][customer_key]['allocated'] += allocation.allocated_quantity
                summary['by_customer'][customer_key]['shipped'] += allocation.shipped_quantity
                summary['by_customer'][customer_key]['available'] += (allocation.allocated_quantity - allocation.shipped_quantity)
        
        # Expiring allocations (30 days)
        cutoff_date = date.today() + timedelta(days=30)
        expiring_allocations = [a for a in allocations if a.expiry_date and a.expiry_date <= cutoff_date]
        summary['expiring_soon'] = self.response_schema(many=True).dump(expiring_allocations)
        
        return summary
    
    def get_customer_allocations(self, customer_id: int, 
                               include_shipped: bool = False) -> List[Dict[str, Any]]:
        """Get all allocations untuk customer"""
        query = self.db.query(Allocation).filter(Allocation.customer_id == customer_id)
        
        if not include_shipped:
            query = query.filter(Allocation.status != 'shipped')
        
        query = query.order_by(Allocation.allocation_date.desc())
        
        allocations = query.all()
        return self.response_schema(many=True).dump(allocations)
    
    def get_tender_allocations(self, contract_id: int) -> List[Dict[str, Any]]:
        """Get all allocations untuk tender contract"""
        query = self.db.query(Allocation).filter(
            Allocation.tender_contract_id == contract_id
        ).order_by(Allocation.allocation_date.desc())
        
        allocations = query.all()
        return self.response_schema(many=True).dump(allocations)
    
    def transfer_allocation(self, allocation_id: int, target_customer_id: int,
                          quantity: int = None) -> Dict[str, Any]:
        """Transfer allocation ke customer lain (untuk tender)"""
        allocation = self._get_or_404(Allocation, allocation_id)
        
        # Validate transfer rules
        if allocation.allocation_type.code != 'TENDER':
            raise AllocationError("Only tender allocations can be transferred")
        
        if allocation.shipped_quantity > 0:
            raise AllocationError("Cannot transfer allocation that has been shipped")
        
        target_customer = self._get_or_404(Customer, target_customer_id)
        
        transfer_qty = quantity or allocation.allocated_quantity
        
        if transfer_qty > allocation.allocated_quantity:
            raise AllocationError(f"Transfer quantity exceeds allocation quantity")
        
        # Create new allocation for target customer
        new_allocation_data = {
            'batch_id': allocation.batch_id,
            'allocation_type_id': allocation.allocation_type_id,
            'customer_id': target_customer_id,
            'tender_contract_id': allocation.tender_contract_id,
            'allocated_quantity': transfer_qty,
            'allocation_date': date.today(),
            'original_reserved_quantity': allocation.original_reserved_quantity
        }
        
        new_allocation = self.create_allocation(new_allocation_data)
        
        # Update original allocation
        if transfer_qty >= allocation.allocated_quantity:
            # Full transfer - mark as consumed
            allocation.status = 'consumed'
        else:
            # Partial transfer - reduce quantity
            allocation.allocated_quantity -= transfer_qty
        
        self._set_audit_fields(allocation, is_update=True)
        
        return {
            'original_allocation': self.response_schema().dump(allocation),
            'new_allocation': new_allocation
        }
    
    # ==================== PRIVATE METHODS ====================
    
    def _validate_batch_for_allocation(self, batch_id: int) -> Batch:
        """Validate batch dapat digunakan untuk allocation"""
        batch = self._get_or_404(Batch, batch_id)
        
        if batch.status != 'ACTIVE':
            raise ValidationError(f"Batch {batch.batch_number} is not active")
        
        if batch.qc_status != 'PASSED':
            raise ValidationError(f"Batch {batch.batch_number} has not passed QC")
        
        if batch.expiry_date and batch.expiry_date <= date.today():
            raise ValidationError(f"Batch {batch.batch_number} has expired")
        
        return batch
    
    def _validate_allocation_type(self, allocation_type_id: int) -> AllocationType:
        """Validate allocation type exists dan active"""
        allocation_type = self._get_or_404(AllocationType, allocation_type_id)
        
        if not allocation_type.is_active:
            raise ValidationError(f"Allocation type {allocation_type.name} is not active")
        
        return allocation_type
    
    def _validate_customer_requirement(self, allocation_type: AllocationType, customer_id: Optional[int]):
        """Validate customer requirement berdasarkan allocation type"""
        if allocation_type.requires_customer and not customer_id:
            raise ValidationError(f"Allocation type {allocation_type.name} requires customer")
        
        if customer_id:
            customer = self._get_or_404(Customer, customer_id)
            if not customer.is_active:
                raise ValidationError(f"Customer {customer.name} is not active")
    
    def _get_available_stock(self, batch_id: int) -> int:
        """Calculate available stock untuk batch"""
        batch = self._get_or_404(Batch, batch_id)
        
        # Calculate total allocated
        total_allocated = self.db.query(
            func.sum(Allocation.allocated_quantity - Allocation.shipped_quantity)
        ).filter(
            and_(Allocation.batch_id == batch_id, Allocation.status == 'active')
        ).scalar() or 0
        
        return batch.received_quantity - total_allocated
    
    def _get_available_batches_by_strategy(self, product_id: int, 
                                         strategy: AllocationStrategy,
                                         specific_batch_id: int = None) -> List[Dict[str, Any]]:
        """Get available batches berdasarkan allocation strategy"""
        
        if strategy == AllocationStrategy.SPECIFIC and specific_batch_id:
            batch = self._get_or_404(Batch, specific_batch_id)
            available_qty = self._get_available_stock(specific_batch_id)
            if available_qty > 0:
                batch_data = self.response_schema().dump(batch)
                batch_data['available_quantity'] = available_qty
                return [batch_data]
            return []
        
        # Get all available batches for product
        query = self.db.query(Batch).filter(
            and_(
                Batch.product_id == product_id,
                Batch.status == 'ACTIVE',
                Batch.qc_status == 'PASSED'
            )
        )
        
        # Apply sorting based on strategy
        if strategy == AllocationStrategy.FEFO:
            query = query.order_by(Batch.expiry_date.asc(), Batch.received_date.asc())
        elif strategy == AllocationStrategy.FIFO:
            query = query.order_by(Batch.received_date.asc())
        elif strategy == AllocationStrategy.LIFO:
            query = query.order_by(Batch.received_date.desc())
        
        batches = query.all()
        
        # Calculate available quantity for each batch
        result = []
        for batch in batches:
            available_qty = self._get_available_stock(batch.id)
            if available_qty > 0:
                batch_data = self.response_schema().dump(batch)
                batch_data['available_quantity'] = available_qty
                result.append(batch_data)
        
        return result
    
    def _generate_allocation_number(self, allocation_type_code: str) -> str:
        """Generate unique allocation number"""
        today = date.today()
        prefix = f"AL{allocation_type_code[:2]}{today.strftime('%y%m%d')}"
        
        # Get next sequence number
        last_allocation = self.db.query(Allocation).filter(
            Allocation.allocation_number.like(f"{prefix}%")
        ).order_by(Allocation.id.desc()).first()
        
        if last_allocation:
            last_seq = int(last_allocation.allocation_number[-4:])
            next_seq = last_seq + 1
        else:
            next_seq = 1
        
        return f"{prefix}{next_seq:04d}"
    
    def _handle_tender_allocation(self, allocation_id: int, data: Dict[str, Any]):
        """Handle special logic untuk tender allocations"""
        tender_contract_id = data.get('tender_contract_id')
        if not tender_contract_id:
            return
        
        # Validate contract exists dan active
        contract = self._get_or_404(TenderContract, tender_contract_id)
        if contract.status != 'ACTIVE':
            raise ContractError(f"Contract {contract.contract_number} is not active")
        
        # Update contract reservation
        reservation = self.db.query(ContractReservation).filter(
            and_(
                ContractReservation.contract_id == tender_contract_id,
                ContractReservation.allocation_id == allocation_id
            )
        ).first()
        
        if reservation:
            allocated_qty = data['allocated_quantity']
            reservation.allocated_quantity += allocated_qty
            reservation.remaining_quantity = reservation.reserved_quantity - reservation.allocated_quantity
            
            if reservation.remaining_quantity < 0:
                raise ContractError("Allocation exceeds contract reservation")
    
    def _update_contract_allocation(self, allocation: Allocation, shipped_qty: int):
        """Update contract allocation ketika shipment"""
        if not allocation.tender_contract_id:
            return
        
        reservation = self.db.query(ContractReservation).filter(
            and_(
                ContractReservation.contract_id == allocation.tender_contract_id,
                ContractReservation.allocation_id == allocation.id
            )
        ).first()
        
        if reservation:
            # This would update the contract reservation status
            # Implementation depends on specific business rules
            pass