import uuid
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Text, DateTime, Boolean, Float, func
)
from sqlalchemy.orm import relationship
from .base import BaseModel


# Jika belum ada Customer model, tambahkan:
class Customer(BaseModel):
    __tablename__ = 'customers'
    
    public_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)
    
    # Basic info
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    
    # Types
    customer_type_id = Column(Integer, ForeignKey('customer_types.id'), nullable=False)
    customer_type = relationship('CustomerType', back_populates='customers')
    
    sector_type_id = Column(Integer, ForeignKey('sector_types.id'), nullable=False)
    sector_type = relationship('SectorType', back_populates='customers')
    
    # Relationships
    sales_orders = relationship('SalesOrder', back_populates='customer')
    allocations = relationship('Allocation', back_populates='customer')
    consignment_agreements = relationship('ConsignmentAgreement', back_populates='customer')
    consignment_statements = relationship('ConsignmentStatement', back_populates='customer')    

    # TAMBAHAN: Enhanced relationships
    addresses = relationship('CustomerAddress', back_populates='customer', cascade='all, delete-orphan')
    
    @property
    def default_address(self):
        return next((addr for addr in self.addresses if addr.is_default), None)
    
    @property
    def delivery_addresses(self):
        return [addr for addr in self.addresses if addr.address_type == 'DELIVERY' and addr.is_active]    
    

class CustomerAddress(BaseModel):
    """Model untuk multiple addresses per customer"""
    __tablename__ = 'customer_addresses'
    
    public_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)
    
    # Customer reference
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    
    # Address details
    address_name = Column(String(100), nullable=False)
    address_type = Column(String(20), default='DELIVERY')
    
    # Full address
    address_line1 = Column(String(200), nullable=False)
    address_line2 = Column(String(200))
    city = Column(String(50), nullable=False)
    state_province = Column(String(50))
    postal_code = Column(String(10))
    country = Column(String(50), default='Indonesia')
    
    # Contact at this address
    contact_person = Column(String(100))
    contact_phone = Column(String(20))
    contact_email = Column(String(100))
    
    # Special instructions
    delivery_instructions = Column(Text)
    special_requirements = Column(Text)
    
    # GPS coordinates (optional)
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Flags
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Tracking
    created_by = Column(String(50))
    created_date = Column(DateTime, default=func.current_timestamp())
    
    # Relationships
    customer = relationship('Customer', back_populates='addresses')
    shipments = relationship('Shipment', back_populates='delivery_address')
    
    def __repr__(self):
        return f'<CustomerAddress {self.customer.name} - {self.address_name}>'
