from app.models.base import BaseModel, db
from sqlalchemy.dialects.postgresql import UUID
import uuid
import bcrypt
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

class User(BaseModel):
    """Enhanced User model dengan proper security dan role management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    
    # Authentication credentials
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # User information
    user_id = db.Column(db.String(20), unique=True, nullable=False, index=True)  # Employee ID
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    full_name = db.Column(db.String(100))
    
    # Contact information
    phone = db.Column(db.String(20))
    emergency_contact = db.Column(db.String(100))
    
    # Role and permissions
    role = db.Column(db.String(20), nullable=False, default='admin')  # superadmin, admin
    department = db.Column(db.String(50))  # WAREHOUSE, SALES, ADMIN, FINANCE
    position = db.Column(db.String(50))
    
    # Access control
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=False)
    
    # Password policy
    password_expires_at = db.Column(db.DateTime)
    must_change_password = db.Column(db.Boolean, default=True)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    
    # Session tracking
    last_login = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(45))
    current_session_id = db.Column(db.String(64))
    session_expires_at = db.Column(db.DateTime)
    
    # Settings and preferences
    timezone = db.Column(db.String(50), default='Asia/Jakarta')
    language = db.Column(db.String(5), default='id')
    date_format = db.Column(db.String(20), default='DD/MM/YYYY')
    
    # Warehouse access (untuk admin yang terbatas pada warehouse tertentu)
    assigned_warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=True)
    assigned_warehouse = db.relationship('Warehouse')
    
    # Creation and modification tracking
    created_by = db.Column(db.String(50))
    created_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_modified_by = db.Column(db.String(50))
    last_modified_date = db.Column(db.DateTime, onupdate=db.func.current_timestamp())
    
    # Relationships
    audit_logs = db.relationship('AuditLog', back_populates='user')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.first_name and self.last_name:
            self.full_name = f"{self.first_name} {self.last_name}"
    
    def set_password(self, password):
        """Set password dengan proper hashing"""
        self.password_hash = generate_password_hash(password)
        self.password_expires_at = datetime.utcnow() + timedelta(days=90)  # 90 days expiry
        self.must_change_password = False
        
    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.password_hash, password)
    
    def is_password_expired(self):
        """Check if password is expired"""
        if not self.password_expires_at:
            return True
        return datetime.utcnow() > self.password_expires_at
    
    def lock_account(self, reason="Multiple failed login attempts"):
        """Lock user account"""
        self.is_locked = True
        self.locked_until = datetime.utcnow() + timedelta(hours=1)  # Lock for 1 hour
        
    def unlock_account(self):
        """Unlock user account"""
        self.is_locked = False
        self.locked_until = None
        self.failed_login_attempts = 0
        
    def is_account_locked(self):
        """Check if account is currently locked"""
        if not self.is_locked:
            return False
        if self.locked_until and datetime.utcnow() > self.locked_until:
            self.unlock_account()
            return False
        return True
    
    def record_login(self, ip_address, session_id):
        """Record successful login"""
        self.last_login = datetime.utcnow()
        self.last_login_ip = ip_address
        self.current_session_id = session_id
        self.session_expires_at = datetime.utcnow() + timedelta(hours=8)  # 8 hour session
        self.failed_login_attempts = 0
        
    def record_failed_login(self):
        """Record failed login attempt"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:  # Lock after 5 failed attempts
            self.lock_account()
    
    def has_permission(self, permission):
        """Check if user has specific permission"""
        return UserRole.has_permission(self.role, permission)
    
    def can_access_warehouse(self, warehouse_id):
        """Check if user can access specific warehouse"""
        if self.role == 'superadmin':
            return True
        if self.assigned_warehouse_id:
            return self.assigned_warehouse_id == warehouse_id
        return True  # Admin dapat akses semua warehouse secara default
    
    def can_manage_user(self, target_user):
        """Check if user can manage another user"""
        if self.role == 'superadmin':
            return True
        if self.role == 'admin' and target_user.role == 'admin':
            return False  # Admin tidak bisa manage admin lain
        return False
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'public_id': str(self.public_id),
            'username': self.username,
            'email': self.email,
            'user_id': self.user_id,
            'full_name': self.full_name,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role,
            'department': self.department,
            'position': self.position,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'assigned_warehouse': self.assigned_warehouse.name if self.assigned_warehouse else None
        }
        
        if include_sensitive:
            data.update({
                'is_locked': self.is_locked,
                'failed_login_attempts': self.failed_login_attempts,
                'password_expires_at': self.password_expires_at.isoformat() if self.password_expires_at else None,
                'must_change_password': self.must_change_password
            })
        
        return data
    
    def __repr__(self):
        return f'<User {self.username}: {self.full_name} ({self.role})>'

