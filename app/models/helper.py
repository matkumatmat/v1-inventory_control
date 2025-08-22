from app.models.base import BaseModel, db  
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy import Numeric

# ==================== PRODUCT RELATED ENUMS ====================

class ProductType(BaseModel):
    """Master data untuk jenis produk"""
    __tablename__ = 'product_types'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    
    # Additional properties
    requires_batch_tracking = db.Column(db.Boolean, default=True)
    requires_expiry_tracking = db.Column(db.Boolean, default=True)
    shelf_life_days = db.Column(db.Integer)  # Default shelf life
    
    # Relationships
    products = db.relationship('Product', back_populates='product_type')
    
    def __repr__(self):
        return f'<ProductType {self.code}: {self.name}>'

class PackageType(BaseModel):
    """Master data untuk jenis kemasan"""
    __tablename__ = 'package_types'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Package properties
    is_fragile = db.Column(db.Boolean, default=False, nullable=False)
    is_stackable = db.Column(db.Boolean, default=True, nullable=False)
    max_stack_height = db.Column(db.Integer)  # Max units yang bisa ditumpuk
    
    # Standard dimensions (jika ada)
    standard_length = db.Column(db.Float)
    standard_width = db.Column(db.Float)
    standard_height = db.Column(db.Float)
    standard_weight = db.Column(db.Float)
    
    # Handling requirements
    special_handling_required = db.Column(db.Boolean, default=False)
    handling_instructions = db.Column(db.Text)
    
    # Relationships
    products = db.relationship('Product', back_populates='package_type')
    
    def __repr__(self):
        return f'<PackageType {self.code}: {self.name}>'

class TemperatureType(BaseModel):
    """Master data untuk jenis suhu penyimpanan"""
    __tablename__ = 'temperature_types'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Temperature ranges
    min_celsius = db.Column(db.Float)
    max_celsius = db.Column(db.Float)
    optimal_celsius = db.Column(db.Float)
    
    # Display format
    celsius_display = db.Column(db.String(20))  # e.g., "2-8°C", "-18°C"
    
    # Storage requirements
    humidity_range = db.Column(db.String(20))  # e.g., "45-75%"
    special_storage_requirements = db.Column(db.Text)
    
    # Colors for UI
    color_code = db.Column(db.String(7))  # Hex color untuk UI
    icon = db.Column(db.String(50))  # Icon name untuk UI
    
    # Relationships
    products = db.relationship('Product', back_populates='temperature_type')
    
    def __repr__(self):
        return f'<TemperatureType {self.code}: {self.name}>'

# ==================== ALLOCATION & MOVEMENT ENUMS ====================

class AllocationType(BaseModel):
    """Master data untuk jenis alokasi"""
    __tablename__ = 'allocation_types'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Allocation properties
    requires_customer = db.Column(db.Boolean, default=False)  # Tender memerlukan customer
    is_reservable = db.Column(db.Boolean, default=True)  # Bisa di-reserve atau tidak
    auto_assign_customer = db.Column(db.Boolean, default=False)  # Auto assign dari SO
    
    # Business rules
    priority_level = db.Column(db.Integer, default=1)  # 1=highest, 9=lowest
    max_allocation_days = db.Column(db.Integer)  # Max hari sebelum expired
    
    # Colors for UI
    color_code = db.Column(db.String(7))  # Hex color
    icon = db.Column(db.String(50))
    
    # Relationships
    allocations = db.relationship('Allocation', back_populates='allocation_type')
    
    def __repr__(self):
        return f'<AllocationType {self.code}: {self.name}>'

class MovementType(BaseModel):
    """Master data untuk jenis pergerakan stock"""
    __tablename__ = 'movement_types'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Movement direction
    direction = db.Column(db.String(10), nullable=False)  # IN, OUT, TRANSFER
    affects_stock = db.Column(db.Boolean, default=True)  # Apakah mempengaruhi stock
    
    # Auto generation rules
    auto_generate_document = db.Column(db.Boolean, default=False)
    document_prefix = db.Column(db.String(10))
    
    # Approval requirements
    requires_approval = db.Column(db.Boolean, default=False)
    approval_level = db.Column(db.Integer, default=1)
    
    # Relationships
    stock_movements = db.relationship('StockMovement', back_populates='movement_type')
    
    def __repr__(self):
        return f'<MovementType {self.code}: {self.name}>'

