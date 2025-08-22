"""
WMS (Warehouse Management System) Models Package
==================================================

This package contains all database models for the WMS system.
Models are organized by domain and functionality.

Domain Structure:
- Core: Base model and database setup
- Product: Product, Batch, and Allocation management
- Warehouse: Warehouse and Rack management  
- Customer: Customer and related entities
- Sales: Sales Order and Shipping Plan management
- Picking: Picking List, Picking Order, and execution
- Packing: Packing Order and Box management
- Shipping: Shipment and delivery management
- Consignment: Consignment/titip jual management
- User: User management and authentication
- Helper: Enum tables and master data

Author: WMS Development Team
Version: 1.0.0
"""

# ==================== CORE IMPORTS ====================

from .base import BaseModel, db

# ==================== PRODUCT DOMAIN ====================

from .product import (
    # Core product entities
    Product,
    Batch,
    Allocation,
    StockMovement,
)

# ==================== WAREHOUSE DOMAIN ====================

from .warehouse import (
    Warehouse,
    Rack,
    RackAllocation
)

# ==================== CUSTOMER DOMAIN ====================

from .customer import (
    Customer,
    # Add other customer-related models if any
)

# ==================== SALES DOMAIN ====================

from .salesorder import (
    SalesOrder,
    SalesOrderItem,
    ShippingPlan,
    ShippingPlanItem,
)

# ==================== PICKING DOMAIN ====================

from .picking import (
    # Picking workflow
    PickingList,
    PickingListItem,
    PickingOrder,
    PickingOrderItem,
    
    # Packing workflow
    PackingOrder,
    PackingBox,
    PackingBoxItem,
)

# ==================== SHIPPING DOMAIN ====================

from .shipment import (
    # Core shipment
    Shipment,
    ShipmentDocument,
    ShipmentTracking,
    
    # Master data
    DeliveryMethod,
    Carrier,
)

# ==================== CONSIGNMENT DOMAIN ====================

from .consignment import (
    ConsignmentAgreement,
    Consignment,
    ConsignmentItem,
    ConsignmentSale,
    ConsignmentReturn,
    ConsignmentStatement,
)

# ==================== USER & SECURITY DOMAIN ====================

from .user import (
    User,
    UserRole,
    UserSession,
    UserActivity,
)

# ==================== HELPER/ENUM TABLES ====================

from .helper import (
    # Product related enums
    ProductType,
    PackageType,
    TemperatureType,
    
    # Allocation & movement enums
    AllocationType,
    MovementType,
    
    # Customer & sector enums
    SectorType,
    CustomerType,
    
    # Document & status enums
    DocumentType,
    StatusType,
    
    # Shipping & logistics enums
    ShippingMethod,
    CarrierType,
    
    # Warehouse & packing enums
    LocationType,
    PackagingMaterial,
    
    # System enums
    PriorityLevel,
    NotificationType,
)

# TAMBAHAN IMPORTS:

# ==================== CONTRACT DOMAIN ====================
from .contract import (
    TenderContract,
    ContractReservation,
)

# ==================== PACKING SLIP DOMAIN ====================
from .packing_slip import (
    PackingSlip,
)

# ==================== CUSTOMER DOMAIN (Enhanced) ====================
from .customer import (
    Customer,
    CustomerAddress,  # TAMBAHAN BARU
)

# ==================== AUDIT & LOGGING MODELS ====================