class UserRole:
    """Helper class untuk role management dan permissions"""
    
    # Role definitions
    SUPERADMIN = 'superadmin'
    ADMIN = 'admin'
    
    # Permission definitions
    PERMISSIONS = {
        'superadmin': [
            # User Management
            'user.create', 'user.read', 'user.update', 'user.delete',
            'user.manage_roles', 'user.reset_password',
            
            # System Management
            'system.configure', 'system.backup', 'system.logs',
            
            # All business operations
            'product.manage', 'batch.manage', 'allocation.manage',
            'sales_order.manage', 'shipping_plan.manage',
            'picking.manage', 'packing.manage', 'shipment.manage',
            'consignment.manage', 'customer.manage',
            'warehouse.manage', 'inventory.manage',
            
            # Reports and Analytics
            'report.all', 'analytics.all', 'export.all'
        ],
        
        'admin': [
            # Basic user operations (tidak bisa manage superadmin)
            'user.read', 'user.update_self',
            
            # Business operations
            'product.read', 'product.create', 'product.update',
            'batch.read', 'batch.create', 'batch.update',
            'allocation.read', 'allocation.create', 'allocation.update',
            
            'sales_order.read', 'sales_order.create', 'sales_order.update',
            'shipping_plan.read', 'shipping_plan.create', 'shipping_plan.update',
            
            'picking.read', 'picking.create', 'picking.execute',
            'packing.read', 'packing.create', 'packing.execute',
            'shipment.read', 'shipment.create', 'shipment.update',
            
            'consignment.read', 'consignment.create', 'consignment.update',
            'customer.read', 'customer.create', 'customer.update',
            
            'warehouse.read', 'inventory.read', 'inventory.update',
            
            # Standard reports
            'report.standard', 'export.standard'
        ]
    }
    
    @classmethod
    def get_all_roles(cls):
        """Get all available roles"""
        return [cls.SUPERADMIN, cls.ADMIN]
    
    @classmethod
    def has_permission(cls, role, permission):
        """Check if role has specific permission"""
        return permission in cls.PERMISSIONS.get(role, [])
    
    @classmethod
    def get_role_permissions(cls, role):
        """Get all permissions for a role"""
        return cls.PERMISSIONS.get(role, [])

class UserSession(BaseModel):
    """Model untuk tracking user sessions"""
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    
    # User reference
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User')
    
    # Session details
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    
    # Timing
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_activity = db.Column(db.DateTime, default=db.func.current_timestamp())
    expires_at = db.Column(db.DateTime, nullable=False)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    logout_reason = db.Column(db.String(50))  # MANUAL, TIMEOUT, FORCED, SECURITY
    
    def is_expired(self):
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at
    
    def extend_session(self, hours=8):
        """Extend session expiry"""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        self.last_activity = datetime.utcnow()
    
    def terminate(self, reason='MANUAL'):
        """Terminate session"""
        self.is_active = False
        self.logout_reason = reason
    
    def __repr__(self):
        return f'<UserSession {self.session_id[:8]}... - {self.user.username}>'

class UserActivity(BaseModel):
    """Model untuk tracking user activities"""
    __tablename__ = 'user_activities'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # User reference
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User')
    
    # Activity details
    activity_type = db.Column(db.String(50), nullable=False, index=True)  # LOGIN, LOGOUT, CREATE, UPDATE, DELETE, VIEW
    entity_type = db.Column(db.String(50), index=True)  # SalesOrder, Product, etc.
    entity_id = db.Column(db.Integer)
    
    # Context
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    
    # Additional data
    additional_data = db.Column(db.JSON)
    
    # Timing
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp(), index=True)
    
    def __repr__(self):
        return f'<UserActivity {self.user.username}: {self.activity_type}>'