# ==================== CUSTOMER & SECTOR ENUMS ====================

class SectorType(BaseModel):
    """Master data untuk jenis sektor customer"""
    __tablename__ = 'sector_types'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Sector properties
    requires_special_handling = db.Column(db.Boolean, default=False)
    default_payment_terms = db.Column(db.Integer)  # Days
    default_delivery_terms = db.Column(db.String(50))
    
    # Compliance requirements
    requires_temperature_monitoring = db.Column(db.Boolean, default=False)
    requires_chain_of_custody = db.Column(db.Boolean, default=False)
    special_documentation = db.Column(db.Text)
    
    # Relationships
    customers = db.relationship('Customer', back_populates='sector_type')
    
    def __repr__(self):
        return f'<SectorType {self.code}: {self.name}>'

class CustomerType(BaseModel):
    """Master data untuk jenis customer"""
    __tablename__ = 'customer_types'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Customer properties
    allows_tender_allocation = db.Column(db.Boolean, default=False)
    requires_pre_approval = db.Column(db.Boolean, default=False)
    default_credit_limit = db.Column(db.Numeric(15, 2))
    
    # Pricing and terms
    default_discount_percent = db.Column(db.Numeric(5, 2))
    default_payment_terms_days = db.Column(db.Integer, default=30)
    
    # Relationships
    customers = db.relationship('Customer', back_populates='customer_type')
    
    def __repr__(self):
        return f'<CustomerType {self.code}: {self.name}>'

# ==================== DOCUMENT & STATUS ENUMS ====================

class DocumentType(BaseModel):
    """Master data untuk jenis dokumen"""
    __tablename__ = 'document_types'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Document properties
    is_mandatory = db.Column(db.Boolean, default=False)
    is_customer_visible = db.Column(db.Boolean, default=True)
    max_file_size_mb = db.Column(db.Integer, default=10)
    allowed_extensions = db.Column(db.String(100))  # e.g., "pdf,jpg,png"
    
    # Auto generation
    auto_generate = db.Column(db.Boolean, default=False)
    template_path = db.Column(db.String(255))
    
    # Relationships
    shipment_documents = db.relationship('ShipmentDocument', back_populates='document_type')
    
    def __repr__(self):
        return f'<DocumentType {self.code}: {self.name}>'

