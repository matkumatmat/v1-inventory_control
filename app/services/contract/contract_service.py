"""
Tender Contract Service
=======================

Service untuk Tender Contract management dan business logic
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_

from ..base import CRUDService, transactional, audit_log
from ..exceptions import ValidationError, BusinessRuleError, ContractError, NotFoundError
from ...models import TenderContract, ContractReservation, Customer, Allocation
from ...schemas import TenderContractSchema, TenderContractCreateSchema, TenderContractUpdateSchema

class TenderContractService(CRUDService):
    """Service untuk Tender Contract management"""
    
    model_class = TenderContract
    create_schema = TenderContractCreateSchema
    update_schema = TenderContractUpdateSchema
    response_schema = TenderContractSchema
    search_fields = ['contract_number', 'tender_reference', 'tender_winner']
    
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None, 
                 allocation_service=None, reservation_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)
        self.allocation_service = allocation_service
        self.reservation_service = reservation_service
    
    @transactional
    @audit_log('CREATE', 'TenderContract')
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create tender contract dengan validation"""
        # Validate contract number uniqueness
        contract_number = data.get('contract_number')
        if contract_number:
            self._validate_unique_field(TenderContract, 'contract_number', contract_number,
                                      error_message=f"Contract number '{contract_number}' already exists")
        
        # Validate date relationships
        self._validate_contract_dates(data)
        
        # Create contract
        contract_data = super().create(data)
        
        # Send notification
        self._send_notification('CONTRACT_CREATED', ['admin', 'sales_team'], {
            'contract_id': contract_data['id'],
            'contract_number': contract_number,
            'contract_value': data.get('contract_value'),
            'start_date': data.get('start_date'),
            'end_date': data.get('end_date')
        })
        
        return contract_data
    
    @transactional
    @audit_log('UPDATE', 'TenderContract')
    def update(self, entity_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update contract dengan validation"""
        contract = self._get_or_404(TenderContract, entity_id)
        
        # Restrict updates if contract has reservations
        if self._contract_has_reservations(entity_id):
            restricted_fields = ['start_date', 'end_date', 'contract_value']
            for field in restricted_fields:
                if field in data:
                    raise BusinessRuleError(f"Cannot update {field} - contract has active reservations")
        
        # Validate contract number uniqueness if changed
        contract_number = data.get('contract_number')
        if contract_number and contract_number != contract.contract_number:
            self._validate_unique_field(TenderContract, 'contract_number', contract_number,
                                      exclude_id=entity_id,
                                      error_message=f"Contract number '{contract_number}' already exists")
        
        # Validate dates if provided
        if any(key in data for key in ['contract_date', 'start_date', 'end_date']):
            self._validate_contract_dates(data, existing_contract=contract)
        
        return super().update(entity_id, data)
    
    @transactional
    @audit_log('ACTIVATE', 'TenderContract')
    def activate_contract(self, contract_id: int) -> Dict[str, Any]:
        """Activate contract"""
        contract = self._get_or_404(TenderContract, contract_id)
        
        # Validate can be activated
        if contract.status == 'ACTIVE':
            raise BusinessRuleError("Contract is already active")
        
        if contract.status == 'COMPLETED':
            raise BusinessRuleError("Cannot activate completed contract")
        
        if contract.end_date and contract.end_date <= date.today():
            raise BusinessRuleError("Cannot activate expired contract")
        
        # Activate contract
        contract.status = 'ACTIVE'
        self._set_audit_fields(contract, is_update=True)
        
        # Send notification
        self._send_notification('CONTRACT_ACTIVATED', ['admin', 'sales_team'], {
            'contract_id': contract_id,
            'contract_number': contract.contract_number
        })
        
        return self.response_schema().dump(contract)
    
    @transactional
    @audit_log('SUSPEND', 'TenderContract')
    def suspend_contract(self, contract_id: int, reason: str = None) -> Dict[str, Any]:
        """Suspend contract"""
        contract = self._get_or_404(TenderContract, contract_id)
        
        if contract.status != 'ACTIVE':
            raise BusinessRuleError("Only active contracts can be suspended")
        
        # Suspend contract
        contract.status = 'SUSPENDED'
        self._set_audit_fields(contract, is_update=True)
        
        # Log reason in notes or separate field
        if reason:
            contract.notes = f"Suspended: {reason}"
        
        # Send notification
        self._send_notification('CONTRACT_SUSPENDED', ['admin', 'sales_team'], {
            'contract_id': contract_id,
            'contract_number': contract.contract_number,
            'reason': reason
        })
        
        return self.response_schema().dump(contract)
    
    @transactional
    @audit_log('COMPLETE', 'TenderContract')
    def complete_contract(self, contract_id: int) -> Dict[str, Any]:
        """Complete contract"""
        contract = self._get_or_404(TenderContract, contract_id)
        
        if contract.status == 'COMPLETED':
            raise BusinessRuleError("Contract is already completed")
        
        # Check if all reservations are fulfilled
        pending_reservations = self.db_session.query(ContractReservation).filter(
            and_(
                ContractReservation.contract_id == contract_id,
                ContractReservation.remaining_quantity > 0
            )
        ).count()
        
        if pending_reservations > 0:
            raise BusinessRuleError("Cannot complete contract with pending reservations")
        
        # Complete contract
        contract.status = 'COMPLETED'
        self._set_audit_fields(contract, is_update=True)
        
        # Send notification
        self._send_notification('CONTRACT_COMPLETED', ['admin', 'sales_team'], {
            'contract_id': contract_id,
            'contract_number': contract.contract_number
        })
        
        return self.response_schema().dump(contract)
    
    def get_by_contract_number(self, contract_number: str) -> Dict[str, Any]:
        """Get contract by contract number"""
        contract = self.db_session.query(TenderContract).filter(
            TenderContract.contract_number == contract_number
        ).first()
        
        if not contract:
            raise NotFoundError('TenderContract', contract_number)
        
        return self.response_schema().dump(contract)
    
    def get_active_contracts(self, include_expiring: bool = True, 
                           days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Get active contracts"""
        query = self.db_session.query(TenderContract).filter(
            TenderContract.status == 'ACTIVE'
        )
        
        if not include_expiring:
            cutoff_date = date.today() + timedelta(days=days_ahead)
            query = query.filter(
                or_(TenderContract.end_date.is_(None), TenderContract.end_date > cutoff_date)
            )
        
        query = query.order_by(TenderContract.end_date.asc())
        
        contracts = query.all()
        
        # Add computed fields
        result = []
        for contract in contracts:
            contract_data = self.response_schema().dump(contract)
            
            # Calculate remaining days
            if contract.end_date:
                remaining_days = (contract.end_date - date.today()).days
                contract_data['remaining_days'] = remaining_days
                contract_data['is_expiring_soon'] = remaining_days <= days_ahead
            
            # Get reservation summary
            contract_data['reservation_summary'] = self._get_contract_reservation_summary(contract.id)
            
            result.append(contract_data)
        
        return result
    
    def get_expiring_contracts(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Get contracts yang akan expire"""
        cutoff_date = date.today() + timedelta(days=days_ahead)
        
        query = self.db_session.query(TenderContract).filter(
            and_(
                TenderContract.status == 'ACTIVE',
                TenderContract.end_date <= cutoff_date,
                TenderContract.end_date >= date.today()
            )
        ).order_by(TenderContract.end_date.asc())
        
        contracts = query.all()
        
        result = []
        for contract in contracts:
            contract_data = self.response_schema().dump(contract)
            contract_data['days_remaining'] = (contract.end_date - date.today()).days
            contract_data['reservation_summary'] = self._get_contract_reservation_summary(contract.id)
            result.append(contract_data)
        
        return result
    
    def get_contract_performance_report(self, contract_id: int) -> Dict[str, Any]:
        """Get contract performance report"""
        contract = self._get_or_404(TenderContract, contract_id)
        
        # Get all reservations
        reservations = self.db_session.query(ContractReservation).filter(
            ContractReservation.contract_id == contract_id
        ).all()
        
        # Get all allocations for this contract
        allocations = self.db_session.query(Allocation).filter(
            Allocation.tender_contract_id == contract_id
        ).all()
        
        # Calculate performance metrics
        total_reserved_value = sum(res.reserved_quantity * (res.unit_value or 0) for res in reservations)
        total_allocated_value = sum(alloc.allocated_quantity * (alloc.unit_value or 0) for alloc in allocations)
        total_shipped_value = sum(alloc.shipped_quantity * (alloc.unit_value or 0) for alloc in allocations)
        
        # Calculate percentages
        allocated_percentage = (total_allocated_value / total_reserved_value * 100) if total_reserved_value > 0 else 0
        shipped_percentage = (total_shipped_value / total_allocated_value * 100) if total_allocated_value > 0 else 0
        
        return {
            'contract': self.response_schema().dump(contract),
            'performance_metrics': {
                'total_reservations': len(reservations),
                'total_allocations': len(allocations),
                'total_reserved_value': total_reserved_value,
                'total_allocated_value': total_allocated_value,
                'total_shipped_value': total_shipped_value,
                'allocated_percentage': round(allocated_percentage, 2),
                'shipped_percentage': round(shipped_percentage, 2),
                'contract_utilization': round(shipped_percentage, 2)
            },
            'reservations': [
                {
                    'product_name': res.product.name,
                    'reserved_quantity': res.reserved_quantity,
                    'allocated_quantity': res.allocated_quantity,
                    'remaining_quantity': res.remaining_quantity,
                    'fulfillment_percentage': (res.allocated_quantity / res.reserved_quantity * 100) if res.reserved_quantity > 0 else 0
                }
                for res in reservations
            ]
        }
    
    def _validate_contract_dates(self, data: Dict[str, Any], existing_contract: TenderContract = None):
        """Validate contract date relationships"""
        contract_date = data.get('contract_date') or (existing_contract.contract_date if existing_contract else None)
        start_date = data.get('start_date') or (existing_contract.start_date if existing_contract else None)
        end_date = data.get('end_date') or (existing_contract.end_date if existing_contract else None)
        
        if start_date and end_date and start_date >= end_date:
            raise ValidationError("Start date must be before end date")
        
        if contract_date and start_date and contract_date > start_date:
            raise ValidationError("Contract date cannot be after start date")
        
        if end_date and end_date <= date.today():
            raise ValidationError("End date must be in the future")
    
    def _contract_has_reservations(self, contract_id: int) -> bool:
        """Check if contract has any reservations"""
        return self.db_session.query(ContractReservation).filter(
            ContractReservation.contract_id == contract_id
        ).count() > 0
    
    def _get_contract_reservation_summary(self, contract_id: int) -> Dict[str, Any]:
        """Get reservation summary for contract"""
        reservations = self.db_session.query(ContractReservation).filter(
            ContractReservation.contract_id == contract_id
        ).all()
        
        total_reserved = sum(res.reserved_quantity for res in reservations)
        total_allocated = sum(res.allocated_quantity for res in reservations)
        total_remaining = sum(res.remaining_quantity for res in reservations)
        
        return {
            'total_reservations': len(reservations),
            'total_reserved_quantity': total_reserved,
            'total_allocated_quantity': total_allocated,
            'total_remaining_quantity': total_remaining,
            'allocation_percentage': (total_allocated / total_reserved * 100) if total_reserved > 0 else 0
        }