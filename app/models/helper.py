import uuid
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Text, DateTime, Date, Numeric, Boolean,
    Float, func, UniqueConstraint
)
from sqlalchemy.orm import relationship
from .base import BaseModel

# ==================== PRODUCT RELATED ENUMS ====================

class ProductType(BaseModel):
    """Master data untuk jenis produk"""
    __tablename__ = 'product_types'
    
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0)
    
    # Additional properties
    requires_batch_tracking = Column(Boolean, default=True)
    requires_expiry_tracking = Column(Boolean, default=True)
    shelf_life_days = Column(Integer)  # Default shelf life
    
    # Relationships
    products = relationship('Product', back_populates='product_type')
    
    def __repr__(self):
        return f'<ProductType {self.code}: {self.name}>'

class PackageType(BaseModel):
    """Master data untuk jenis kemasan"""
    __tablename__ = 'package_types'
    
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Package properties
    is_fragile = Column(Boolean, default=False, nullable=False)
    is_stackable = Column(Boolean, default=True, nullable=False)
    max_stack_height = Column(Integer)  # Max units yang bisa ditumpuk
    
    # Standard dimensions (jika ada)
    standard_length = Column(Float)
    standard_width = Column(Float)
    standard_height = Column(Float)
    standard_weight = Column(Float)
    
    # Handling requirements
    special_handling_required = Column(Boolean, default=False)
    handling_instructions = Column(Text)
    
    # Relationships
    products = relationship('Product', back_populates='package_type')
    
    def __repr__(self):
        return f'<PackageType {self.code}: {self.name}>'

class TemperatureType(BaseModel):
    """Master data untuk jenis suhu penyimpanan"""
    __tablename__ = 'temperature_types'
    
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Temperature ranges
    min_celsius = Column(Float)
    max_celsius = Column(Float)
    optimal_celsius = Column(Float)
    
    # Display format
    celsius_display = Column(String(20))  # e.g., "2-8°C", "-18°C"
    
    # Storage requirements
    humidity_range = Column(String(20))  # e.g., "45-75%"
    special_storage_requirements = Column(Text)
    
    # Colors for UI
    color_code = Column(String(7))  # Hex color untuk UI
    icon = Column(String(50))  # Icon name untuk UI
    
    # Relationships
    products = relationship('Product', back_populates='temperature_type')
    
    def __repr__(self):
        return f'<TemperatureType {self.code}: {self.name}>'

# ==================== ALLOCATION & MOVEMENT ENUMS ====================

class AllocationType(BaseModel):
    """Master data untuk jenis alokasi"""
    __tablename__ = 'allocation_types'
    
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Allocation properties
    requires_customer = Column(Boolean, default=False)  # Tender memerlukan customer
    is_reservable = Column(Boolean, default=True)  # Bisa di-reserve atau tidak
    auto_assign_customer = Column(Boolean, default=False)  # Auto assign dari SO
    
    # Business rules
    priority_level = Column(Integer, default=1)  # 1=highest, 9=lowest
    max_allocation_days = Column(Integer)  # Max hari sebelum expired
    
    # Colors for UI
    color_code = Column(String(7))  # Hex color
    icon = Column(String(50))
    
    # Relationships
    allocations = relationship('Allocation', back_populates='allocation_type')
    
    def __repr__(self):
        return f'<AllocationType {self.code}: {self.name}>'

class MovementType(BaseModel):
    """Master data untuk jenis pergerakan stock"""
    __tablename__ = 'movement_types'
    
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Movement direction
    direction = Column(String(10), nullable=False)  # IN, OUT, TRANSFER
    affects_stock = Column(Boolean, default=True)  # Apakah mempengaruhi stock
    
    # Auto generation rules
    auto_generate_document = Column(Boolean, default=False)
    document_prefix = Column(String(10))
    
    # Approval requirements
    requires_approval = Column(Boolean, default=False)
    approval_level = Column(Integer, default=1)
    
    # Relationships
    stock_movements = relationship('StockMovement', back_populates='movement_type')
    
    def __repr__(self):
        return f'<MovementType {self.code}: {self.name}>'