class AuditLog(BaseModel):
    """Model untuk Audit Trail semua perubahan data"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Event information
    entity_type = db.Column(db.String(50), nullable=False, index=True)  # SalesOrder, Product, etc
    entity_id = db.Column(db.Integer, nullable=False, index=True)
    action = db.Column(db.String(20), nullable=False, index=True)  # CREATE, UPDATE, DELETE, VIEW
    
    # User information
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user = db.relationship('User')
    username = db.Column(db.String(50))  # Backup jika user dihapus
    
    # Change details
    old_values = db.Column(db.JSON)  # JSON field untuk old values
    new_values = db.Column(db.JSON)  # JSON field untuk new values
    changed_fields = db.Column(db.JSON)  # Array field names yang berubah
    
    # Context information
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    request_id = db.Column(db.String(36))  # UUID untuk trace request
    
    # Additional context
    notes = db.Column(db.Text)
    severity = db.Column(db.String(10), default='INFO')  # DEBUG, INFO, WARN, ERROR
    
    # Timestamp
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp(), index=True)
    
    def __repr__(self):
        return f'<AuditLog {self.entity_type}({self.entity_id}) - {self.action}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'action': self.action,
            'username': self.username,
            'changed_fields': self.changed_fields,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'notes': self.notes
        }

class SystemLog(BaseModel):
    """Model untuk System Logs dan Error Tracking"""
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Log information
    level = db.Column(db.String(10), nullable=False, index=True)  # DEBUG, INFO, WARN, ERROR, FATAL
    logger_name = db.Column(db.String(100), index=True)
    message = db.Column(db.Text, nullable=False)
    
    # Context
    module = db.Column(db.String(50))
    function = db.Column(db.String(50))
    line_number = db.Column(db.Integer)
    
    # Exception details (jika error)
    exception_type = db.Column(db.String(100))
    exception_message = db.Column(db.Text)
    stack_trace = db.Column(db.Text)
    
    # Request context
    request_id = db.Column(db.String(36))
    user_id = db.Column(db.Integer)
    ip_address = db.Column(db.String(45))
    
    # Additional data
    extra_data = db.Column(db.JSON)
    
    # Timestamp
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp(), index=True)
    
    def __repr__(self):
        return f'<SystemLog {self.level}: {self.message[:50]}...>'

class NotificationLog(BaseModel):
    """Model untuk tracking notifikasi yang dikirim"""
    __tablename__ = 'notification_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Notification details
    notification_type_id = db.Column(db.Integer, db.ForeignKey('notification_types.id'), nullable=False)
    notification_type = db.relationship('NotificationType')
    
    # Recipient
    recipient_type = db.Column(db.String(20), nullable=False)  # USER, CUSTOMER, EXTERNAL
    recipient_id = db.Column(db.Integer)  # User ID atau Customer ID
    recipient_email = db.Column(db.String(100))
    recipient_phone = db.Column(db.String(20))
    
    # Message content
    subject = db.Column(db.String(200))
    message_body = db.Column(db.Text)
    
    # Delivery details
    delivery_method = db.Column(db.String(20), nullable=False)  # EMAIL, SMS, PUSH, SYSTEM
    delivery_status = db.Column(db.String(20), default='PENDING')  # PENDING, SENT, DELIVERED, FAILED
    delivery_attempts = db.Column(db.Integer, default=0)
    
    # Context
    entity_type = db.Column(db.String(50))  # SalesOrder, Shipment, etc
    entity_id = db.Column(db.Integer)
    
    # External provider details
    external_message_id = db.Column(db.String(100))  # ID dari provider (SendGrid, Twilio, etc)
    external_response = db.Column(db.JSON)
    
    # Timing
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    sent_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    failed_at = db.Column(db.DateTime)
    
    # Error details (jika gagal)
    error_message = db.Column(db.Text)
    error_code = db.Column(db.String(50))
    
    def __repr__(self):
        return f'<NotificationLog {self.notification_type.code if self.notification_type else "Unknown"} - {self.delivery_status}>'

# ==================== CONFIGURATION & SETTINGS ====================

class SystemConfiguration(BaseModel):
    """Model untuk system configuration dan settings"""
    __tablename__ = 'system_configurations'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Configuration key and value
    config_key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    config_value = db.Column(db.Text)
    config_type = db.Column(db.String(20), default='STRING')  # STRING, INTEGER, FLOAT, BOOLEAN, JSON
    
    # Metadata
    category = db.Column(db.String(50), index=True)  # SYSTEM, NOTIFICATION, BUSINESS, SECURITY
    description = db.Column(db.Text)
    is_sensitive = db.Column(db.Boolean, default=False)  # Untuk password, API keys, etc
    
    # Validation
    validation_rule = db.Column(db.Text)  # Regex atau rule untuk validasi
    default_value = db.Column(db.Text)
    
    # Access control
    is_user_editable = db.Column(db.Boolean, default=True)
    required_role = db.Column(db.String(20), default='admin')  # Role minimum untuk edit
    
    # Tracking
    last_modified_by = db.Column(db.String(50))
    last_modified_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    def get_typed_value(self):
        """Get value dengan tipe data yang sesuai"""
        if self.config_type == 'INTEGER':
            return int(self.config_value) if self.config_value else 0
        elif self.config_type == 'FLOAT':
            return float(self.config_value) if self.config_value else 0.0
        elif self.config_type == 'BOOLEAN':
            return self.config_value.lower() in ('true', '1', 'yes') if self.config_value else False
        elif self.config_type == 'JSON':
            import json
            return json.loads(self.config_value) if self.config_value else {}
        else:
            return self.config_value or ''
    
    def __repr__(self):
        return f'<SystemConfiguration {self.config_key}: {self.config_value}>'

# ==================== ALL MODEL EXPORTS ====================

__all__ = [
    # Core
    'BaseModel', 'db',
    
    # Product domain
    'Product', 'Batch', 'Allocation', 'StockMovement',
    
    # Warehouse domain
    'Warehouse', 'Rack',
    
    # Sales domain
    'SalesOrder', 'SalesOrderItem', 'ShippingPlan', 'ShippingPlanItem',
    
    # Picking domain
    'PickingList', 'PickingListItem', 'PickingOrder', 'PickingOrderItem',
    'PackingOrder', 'PackingBox', 'PackingBoxItem',
    
    # Shipping domain
    'Shipment', 'ShipmentDocument', 'ShipmentTracking',
    'DeliveryMethod', 'Carrier',
    
    # Consignment domain
    'ConsignmentAgreement', 'Consignment', 'ConsignmentItem',
    'ConsignmentSale', 'ConsignmentReturn', 'ConsignmentStatement',
    
    # User & security domain
    'User', 'UserRole', 'UserSession', 'UserActivity',
    
    # Audit & logging domain
    'AuditLog', 'SystemLog', 'NotificationLog',
    
    # Configuration
    'SystemConfiguration',
    
    # Helper/Enum tables
    'ProductType', 'PackageType', 'TemperatureType',
    'AllocationType', 'MovementType',
    'SectorType', 'CustomerType',
    'DocumentType', 'StatusType',
    'ShippingMethod', 'CarrierType',
    'LocationType', 'PackagingMaterial',
    'PriorityLevel', 'NotificationType',

    # Contract domain - TAMBAHAN BARU
    'TenderContract', 'ContractReservation',
    
    # Packing slip domain - TAMBAHAN BARU  
    'PackingSlip',
    
    # Customer domain (enhanced)
    'Customer', 'CustomerAddress',  # CustomerAddress adalah TAMBAHAN BARU    
]

# ==================== MODEL INITIALIZATION ====================

def init_app(app):
    """Initialize models with Flask app"""
    db.init_app(app)
    
    # Import all models to ensure they're registered with SQLAlchemy
    from . import (
        product, warehouse, customer, salesorder, picking, 
        shipment, consignment, user, helper,
        contract, packing_slip  # TAMBAHAN BARU
    )
    
    # Create tables if they don't exist (for development)
    with app.app_context():
        if app.config.get('SQLALCHEMY_CREATE_TABLES', False):
            db.create_all()
            # Initialize default data if needed
            _initialize_default_data()

def create_tables():
    """Create all tables (for migration scripts)"""
    db.create_all()

def drop_tables():
    """Drop all tables (for testing/reset)"""
    db.drop_all()

def _initialize_default_data():
    """Initialize default master data"""
    try:
        # Initialize default user roles, product types, etc.
        # This will be called only once during initial setup
        _init_default_helper_data()
        _init_default_system_config()
        _init_default_superadmin()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing default data: {e}")

def _init_default_helper_data():
    """Initialize default helper/enum data"""
    # ProductType default data
    if not ProductType.query.first():
        product_types = [
            {'code': 'DRUG', 'name': 'Pharmaceutical Drug', 'description': 'Prescription and OTC drugs'},
            {'code': 'VAC', 'name': 'Vaccine', 'description': 'Vaccines and biologics'},
            {'code': 'MED_DEV', 'name': 'Medical Device', 'description': 'Medical devices and equipment'},
            {'code': 'SUPP', 'name': 'Medical Supply', 'description': 'Medical supplies and consumables'}
        ]
        for pt_data in product_types:
            pt = ProductType(**pt_data)
            db.session.add(pt)
    
    # AllocationType default data
    if not AllocationType.query.first():
        allocation_types = [
            {'code': 'REG', 'name': 'Regular', 'description': 'Regular allocation', 'requires_customer': False, 'priority_level': 2},
            {'code': 'TENDER', 'name': 'Tender', 'description': 'Tender allocation', 'requires_customer': True, 'priority_level': 1},
            {'code': 'CONSIGN', 'name': 'Consignment', 'description': 'Consignment allocation', 'requires_customer': True, 'priority_level': 2},
            {'code': 'RESERVE', 'name': 'Reserve', 'description': 'Reserved stock', 'requires_customer': False, 'priority_level': 3}
        ]
        for at_data in allocation_types:
            at = AllocationType(**at_data)
            db.session.add(at)
    
    # MovementType default data
    if not MovementType.query.first():
        movement_types = [
            {'code': 'IN_RECEIPT', 'name': 'Receipt', 'direction': 'IN', 'description': 'Stock receipt'},
            {'code': 'OUT_SHIP', 'name': 'Shipment', 'direction': 'OUT', 'description': 'Stock shipment'},
            {'code': 'OUT_CONSIGN', 'name': 'Consignment', 'direction': 'OUT', 'description': 'Consignment shipment'},
            {'code': 'IN_RETURN', 'name': 'Return', 'direction': 'IN', 'description': 'Return from consignment'},
            {'code': 'ADJUST', 'name': 'Adjustment', 'direction': 'TRANSFER', 'description': 'Stock adjustment'}
        ]
        for mt_data in movement_types:
            mt = MovementType(**mt_data)
            db.session.add(mt)

def _init_default_system_config():
    """Initialize default system configuration"""
    if not SystemConfiguration.query.first():
        configs = [
            {'config_key': 'SYSTEM_NAME', 'config_value': 'WMS - Warehouse Management System', 'category': 'SYSTEM'},
            {'config_key': 'DEFAULT_TIMEZONE', 'config_value': 'Asia/Jakarta', 'category': 'SYSTEM'},
            {'config_key': 'PASSWORD_EXPIRY_DAYS', 'config_value': '90', 'config_type': 'INTEGER', 'category': 'SECURITY'},
            {'config_key': 'MAX_LOGIN_ATTEMPTS', 'config_value': '5', 'config_type': 'INTEGER', 'category': 'SECURITY'},
            {'config_key': 'SESSION_TIMEOUT_HOURS', 'config_value': '8', 'config_type': 'INTEGER', 'category': 'SECURITY'},
            {'config_key': 'AUTO_BACKUP_ENABLED', 'config_value': 'true', 'config_type': 'BOOLEAN', 'category': 'SYSTEM'},
            {'config_key': 'EMAIL_NOTIFICATIONS_ENABLED', 'config_value': 'true', 'config_type': 'BOOLEAN', 'category': 'NOTIFICATION'},
            {'config_key': 'DEFAULT_ALLOCATION_TYPE', 'config_value': 'REG', 'category': 'BUSINESS'}
        ]
        for config_data in configs:
            config = SystemConfiguration(**config_data)
            db.session.add(config)

def _init_default_superadmin():
    """Initialize default superadmin user"""
    if not User.query.filter_by(role='superadmin').first():
        superadmin = User(
            username='superadmin',
            email='superadmin@wms.local',
            user_id='SA001',
            first_name='Super',
            last_name='Admin',
            role='superadmin',
            department='SYSTEM',
            is_active=True,
            is_verified=True,
            created_by='SYSTEM'
        )
        superadmin.set_password('superadmin123')  # Change this in production!
        db.session.add(superadmin)

        

# ==================== COMMON QUERIES ====================

class CommonQueries:
    """Common database queries untuk WMS system"""
    
    @staticmethod
    def get_available_stock_by_product(product_id, allocation_type=None):
        """Get available stock untuk product tertentu"""
        query = db.session.query(
            db.func.sum(Allocation.available_stock)
        ).join(Batch).filter(
            Batch.product_id == product_id,
            Allocation.status == 'active'
        )
        
        if allocation_type:
            query = query.join(AllocationType).filter(
                AllocationType.code == allocation_type
            )
        
        return query.scalar() or 0
    
    @staticmethod
    def get_expiring_batches(days=30):
        """Get batches yang akan expire dalam X hari"""
        from datetime import datetime, timedelta
        cutoff_date = datetime.now().date() + timedelta(days=days)
        
        return Batch.query.filter(
            Batch.expiry_date <= cutoff_date
        ).order_by(Batch.expiry_date).all()
    
    @staticmethod
    def get_pending_sales_orders():
        """Get semua pending sales orders"""
        return SalesOrder.query.filter(
            SalesOrder.status.in_(['PENDING', 'CONFIRMED'])
        ).order_by(SalesOrder.so_date.desc()).all()
    
    @staticmethod
    def get_active_picking_orders():
        """Get semua active picking orders"""
        return PickingOrder.query.filter(
            PickingOrder.status.in_(['PENDING', 'IN_PROGRESS'])
        ).order_by(PickingOrder.created_at.desc()).all()
    
    @staticmethod
    def get_customer_allocations(customer_id, allocation_type=None):
        """Get allocations untuk customer tertentu"""
        query = Allocation.query.filter(
            Allocation.customer_id == customer_id,
            Allocation.status == 'active'
        )
        
        if allocation_type:
            query = query.join(AllocationType).filter(
                AllocationType.code == allocation_type
            )
        
        return query.all()
    
    @staticmethod
    def get_consignment_summary(customer_id=None, status=None):
        """Get summary konsinyasi"""
        query = Consignment.query
        
        if customer_id:
            query = query.join(ConsignmentAgreement).filter(
                ConsignmentAgreement.customer_id == customer_id
            )
        
        if status:
            query = query.filter(Consignment.status == status)
        
        return query.all()
    
    @staticmethod
    def get_low_stock_products(threshold=10):
        """Get products dengan stock rendah"""
        return db.session.query(Product).join(Batch).join(Allocation).group_by(
            Product.id
        ).having(
            db.func.sum(Allocation.available_stock) <= threshold
        ).all()
    
    @staticmethod
    def get_user_activity_summary(user_id, days=7):
        """Get summary aktivitas user dalam X hari terakhir"""
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        
        return UserActivity.query.filter(
            UserActivity.user_id == user_id,
            UserActivity.timestamp >= cutoff_date
        ).order_by(UserActivity.timestamp.desc()).all()
    
    @staticmethod
    def get_system_health_check():
        """Get basic system health metrics"""
        return {
            'total_products': Product.query.count(),
            'total_batches': Batch.query.count(),
            'active_allocations': Allocation.query.filter_by(status='active').count(),
            'pending_sales_orders': SalesOrder.query.filter(SalesOrder.status.in_(['PENDING', 'CONFIRMED'])).count(),
            'active_consignments': Consignment.query.filter(Consignment.status.in_(['SHIPPED', 'RECEIVED_BY_CUSTOMER'])).count(),
            'active_users': User.query.filter_by(is_active=True).count(),
            'recent_errors': SystemLog.query.filter_by(level='ERROR').count()
        }

__all__.append('CommonQueries')

# ==================== MODEL RELATIONSHIPS SUMMARY ====================

"""
RELATIONSHIP SUMMARY:
=====================

