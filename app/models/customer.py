from app.models.base import BaseModel,db  # ← Tambahkan ini
import uuid
from sqlalchemy.dialects.postgresql import UUID 


# Jika belum ada Customer model, tambahkan:
class Customer(BaseModel):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    
    # Basic info
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    
    # Types
    customer_type_id = db.Column(db.Integer, db.ForeignKey('customer_types.id'), nullable=False)
    customer_type = db.relationship('CustomerType', back_populates='customers')
    
    sector_type_id = db.Column(db.Integer, db.ForeignKey('sector_types.id'), nullable=False)
    sector_type = db.relationship('SectorType', back_populates='customers')
    
    # Relationships
    sales_orders = db.relationship('SalesOrder', back_populates='customer')
    allocations = db.relationship('Allocation', back_populates='customer')
    consignment_agreements = db.relationship('ConsignmentAgreement', back_populates='customer')
    consignment_statements = db.relationship('ConsignmentStatement', back_populates='customer')    

    # TAMBAHAN: Enhanced relationships
    addresses = db.relationship('CustomerAddress', back_populates='customer', cascade='all, delete-orphan')
    
    @property
    def default_address(self):
        return next((addr for addr in self.addresses if addr.is_default), None)
    
    @property
    def delivery_addresses(self):
        return [addr for addr in self.addresses if addr.address_type == 'DELIVERY' and addr.is_active]    
    

class CustomerAddress(BaseModel):
    """Model untuk multiple addresses per customer"""
    __tablename__ = 'customer_addresses'
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    
    # Customer reference
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    customer = db.relationship('Customer', back_populates='addresses')
    
    # Address details
    address_name = db.Column(db.String(100), nullable=False)
    address_type = db.Column(db.String(20), default='DELIVERY')
    
    # Full address
    address_line1 = db.Column(db.String(200), nullable=False)
    address_line2 = db.Column(db.String(200))
    city = db.Column(db.String(50), nullable=False)
    state_province = db.Column(db.String(50))
    postal_code = db.Column(db.String(10))
    country = db.Column(db.String(50), default='Indonesia')
    
    # Contact at this address
    contact_person = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    contact_email = db.Column(db.String(100))
    
    # Special instructions
    delivery_instructions = db.Column(db.Text)
    special_requirements = db.Column(db.Text)
    
    # GPS coordinates (optional)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # Flags
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Tracking
    created_by = db.Column(db.String(50))
    created_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationships
    shipments = db.relationship('Shipment', back_populates='delivery_address')
    
    def __repr__(self):
        return f'<CustomerAddress {self.customer.name} - {self.address_name}>'