# ==================== CUSTOMER & SECTOR ENUMS ====================

class SectorType(BaseModel):
    """Master data untuk jenis sektor customer"""
    __tablename__ = 'sector_types'
    
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Sector properties
    requires_special_handling = Column(Boolean, default=False)
    default_payment_terms = Column(Integer)  # Days
    default_delivery_terms = Column(String(50))
    
    # Compliance requirements
    requires_temperature_monitoring = Column(Boolean, default=False)
    requires_chain_of_custody = Column(Boolean, default=False)
    special_documentation = Column(Text)
    
    # Relationships
    customers = relationship('Customer', back_populates='sector_type')
    
    def __repr__(self):
        return f'<SectorType {self.code}: {self.name}>'

class CustomerType(BaseModel):
    """Master data untuk jenis customer"""
    __tablename__ = 'customer_types'
    
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Customer properties
    allows_tender_allocation = Column(Boolean, default=False)
    requires_pre_approval = Column(Boolean, default=False)
    default_credit_limit = Column(Numeric(15, 2))
    
    # Pricing and terms
    default_discount_percent = Column(Numeric(5, 2))
    default_payment_terms_days = Column(Integer, default=30)
    
    # Relationships
    customers = relationship('Customer', back_populates='customer_type')
    
    def __repr__(self):
        return f'<CustomerType {self.code}: {self.name}>'

# ==================== DOCUMENT & STATUS ENUMS ====================

class DocumentType(BaseModel):
    """Master data untuk jenis dokumen"""
    __tablename__ = 'document_types'
    
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Document properties
    is_mandatory = Column(Boolean, default=False)
    is_customer_visible = Column(Boolean, default=True)
    max_file_size_mb = Column(Integer, default=10)
    allowed_extensions = Column(String(100))  # e.g., "pdf,jpg,png"
    
    # Auto generation
    auto_generate = Column(Boolean, default=False)
    template_path = Column(String(255))
    
    # Relationships
    shipment_documents = relationship('ShipmentDocument', back_populates='document_type')
    
    def __repr__(self):
        return f'<DocumentType {self.code}: {self.name}>'

