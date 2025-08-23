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

from .base import BaseModel
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Text, DateTime, Date, Numeric, Boolean,
    Float, func, JSON
)
from sqlalchemy.orm import relationship

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

# ==================== INTEGRATION DOMAIN ====================

from .integration import (
    ERPSyncLog,
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
    
    # Event information
    entity_type = Column(String(50), nullable=False, index=True)  # SalesOrder, Product, etc
    entity_id = Column(Integer, nullable=False, index=True)
    action = Column(String(20), nullable=False, index=True)  # CREATE, UPDATE, DELETE, VIEW
    
    # User information
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    user = relationship('User')
    username = Column(String(50))  # Backup jika user dihapus
    
    # Change details
    old_values = Column(JSON)  # JSON field untuk old values
    new_values = Column(JSON)  # JSON field untuk new values
    changed_fields = Column(JSON)  # Array field names yang berubah
    
    # Context information
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    request_id = Column(String(36))  # UUID untuk trace request
    
    # Additional context
    notes = Column(Text)
    severity = Column(String(10), default='INFO')  # DEBUG, INFO, WARN, ERROR
    
    # Timestamp
    timestamp = Column(DateTime, default=func.current_timestamp(), index=True)
    
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
    
    # Log information
    level = Column(String(10), nullable=False, index=True)  # DEBUG, INFO, WARN, ERROR, FATAL
    logger_name = Column(String(100), index=True)
    message = Column(Text, nullable=False)
    
    # Context
    module = Column(String(50))
    function = Column(String(50))
    line_number = Column(Integer)
    
    # Exception details (jika error)
    exception_type = Column(String(100))
    exception_message = Column(Text)
    stack_trace = Column(Text)
    
    # Request context
    request_id = Column(String(36))
    user_id = Column(Integer)
    ip_address = Column(String(45))
    
    # Additional data
    extra_data = Column(JSON)
    
    # Timestamp
    timestamp = Column(DateTime, default=func.current_timestamp(), index=True)
    
    def __repr__(self):
        return f'<SystemLog {self.level}: {self.message[:50]}...>'

class NotificationLog(BaseModel):
    """Model untuk tracking notifikasi yang dikirim"""
    __tablename__ = 'notification_logs'
    
    # Notification details
    notification_type_id = Column(Integer, ForeignKey('notification_types.id'), nullable=False)
    notification_type = relationship('NotificationType')
    
    # Recipient
    recipient_type = Column(String(20), nullable=False)  # USER, CUSTOMER, EXTERNAL
    recipient_id = Column(Integer)  # User ID atau Customer ID
    recipient_email = Column(String(100))
    recipient_phone = Column(String(20))
    
    # Message content
    subject = Column(String(200))
    message_body = Column(Text)
    
    # Delivery details
    delivery_method = Column(String(20), nullable=False)  # EMAIL, SMS, PUSH, SYSTEM
    delivery_status = Column(String(20), default='PENDING')  # PENDING, SENT, DELIVERED, FAILED
    delivery_attempts = Column(Integer, default=0)
    
    # Context
    entity_type = Column(String(50))  # SalesOrder, Shipment, etc
    entity_id = Column(Integer)
    
    # External provider details
    external_message_id = Column(String(100))  # ID dari provider (SendGrid, Twilio, etc)
    external_response = Column(JSON)
    
    # Timing
    created_at = Column(DateTime, default=func.current_timestamp())
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    failed_at = Column(DateTime)
    
    # Error details (jika gagal)
    error_message = Column(Text)
    error_code = Column(String(50))
    
    def __repr__(self):
        return f'<NotificationLog {self.notification_type.code if self.notification_type else "Unknown"} - {self.delivery_status}>'

# ==================== CONFIGURATION & SETTINGS ====================

class SystemConfiguration(BaseModel):
    """Model untuk system configuration dan settings"""
    __tablename__ = 'system_configurations'
    
    # Configuration key and value
    config_key = Column(String(100), unique=True, nullable=False, index=True)
    config_value = Column(Text)
    config_type = Column(String(20), default='STRING')  # STRING, INTEGER, FLOAT, BOOLEAN, JSON
    
    # Metadata
    category = Column(String(50), index=True)  # SYSTEM, NOTIFICATION, BUSINESS, SECURITY
    description = Column(Text)
    is_sensitive = Column(Boolean, default=False)  # Untuk password, API keys, etc
    
    # Validation
    validation_rule = Column(Text)  # Regex atau rule untuk validasi
    default_value = Column(Text)
    
    # Access control
    is_user_editable = Column(Boolean, default=True)
    required_role = Column(String(20), default='admin')  # Role minimum untuk edit
    
    # Tracking
    last_modified_by = Column(String(50))
    last_modified_date = Column(DateTime, default=func.current_timestamp())
    
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
    'BaseModel',
    
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

    # Integration domain
    'ERPSyncLog',
    
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
