"""
Contract Reservation Service
============================

Service untuk Contract Reservation management
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ..base import CRUDService, transactional, audit_log
from ..exceptions import ValidationError, BusinessRuleError, ContractError, NotFoundError
from ...models import ContractReservation, TenderContract, Product, Batch, Allocation
from ...schemas import ContractReservationSchema, ContractReservationCreateSchema, ContractReservationUpdateSchema

class ContractReservationService(CRUDService):
    """Service untuk Contract Reservation management"""
    
    model_class = ContractReservation
    create_schema = ContractReservationCreateSchema
    update_schema = ContractReservationUpdateSchema
    response_schema = ContractReservationSchema
    
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None, allocation_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)
        self.allocation_service = allocation_service
    
    @transactional
    @audit_log('CREATE', 'ContractReservation')
    def create_reservation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create contract reservation dengan business logic"""
        # Validate contract exists dan active
        contract = self._validate_contract(data['contract_id'])
        
        # Validate product exists
        product = self._get_or_404(Product, data['product_id'])
        
        # Validate batch exists dan available
        batch = self._validate_batch_for_reservation(data['batch_id'])
        
        # Validate allocation exists
        allocation = self._get_or_404(Allocation, data['allocation_id'])
        
        # Validate allocation belongs to same batch/product
        if allocation.batch_id != data['batch_id']:
            raise ValidationError("Allocation does not belong to specified batch")
        
        # Validate reservation quantity
        reserved_qty = data['reserved_quantity']
        max_reservable = allocation.allocated_quantity - allocation.shipped_quantity
        
        if reserved_qty > max_reservable:
            raise ContractError(
                f"Cannot reserve {reserved_qty}. Max reservable: {max_reservable}",
                contract_id=data['contract_id']
            )
        
        # Check for existing reservation for same allocation
        existing_reservation = self.db.query(ContractReservation).filter(
            and_(
                ContractReservation.contract_id == data['contract_id'],
                ContractReservation.allocation_id == data['allocation_id']
            )
        ).first()
        
        if existing_reservation:
            raise BusinessRuleError("Allocation already reserved for this contract")
        
        # Set initial remaining quantity
        data['remaining_quantity'] = reserved_qty
        data['allocated_quantity'] = 0
        
        # Create reservation
        reservation_data = super().create(data)
        
        # Update allocation to mark as reserved for tender
        allocation.original_reserved_quantity = (allocation.original_reserved_quantity or 0) + reserved_qty
        allocation.tender_contract_id = data['contract_id']
        self._set_audit_fields(allocation, is_update=True)
        
        # Send notification
        self._send_notification('CONTRACT_RESERVATION_CREATED', ['admin', 'sales_team'], {
            'reservation_id': reservation_data['id'],
            'contract_number': contract.contract_number,
            'product_name': product.name,
            'reserved_quantity': reserved_qty
        })
        
        return reservation_data
    
    @transactional
    @audit_log('UPDATE', 'ContractReservation')
    def update_reservation(self, reservation_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update reservation dengan validation"""
        reservation = self._get_or_404(ContractReservation, reservation_id)
        
        # Validate quantity changes
        if 'reserved_quantity' in data:
            new_reserved_qty = data['reserved_quantity']
            
            # Cannot reduce below already allocated
            if new_reserved_qty < reservation.allocated_quantity:
                raise BusinessRuleError(
                    f"Cannot reduce reservation below allocated quantity ({reservation.allocated_quantity})"
                )
            
            # Update remaining quantity
            data['remaining_quantity'] = new_reserved_qty - reservation.allocated_quantity
        
        return super().update(reservation_id, data)
    
    @transactional
    @audit_log('ALLOCATE', 'ContractReservation')
    def allocate_from_reservation(self, reservation_id: int, quantity: int,
                                customer_id: int) -> Dict[str, Any]:
        """Allocate quantity dari contract reservation ke customer"""
        reservation = self._get_or_404(ContractReservation, reservation_id)
        
        # Validate allocation quantity
        if quantity > reservation.remaining_quantity:
            raise ContractError(
                f"Cannot allocate {quantity}. Only {reservation.remaining_quantity} remaining",
                contract_id=reservation.contract_id
            )
        
        # Validate contract is still active
        contract = self._get_or_404(TenderContract, reservation.contract_id)
        if contract.status != 'ACTIVE':
            raise ContractError(f"Contract {contract.contract_number} is not active")
        
        # Create new allocation for customer using allocation service
        if self.allocation_service:
            allocation_data = {
                'batch_id': reservation.batch_id,
                'allocation_type_id': 2,  # Assuming TENDER allocation type ID is 2
                'customer_id': customer_id,
                'tender_contract_id': reservation.contract_id,
                'allocated_quantity': quantity,
                'allocation_date': date.today(),
                'original_reserved_quantity': quantity
            }
            
            new_allocation = self.allocation_service.create_allocation(allocation_data)
            
            # Update reservation quantities
            reservation.allocated_quantity += quantity
            reservation.remaining_quantity -= quantity
            self._set_audit_fields(reservation, is_update=True)
            
            # Send notification
            self._send_notification('CONTRACT_ALLOCATION_CREATED', ['admin', 'sales_team'], {
                'allocation_id': new_allocation['id'],
                'contract_number': contract.contract_number,
                'customer_id': customer_id,
                'quantity': quantity
            })
            
            return {
                'reservation': self.response_schema().dump(reservation),
                'new_allocation': new_allocation
            }
        else:
            raise BusinessRuleError("Allocation service not available")
    
    @transactional
    @audit_log('RELEASE', 'ContractReservation')
    def release_reservation(self, reservation_id: int, quantity: int = None) -> Dict[str, Any]:
        """Release reservation (partial atau full)"""
        reservation = self._get_or_404(ContractReservation, reservation_id)
        
        release_qty = quantity or reservation.remaining_quantity
        
        if release_qty > reservation.remaining_quantity:
            raise BusinessRuleError(f"Cannot release {release_qty}. Only {reservation.remaining_quantity} available")
        
        # Update reservation
        original_allocation = self._get_or_404(Allocation, reservation.allocation_id)
        
        # Release from original allocation
        if self.allocation_service:
            self.allocation_service.release_reservation(reservation.allocation_id, release_qty)
        
        # Update reservation quantities
        reservation.reserved_quantity -= release_qty
        reservation.remaining_quantity -= release_qty
        self._set_audit_fields(reservation, is_update=True)
        
        # If fully released, mark as inactive
        if reservation.remaining_quantity <= 0 and reservation.allocated_quantity <= 0:
            # This would be a soft delete or status change
            pass
        
        return self.response_schema().dump(reservation)
    
    def get_contract_reservations(self, contract_id: int) -> List[Dict[str, Any]]:
        """Get all reservations untuk contract"""
        reservations = self.db.query(ContractReservation).filter(
            ContractReservation.contract_id == contract_id
        ).all()
        
        return self.response_schema(many=True).dump(reservations)
    
    def get_product_reservations(self, product_id: int, 
                               include_allocated: bool = True) -> List[Dict[str, Any]]:
        """Get all reservations untuk product"""
        query = self.db.query(ContractReservation).filter(
            ContractReservation.product_id == product_id
        )
        
        if not include_allocated:
            query = query.filter(ContractReservation.remaining_quantity > 0)
        
        reservations = query.all()
        return self.response_schema(many=True).dump(reservations)
    
    def get_available_reservations_for_customer(self, customer_id: int) -> List[Dict[str, Any]]:
        """Get available reservations yang bisa dialokasikan ke customer"""
        # This would depend on business rules about which customers
        # can access which tender contracts
        
        query = self.db.query(ContractReservation).join(TenderContract).filter(
            and_(
                TenderContract.status == 'ACTIVE',
                ContractReservation.remaining_quantity > 0
            )
        )
        
        reservations = query.all()
        
        # Filter based on customer eligibility (implement based on business rules)
        # For now, return all available reservations
        
        result = []
        for reservation in reservations:
            reservation_data = self.response_schema().dump(reservation)
            reservation_data['contract'] = {
                'contract_number': reservation.contract.contract_number,
                'end_date': reservation.contract.end_date.isoformat() if reservation.contract.end_date else None
            }
            result.append(reservation_data)
        
        return result
    
    def get_reservation_utilization_report(self, contract_id: int = None) -> Dict[str, Any]:
        """Get reservation utilization report"""
        query = self.db.query(ContractReservation)
        
        if contract_id:
            query = query.filter(ContractReservation.contract_id == contract_id)
        
        reservations = query.all()
        
        total_reserved = sum(res.reserved_quantity for res in reservations)
        total_allocated = sum(res.allocated_quantity for res in reservations)
        total_remaining = sum(res.remaining_quantity for res in reservations)
        
        # Group by contract
        by_contract = {}
        for reservation in reservations:
            contract_id = reservation.contract_id
            if contract_id not in by_contract:
                by_contract[contract_id] = {
                    'contract_number': reservation.contract.contract_number,
                    'reserved': 0,
                    'allocated': 0,
                    'remaining': 0,
                    'reservations_count': 0
                }
            
            by_contract[contract_id]['reserved'] += reservation.reserved_quantity
            by_contract[contract_id]['allocated'] += reservation.allocated_quantity
            by_contract[contract_id]['remaining'] += reservation.remaining_quantity
            by_contract[contract_id]['reservations_count'] += 1
        
        # Calculate utilization percentages
        for contract_data in by_contract.values():
            if contract_data['reserved'] > 0:
                contract_data['utilization_percentage'] = (
                    contract_data['allocated'] / contract_data['reserved'] * 100
                )
            else:
                contract_data['utilization_percentage'] = 0
        
        return {
            'summary': {
                'total_reservations': len(reservations),
                'total_reserved_quantity': total_reserved,
                'total_allocated_quantity': total_allocated,
                'total_remaining_quantity': total_remaining,
                'overall_utilization_percentage': (total_allocated / total_reserved * 100) if total_reserved > 0 else 0
            },
            'by_contract': list(by_contract.values())
        }
    
    def _validate_contract(self, contract_id: int) -> TenderContract:
        """Validate contract exists dan can accept reservations"""
        contract = self._get_or_404(TenderContract, contract_id)
        
        if contract.status != 'ACTIVE':
            raise ContractError(f"Contract {contract.contract_number} is not active")
        
        if contract.end_date and contract.end_date <= date.today():
            raise ContractError(f"Contract {contract.contract_number} has expired")
        
        return contract
    
    def _validate_batch_for_reservation(self, batch_id: int) -> Batch:
        """Validate batch can be reserved"""
        batch = self._get_or_404(Batch, batch_id)
        
        if batch.status != 'ACTIVE':
            raise ValidationError(f"Batch {batch.batch_number} is not active")
        
        if batch.qc_status != 'PASSED':
            raise ValidationError(f"Batch {batch.batch_number} has not passed QC")
        
        return batch