class StatusType(BaseModel):
    """Master data untuk berbagai status dalam sistem"""
    __tablename__ = 'status_types'
    
    entity_type = Column(String(50), nullable=False, index=True)  # SO, SHIPMENT, PICKING, etc
    code = Column(String(20), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Status properties
    is_initial_status = Column(Boolean, default=False)
    is_final_status = Column(Boolean, default=False)
    is_error_status = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    
    # UI properties
    color_code = Column(String(7))  # Hex color
    icon = Column(String(50))
    css_class = Column(String(50))
    
    # Business rules
    auto_transition_after_hours = Column(Integer)  # Auto transition setelah X jam
    requires_approval = Column(Boolean, default=False)
    sends_notification = Column(Boolean, default=False)
    
    # Unique constraint untuk entity_type + code
    __table_args__ = (
        UniqueConstraint('entity_type', 'code', name='uq_status_entity_code'),
    )
    
    def __repr__(self):
        return f'<StatusType {self.entity_type}.{self.code}: {self.name}>'

# ==================== SHIPPING & LOGISTICS ENUMS ====================

class ShippingMethod(BaseModel):
    """Master data untuk metode pengiriman"""
    __tablename__ = 'shipping_methods'
    
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Shipping properties
    estimated_delivery_days = Column(Integer, nullable=False)
    max_weight_kg = Column(Float)
    max_dimensions_cm = Column(String(20))  # e.g., "100x100x100"
    
    # Cost calculation
    base_cost = Column(Numeric(10, 2))
    cost_per_kg = Column(Numeric(8, 2))
    cost_per_km = Column(Numeric(8, 4))
    fuel_surcharge_percent = Column(Numeric(5, 2))
    
    # Service features
    includes_insurance = Column(Boolean, default=False)
    includes_tracking = Column(Boolean, default=True)
    requires_signature = Column(Boolean, default=False)
    supports_cod = Column(Boolean, default=False)  # Cash on Delivery
    
    def __repr__(self):
        return f'<ShippingMethod {self.code}: {self.name}>'

class CarrierType(BaseModel):
    """Master data untuk jenis kurir"""
    __tablename__ = 'carrier_types'
    
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Integration properties
    has_api_integration = Column(Boolean, default=False)
    api_type = Column(String(20))  # REST, SOAP, FTP
    supports_real_time_tracking = Column(Boolean, default=False)
    
    # Service capabilities
    supports_same_day = Column(Boolean, default=False)
    supports_next_day = Column(Boolean, default=False)
    supports_international = Column(Boolean, default=False)
    supports_temperature_controlled = Column(Boolean, default=False)
    
    # Relationships
    carriers = relationship('Carrier', back_populates='carrier_type')
    
    def __repr__(self):
        return f'<CarrierType {self.code}: {self.name}>'

# ==================== WAREHOUSE & PACKING ENUMS ====================

class LocationType(BaseModel):
    """Master data untuk jenis lokasi dalam warehouse"""
    __tablename__ = 'location_types'
    
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Location properties
    is_storage_location = Column(Boolean, default=True)
    is_picking_location = Column(Boolean, default=True)
    is_staging_location = Column(Boolean, default=False)
    
    # Capacity and restrictions
    max_weight_capacity_kg = Column(Float)
    supports_temperature_control = Column(Boolean, default=False)
    requires_special_access = Column(Boolean, default=False)
    
    def __repr__(self):
        return f'<LocationType {self.code}: {self.name}>'

class PackagingMaterial(BaseModel):
    """Master data untuk material kemasan"""
    __tablename__ = 'packaging_materials'
    
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Material properties
    material_type = Column(String(20))  # BOX, BUBBLE_WRAP, TAPE, etc
    is_reusable = Column(Boolean, default=False)
    is_fragile_protection = Column(Boolean, default=False)
    is_temperature_protection = Column(Boolean, default=False)
    
    # Dimensions and weight
    length_cm = Column(Float)
    width_cm = Column(Float)
    height_cm = Column(Float)
    weight_g = Column(Float)
    
    # Cost
    cost_per_unit = Column(Numeric(8, 2))
    
    def __repr__(self):
        return f'<PackagingMaterial {self.code}: {self.name}>'

# ==================== SYSTEM & NOTIFICATION ENUMS ====================

class PriorityLevel(BaseModel):
    """Master data untuk tingkat prioritas"""
    __tablename__ = 'priority_levels'
    
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Priority properties
    level = Column(Integer, unique=True, nullable=False)  # 1=highest, 9=lowest
    sla_hours = Column(Integer)  # SLA dalam jam
    escalation_hours = Column(Integer)  # Escalate setelah X jam
    
    # UI properties
    color_code = Column(String(7))
    icon = Column(String(50))
    
    def __repr__(self):
        return f'<PriorityLevel {self.code}: {self.name}>'

class NotificationType(BaseModel):
    """Master data untuk jenis notifikasi"""
    __tablename__ = 'notification_types'
    
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Notification properties
    is_email_enabled = Column(Boolean, default=True)
    is_sms_enabled = Column(Boolean, default=False)
    is_push_enabled = Column(Boolean, default=True)
    is_system_notification = Column(Boolean, default=True)
    
    # Template properties
    email_template = Column(String(100))
    sms_template = Column(String(100))
    push_template = Column(String(100))
    
    # Delivery rules
    retry_count = Column(Integer, default=3)
    retry_interval_minutes = Column(Integer, default=5)
    
    def __repr__(self):
        return f'<NotificationType {self.code}: {self.name}>'