class StatusType(BaseModel):
    """Master data untuk berbagai status dalam sistem"""
    __tablename__ = 'status_types'
    
    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(50), nullable=False, index=True)  # SO, SHIPMENT, PICKING, etc
    code = db.Column(db.String(20), nullable=False, index=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Status properties
    is_initial_status = db.Column(db.Boolean, default=False)
    is_final_status = db.Column(db.Boolean, default=False)
    is_error_status = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    
    # UI properties
    color_code = db.Column(db.String(7))  # Hex color
    icon = db.Column(db.String(50))
    css_class = db.Column(db.String(50))
    
    # Business rules
    auto_transition_after_hours = db.Column(db.Integer)  # Auto transition setelah X jam
    requires_approval = db.Column(db.Boolean, default=False)
    sends_notification = db.Column(db.Boolean, default=False)
    
    # Unique constraint untuk entity_type + code
    __table_args__ = (
        db.UniqueConstraint('entity_type', 'code', name='uq_status_entity_code'),
    )
    
    def __repr__(self):
        return f'<StatusType {self.entity_type}.{self.code}: {self.name}>'

# ==================== SHIPPING & LOGISTICS ENUMS ====================

class ShippingMethod(BaseModel):
    """Master data untuk metode pengiriman"""
    __tablename__ = 'shipping_methods'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Shipping properties
    estimated_delivery_days = db.Column(db.Integer, nullable=False)
    max_weight_kg = db.Column(db.Float)
    max_dimensions_cm = db.Column(db.String(20))  # e.g., "100x100x100"
    
    # Cost calculation
    base_cost = db.Column(db.Numeric(10, 2))
    cost_per_kg = db.Column(db.Numeric(8, 2))
    cost_per_km = db.Column(db.Numeric(8, 4))
    fuel_surcharge_percent = db.Column(db.Numeric(5, 2))
    
    # Service features
    includes_insurance = db.Column(db.Boolean, default=False)
    includes_tracking = db.Column(db.Boolean, default=True)
    requires_signature = db.Column(db.Boolean, default=False)
    supports_cod = db.Column(db.Boolean, default=False)  # Cash on Delivery
    
    def __repr__(self):
        return f'<ShippingMethod {self.code}: {self.name}>'

class CarrierType(BaseModel):
    """Master data untuk jenis kurir"""
    __tablename__ = 'carrier_types'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Integration properties
    has_api_integration = db.Column(db.Boolean, default=False)
    api_type = db.Column(db.String(20))  # REST, SOAP, FTP
    supports_real_time_tracking = db.Column(db.Boolean, default=False)
    
    # Service capabilities
    supports_same_day = db.Column(db.Boolean, default=False)
    supports_next_day = db.Column(db.Boolean, default=False)
    supports_international = db.Column(db.Boolean, default=False)
    supports_temperature_controlled = db.Column(db.Boolean, default=False)
    
    # Relationships
    carriers = db.relationship('Carrier', back_populates='carrier_type')
    
    def __repr__(self):
        return f'<CarrierType {self.code}: {self.name}>'

# ==================== WAREHOUSE & PACKING ENUMS ====================

class LocationType(BaseModel):
    """Master data untuk jenis lokasi dalam warehouse"""
    __tablename__ = 'location_types'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Location properties
    is_storage_location = db.Column(db.Boolean, default=True)
    is_picking_location = db.Column(db.Boolean, default=True)
    is_staging_location = db.Column(db.Boolean, default=False)
    
    # Capacity and restrictions
    max_weight_capacity_kg = db.Column(db.Float)
    supports_temperature_control = db.Column(db.Boolean, default=False)
    requires_special_access = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<LocationType {self.code}: {self.name}>'

class PackagingMaterial(BaseModel):
    """Master data untuk material kemasan"""
    __tablename__ = 'packaging_materials'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Material properties
    material_type = db.Column(db.String(20))  # BOX, BUBBLE_WRAP, TAPE, etc
    is_reusable = db.Column(db.Boolean, default=False)
    is_fragile_protection = db.Column(db.Boolean, default=False)
    is_temperature_protection = db.Column(db.Boolean, default=False)
    
    # Dimensions and weight
    length_cm = db.Column(db.Float)
    width_cm = db.Column(db.Float)
    height_cm = db.Column(db.Float)
    weight_g = db.Column(db.Float)
    
    # Cost
    cost_per_unit = db.Column(db.Numeric(8, 2))
    
    def __repr__(self):
        return f'<PackagingMaterial {self.code}: {self.name}>'

# ==================== SYSTEM & NOTIFICATION ENUMS ====================

class PriorityLevel(BaseModel):
    """Master data untuk tingkat prioritas"""
    __tablename__ = 'priority_levels'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Priority properties
    level = db.Column(db.Integer, unique=True, nullable=False)  # 1=highest, 9=lowest
    sla_hours = db.Column(db.Integer)  # SLA dalam jam
    escalation_hours = db.Column(db.Integer)  # Escalate setelah X jam
    
    # UI properties
    color_code = db.Column(db.String(7))
    icon = db.Column(db.String(50))
    
    def __repr__(self):
        return f'<PriorityLevel {self.code}: {self.name}>'

class NotificationType(BaseModel):
    """Master data untuk jenis notifikasi"""
    __tablename__ = 'notification_types'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Notification properties
    is_email_enabled = db.Column(db.Boolean, default=True)
    is_sms_enabled = db.Column(db.Boolean, default=False)
    is_push_enabled = db.Column(db.Boolean, default=True)
    is_system_notification = db.Column(db.Boolean, default=True)
    
    # Template properties
    email_template = db.Column(db.String(100))
    sms_template = db.Column(db.String(100))
    push_template = db.Column(db.String(100))
    
    # Delivery rules
    retry_count = db.Column(db.Integer, default=3)
    retry_interval_minutes = db.Column(db.Integer, default=5)
    
    def __repr__(self):
        return f'<NotificationType {self.code}: {self.name}>'