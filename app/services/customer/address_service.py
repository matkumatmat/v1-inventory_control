"""
Customer Address Service
========================

Service untuk Customer Address management
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select, func

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
    
    def __init__(self, db_session: AsyncSession, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)
    
    @transactional
    @audit_log('CREATE', 'CustomerAddress')
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create customer address dengan validation"""
        # Validate customer exists
        customer_id = data.get('customer_id')
        customer = await self._get_or_404(Customer, customer_id)
        
        # Handle default address logic
        is_default = data.get('is_default', False)
        if is_default:
            await self._unset_other_default_addresses(customer_id)
        
        # If this is first address, make it default
        result = await self.db_session.execute(
            select(func.count(CustomerAddress.id)).filter(CustomerAddress.customer_id == customer_id)
        )
        existing_addresses_count = result.scalar_one()
        
        if existing_addresses_count == 0:
            data['is_default'] = True
        
        return await super().create(data)
    
    @transactional
    @audit_log('UPDATE', 'CustomerAddress')
    async def update(self, entity_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update customer address dengan validation"""
        address = await self._get_or_404(CustomerAddress, entity_id)
        
        # Handle default address logic
        is_default = data.get('is_default')
        if is_default:
            await self._unset_other_default_addresses(address.customer_id, exclude_id=entity_id)
        
        return await super().update(entity_id, data)
    
    @transactional
    @audit_log('DELETE', 'CustomerAddress')
    async def delete(self, entity_id: int) -> bool:
        """Delete customer address dengan validation"""
        address = await self._get_or_404(CustomerAddress, entity_id)
        
        # Cannot delete if it's the only address
        result = await self.db_session.execute(
            select(func.count(CustomerAddress.id)).filter(
                and_(
                    CustomerAddress.customer_id == address.customer_id,
                    CustomerAddress.id != entity_id,
                    CustomerAddress.is_active == True
                )
            )
        )
        other_addresses_count = result.scalar_one()
        
        if other_addresses_count == 0:
            raise BusinessRuleError("Cannot delete the only address for customer")
        
        # If deleting default address, set another as default
        if address.is_default:
            await self._set_new_default_address(address.customer_id, exclude_id=entity_id)
        
        return await super().delete(entity_id)
    
    @transactional
    async def set_as_default(self, address_id: int) -> Dict[str, Any]:
        """Set address sebagai default"""
        address = await self._get_or_404(CustomerAddress, address_id)
        
        # Unset other default addresses
        await self._unset_other_default_addresses(address.customer_id, exclude_id=address_id)
        
        # Set this as default
        address.is_default = True
        self._set_audit_fields(address, is_update=True)
        
        return self.response_schema().dump(address)
    
    async def get_customer_addresses(self, customer_id: int, 
                             address_type: str = None) -> List[Dict[str, Any]]:
        """Get all addresses untuk customer"""
        stmt = select(CustomerAddress).filter(
            and_(
                CustomerAddress.customer_id == customer_id,
                CustomerAddress.is_active == True
            )
        )
        
        if address_type:
            stmt = stmt.filter(CustomerAddress.address_type == address_type)
        
        stmt = stmt.order_by(CustomerAddress.is_default.desc(), CustomerAddress.address_name.asc())
        
        result = await self.db_session.execute(stmt)
        addresses = result.scalars().all()
        return self.response_schema(many=True).dump(addresses)
    
    async def get_default_address(self, customer_id: int) -> Dict[str, Any]:
        """Get default address untuk customer"""
        result = await self.db_session.execute(
            select(CustomerAddress).filter(
                and_(
                    CustomerAddress.customer_id == customer_id,
                    CustomerAddress.is_default == True,
                    CustomerAddress.is_active == True
                )
            )
        )
        address = result.scalars().first()
        
        if not address:
            raise NotFoundError('Default Address', f'for customer {customer_id}')
        
        return self.response_schema().dump(address)
    
    async def get_delivery_addresses(self, customer_id: int) -> List[Dict[str, Any]]:
        """Get delivery addresses untuk customer"""
        return await self.get_customer_addresses(customer_id, address_type='DELIVERY')
    
    async def _unset_other_default_addresses(self, customer_id: int, exclude_id: int = None):
        """Unset default flag dari addresses lain"""
        stmt = select(CustomerAddress).filter(
            and_(
                CustomerAddress.customer_id == customer_id,
                CustomerAddress.is_default == True
            )
        )
        
        if exclude_id:
            stmt = stmt.filter(CustomerAddress.id != exclude_id)
        
        result = await self.db_session.execute(stmt)
        addresses = result.scalars().all()
        for address in addresses:
            address.is_default = False
            self._set_audit_fields(address, is_update=True)
    
    async def _set_new_default_address(self, customer_id: int, exclude_id: int = None):
        """Set address lain sebagai default ketika default address dihapus"""
        stmt = select(CustomerAddress).filter(
            and_(
                CustomerAddress.customer_id == customer_id,
                CustomerAddress.is_active == True
            )
        )
        
        if exclude_id:
            stmt = stmt.filter(CustomerAddress.id != exclude_id)
        
        result = await self.db_session.execute(stmt)
        new_default = result.scalars().first()
        if new_default:
            new_default.is_default = True
            self._set_audit_fields(new_default, is_update=True)