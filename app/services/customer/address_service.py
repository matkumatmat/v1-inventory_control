"""
Customer Address Service
========================

Service untuk Customer Address management
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..base import CRUDService, transactional, audit_log
from ..exceptions import ValidationError, BusinessRuleError, NotFoundError
from ...models import CustomerAddress, Customer
from ...schemas import CustomerAddressSchema, CustomerAddressCreateSchema, CustomerAddressUpdateSchema

class CustomerAddressService(CRUDService):
    """Service untuk Customer Address management"""
    
    model_class = CustomerAddress
    create_schema = CustomerAddressCreateSchema
    update_schema = CustomerAddressUpdateSchema
    response_schema = CustomerAddressSchema
    search_fields = ['address_name', 'address_line1', 'city']
    
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)
    
    @transactional
    @audit_log('CREATE', 'CustomerAddress')
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create customer address dengan validation"""
        # Validate customer exists
        customer_id = data.get('customer_id')
        customer = self._get_or_404(Customer, customer_id)
        
        # Handle default address logic
        is_default = data.get('is_default', False)
        if is_default:
            self._unset_other_default_addresses(customer_id)
        
        # If this is first address, make it default
        existing_addresses_count = self.db_session.query(CustomerAddress).filter(
            CustomerAddress.customer_id == customer_id
        ).count()
        
        if existing_addresses_count == 0:
            data['is_default'] = True
        
        return super().create(data)
    
    @transactional
    @audit_log('UPDATE', 'CustomerAddress')
    def update(self, entity_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update customer address dengan validation"""
        address = self._get_or_404(CustomerAddress, entity_id)
        
        # Handle default address logic
        is_default = data.get('is_default')
        if is_default:
            self._unset_other_default_addresses(address.customer_id, exclude_id=entity_id)
        
        return super().update(entity_id, data)
    
    @transactional
    @audit_log('DELETE', 'CustomerAddress')
    def delete(self, entity_id: int) -> bool:
        """Delete customer address dengan validation"""
        address = self._get_or_404(CustomerAddress, entity_id)
        
        # Cannot delete if it's the only address
        other_addresses_count = self.db_session.query(CustomerAddress).filter(
            and_(
                CustomerAddress.customer_id == address.customer_id,
                CustomerAddress.id != entity_id,
                CustomerAddress.is_active == True
            )
        ).count()
        
        if other_addresses_count == 0:
            raise BusinessRuleError("Cannot delete the only address for customer")
        
        # If deleting default address, set another as default
        if address.is_default:
            self._set_new_default_address(address.customer_id, exclude_id=entity_id)
        
        return super().delete(entity_id)
    
    @transactional
    def set_as_default(self, address_id: int) -> Dict[str, Any]:
        """Set address sebagai default"""
        address = self._get_or_404(CustomerAddress, address_id)
        
        # Unset other default addresses
        self._unset_other_default_addresses(address.customer_id, exclude_id=address_id)
        
        # Set this as default
        address.is_default = True
        self._set_audit_fields(address, is_update=True)
        
        return self.response_schema().dump(address)
    
    def get_customer_addresses(self, customer_id: int, 
                             address_type: str = None) -> List[Dict[str, Any]]:
        """Get all addresses untuk customer"""
        query = self.db_session.query(CustomerAddress).filter(
            and_(
                CustomerAddress.customer_id == customer_id,
                CustomerAddress.is_active == True
            )
        )
        
        if address_type:
            query = query.filter(CustomerAddress.address_type == address_type)
        
        query = query.order_by(CustomerAddress.is_default.desc(), CustomerAddress.address_name.asc())
        
        addresses = query.all()
        return self.response_schema(many=True).dump(addresses)
    
    def get_default_address(self, customer_id: int) -> Dict[str, Any]:
        """Get default address untuk customer"""
        address = self.db_session.query(CustomerAddress).filter(
            and_(
                CustomerAddress.customer_id == customer_id,
                CustomerAddress.is_default == True,
                CustomerAddress.is_active == True
            )
        ).first()
        
        if not address:
            raise NotFoundError('Default Address', f'for customer {customer_id}')
        
        return self.response_schema().dump(address)
    
    def get_delivery_addresses(self, customer_id: int) -> List[Dict[str, Any]]:
        """Get delivery addresses untuk customer"""
        return self.get_customer_addresses(customer_id, address_type='DELIVERY')
    
    def _unset_other_default_addresses(self, customer_id: int, exclude_id: int = None):
        """Unset default flag dari addresses lain"""
        query = self.db_session.query(CustomerAddress).filter(
            and_(
                CustomerAddress.customer_id == customer_id,
                CustomerAddress.is_default == True
            )
        )
        
        if exclude_id:
            query = query.filter(CustomerAddress.id != exclude_id)
        
        addresses = query.all()
        for address in addresses:
            address.is_default = False
            self._set_audit_fields(address, is_update=True)
    
    def _set_new_default_address(self, customer_id: int, exclude_id: int = None):
        """Set address lain sebagai default ketika default address dihapus"""
        query = self.db_session.query(CustomerAddress).filter(
            and_(
                CustomerAddress.customer_id == customer_id,
                CustomerAddress.is_active == True
            )
        )
        
        if exclude_id:
            query = query.filter(CustomerAddress.id != exclude_id)
        
        new_default = query.first()
        if new_default:
            new_default.is_default = True
            self._set_audit_fields(new_default, is_update=True)