CUSTOMER RELATIONSHIPS:
Customer (1) -> (N) SalesOrder
Customer (1) -> (N) Allocation (for tender/consignment)
Customer (1) -> (N) Shipment
Customer (1) -> (N) ConsignmentAgreement

PRODUCT & INVENTORY:
Product (1) -> (N) Batch
Batch (1) -> (N) Allocation
Allocation (1) -> (N) Rack
Allocation (1) -> (N) StockMovement
Allocation (1) -> (N) Consignment (for consignment type)

SALES FLOW:
SalesOrder (1) -> (N) SalesOrderItem
SalesOrder (1) -> (N) ShippingPlan
ShippingPlan (1) -> (N) ShippingPlanItem
ShippingPlan (1) -> (N) PickingList
ShippingPlan (1) -> (1) Shipment

PICKING & PACKING FLOW:
PickingList (1) -> (N) PickingListItem
PickingList (1) -> (N) PickingOrder
PickingOrder (1) -> (N) PickingOrderItem
PickingOrder (1) -> (N) PackingOrder
PackingOrder (1) -> (N) PackingBox
PackingBox (1) -> (N) PackingBoxItem

CONSIGNMENT FLOW:
ConsignmentAgreement (1) -> (N) Consignment
Consignment (1) -> (N) ConsignmentItem
Consignment (1) -> (N) ConsignmentSale
Consignment (1) -> (N) ConsignmentReturn
Customer (1) -> (N) ConsignmentStatement

USER & SECURITY:
User (1) -> (N) UserSession
User (1) -> (N) UserActivity
User (1) -> (N) AuditLog

SYSTEM & CONFIGURATION:
All entities -> Helper/Enum tables
All changes -> AuditLog
All notifications -> NotificationLog
System settings -> SystemConfiguration
"""

# ==================== VERSION INFO ====================

__version__ = '3.1.1'
__author__ = 'Kaayeey-sides'
__email__ = 'mamattewahyu@biofarma.co.id'
__status__ = 'development'

def get_version_info():
    """Get detailed version information"""
    return {
        'version': __version__,
        'author': __author__,
        'status': __status__,
        'models_count': len(__all__),
        'domains': [
            'Product & Inventory', 'Warehouse', 'Customer', 'Sales',
            'Picking & Packing', 'Shipping', 'Consignment',
            'User & Security', 'System & Configuration'
        ]
    }

__all__.append('get_version_info')