"""
Customer Service
================

Service untuk Customer management dan business logic
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..base import CRUDService, transactional, audit_log
from ..exceptions import ValidationError, ConflictError, NotFoundError
from ...models import Customer, CustomerType, SectorType, CustomerAddress
from ...schemas import CustomerSchema, CustomerCreateSchema, CustomerUpdateSchema

class CustomerService(CRUDService):
    """Service untuk Customer management"""
    
    model_class = Customer
    create_schema = CustomerCreateSchema
    update_schema = CustomerUpdateSchema
    response_schema = CustomerSchema
    search_fields = ['name', 'customer_code', 'legal_name', 'email']
    
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)
    
    @transactional
    @audit_log('CREATE', 'Customer')
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create customer dengan validation"""
        # Validate customer code uniqueness
        customer_code = data.get('customer_code')
        if customer_code:
            self._validate_unique_field(Customer, 'customer_code', customer_code,
                                      error_message=f"Customer code '{customer_code}' already exists")
        
        # Validate email uniqueness if provided
        email = data.get('email')
        if email:
            self._validate_unique_field(Customer, 'email', email,
                                      error_message=f"Email '{email}' already exists")
        
        # Validate customer type and sector type
        self._validate_customer_type(data.get('customer_type_id'))
        self._validate_sector_type(data.get('sector_type_id'))
        
        return super().create(data)
    
    @transactional
    @audit_log('UPDATE', 'Customer')
    def update(self, entity_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update customer dengan validation"""
        # Validate customer code uniqueness if changed
        customer_code = data.get('customer_code')
        if customer_code:
            self._validate_unique_field(Customer, 'customer_code', customer_code,
                                      exclude_id=entity_id,
                                      error_message=f"Customer code '{customer_code}' already exists")
        
        # Validate email uniqueness if changed
        email = data.get('email')
        if email:
            self._validate_unique_field(Customer, 'email', email,
                                      exclude_id=entity_id,
                                      error_message=f"Email '{email}' already exists")
        
        # Validate references if changed
        if data.get('customer_type_id'):
            self._validate_customer_type(data.get('customer_type_id'))
        if data.get('sector_type_id'):
            self._validate_sector_type(data.get('sector_type_id'))
        
        return super().update(entity_id, data)
    
    def get_by_code(self, customer_code: str) -> Dict[str, Any]:
        """Get customer by customer code"""
        customer = self.db.query(Customer).filter(
            Customer.customer_code == customer_code
        ).first()
        
        if not customer:
            raise NotFoundError('Customer', customer_code)
        
        return self.response_schema().dump(customer)
    
    def search_customers(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search customers by name or code"""
        query = self.db.query(Customer).filter(Customer.is_active == True)
        
        if search_term:
            search_filter = (
                Customer.name.ilike(f'%{search_term}%') |
                Customer.customer_code.ilike(f'%{search_term}%') |
                Customer.legal_name.ilike(f'%{search_term}%')
            )
            query = query.filter(search_filter)
        
        customers = query.limit(limit).all()
        return self.response_schema(many=True).dump(customers)
    
    def get_customers_by_type(self, customer_type_id: int) -> List[Dict[str, Any]]:
        """Get customers by customer type"""
        query = self.db.query(Customer).filter(
            and_(Customer.customer_type_id == customer_type_id, Customer.is_active == True)
        ).order_by(Customer.name.asc())
        
        customers = query.all()
        return self.response_schema(many=True).dump(customers)
    
    def get_tender_eligible_customers(self) -> List[Dict[str, Any]]:
        """Get customers yang eligible untuk tender"""
        query = self.db.query(Customer).filter(
            and_(
                Customer.is_tender_eligible == True,
                Customer.is_active == True,
                Customer.status == 'ACTIVE'
            )
        ).order_by(Customer.name.asc())
        
        customers = query.all()
        return self.response_schema(many=True).dump(customers)
    
    def get_customer_summary(self, customer_id: int) -> Dict[str, Any]:
        """Get customer summary dengan related data"""
        customer = self._get_or_404(Customer, customer_id)
        
        # Get addresses
        addresses = self.db.query(CustomerAddress).filter(
            CustomerAddress.customer_id == customer_id
        ).all()
        
        # Get orders summary (if you have orders)
        # This would be implemented when you have sales order service
        
        return {
            'customer': self.response_schema().dump(customer),
            'addresses': [addr.__dict__ for addr in addresses],
            'summary': {
                'total_addresses': len(addresses),
                'default_address': next((addr for addr in addresses if addr.is_default), None),
                'delivery_addresses': [addr for addr in addresses if addr.address_type == 'DELIVERY']
            }
        }
    
    def _validate_customer_type(self, customer_type_id: int):
        """Validate customer type exists"""
        if not self.db.query(CustomerType).filter(CustomerType.id == customer_type_id).first():
            raise ValidationError(f"Customer type with ID {customer_type_id} not found")
    
    def _validate_sector_type(self, sector_type_id: int):
        """Validate sector type exists"""
        if not self.db.query(SectorType).filter(SectorType.id == sector_type_id).first():
            raise ValidationError(f"Sector type with ID {sector_type_id} not found")