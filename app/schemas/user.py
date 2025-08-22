"""
User Domain Schemas
===================

Schemas untuk User, UserSession, UserActivity, dan Authentication
"""

from pydantic import BaseModel, model_validator, field_validator
from typing import Optional
from datetime import datetime
import re
from .base import BaseSchema, TimestampMixin
from .validators import validate_phone_number

class UserSchema(BaseSchema, TimestampMixin):
    """Schema untuk User model"""
    username: str
    email: str
    password_hash: Optional[str]
    
    user_id: str
    first_name: str
    last_name: str
    full_name: Optional[str]
    
    phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    
    role: str = 'admin'
    department: Optional[str] = None
    position: Optional[str] = None
    
    is_active: bool = True
    is_verified: bool = False
    is_locked: bool = False
    
    password_expires_at: Optional[datetime] = None
    must_change_password: bool = True
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    
    last_login: Optional[datetime] = None
    last_login_ip: Optional[str] = None
    current_session_id: Optional[str] = None
    session_expires_at: Optional[datetime] = None
    
    timezone: str = 'Asia/Jakarta'
    language: str = 'id'
    date_format: str = 'DD/MM/YYYY'
    
    assigned_warehouse_id: Optional[int] = None
    
    can_login: Optional[bool] = None
    is_session_valid: Optional[bool] = None
    days_until_password_expires: Optional[int] = None

    @field_validator('phone')
    def validate_phone_field(cls, v):
        return validate_phone_number(v)
    
    @field_validator('username')
    def username_length(cls,v):
        if not 3 <= len(v) <= 50:
            raise ValueError('username must be between 3 and 50 characters')
        return v
    
    @field_validator('user_id')
    def user_id_length(cls,v):
        if not 2 <= len(v) <= 20:
            raise ValueError('user id must be between 2 and 20 characters')
        return v
    
    @field_validator('first_name', 'last_name', 'position', 'timezone')
    def name_fields_length(cls,v):
        if v and not 1 <= len(v) <= 50:
            raise ValueError('name fields must be between 1 and 50 characters')
        return v
        
    @field_validator('emergency_contact')
    def emergency_contact_length(cls,v):
        if v and len(v) > 100:
            raise ValueError("emergency contact must be at most 100 chars")
        return v
        
    @field_validator('role')
    def role_valid(cls,v):
        if v not in ['superadmin', 'admin']:
            raise ValueError("invalid role")
        return v
        
    @field_validator('department')
    def department_valid(cls,v):
        if v and v not in ['WAREHOUSE', 'SALES', 'ADMIN', 'FINANCE']:
            raise ValueError("invalid department")
        return v
        
    @field_validator('failed_login_attempts')
    def failed_login_range(cls,v):
        if not 0 <= v <= 10:
            raise ValueError('failed login attempts must be between 0 and 10')
        return v
        
    @field_validator('language')
    def language_valid(cls,v):
        if v not in ['id', 'en']:
            raise ValueError("invalid language")
        return v

    @field_validator('date_format')
    def date_format_length(cls,v):
        if len(v) > 20:
            raise ValueError("date format must be max 20 chars")
        return v

    @field_validator('assigned_warehouse_id')
    def warehouse_id_positive(cls,v):
        if v is not None and v < 1:
            raise ValueError('warehouse id must be positive')
        return v

class UserCreateSchema(BaseModel):
    """Schema untuk create user"""
    username: str
    email: str
    password: str
    confirm_password: str
    
    user_id: str
    first_name: str
    last_name: str
    
    phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    
    role: str = 'admin'
    department: Optional[str] = None
    position: Optional[str] = None
    
    timezone: str = 'Asia/Jakarta'
    language: str = 'id'
    
    assigned_warehouse_id: Optional[int] = None
    
    @field_validator('phone')
    def validate_phone_field(cls, v):
        return validate_phone_number(v)

    @model_validator(mode='after')
    def validate_passwords_match(cls, values):
        """Validate password confirmation"""
        password, confirm_password = values.get('password'), values.get('confirm_password')
        if password != confirm_password:
            raise ValueError('Passwords do not match')
        return values
    
    @field_validator('password')
    def validate_password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>\?]', v):
            raise ValueError('Password must contain at least one special character')
        return v

class UserUpdateSchema(BaseModel):
    """Schema untuk update user"""
    email: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    
    phone: Optional[str]
    emergency_contact: Optional[str]
    
    role: Optional[str]
    department: Optional[str]
    position: Optional[str]
    
    is_active: Optional[bool]
    is_verified: Optional[bool]
    is_locked: Optional[bool]
    
    timezone: Optional[str]
    language: Optional[str]
    date_format: Optional[str]
    
    assigned_warehouse_id: Optional[int]

class PasswordChangeSchema(BaseModel):
    """Schema untuk change password"""
    current_password: str
    new_password: str
    confirm_password: str
    
    @model_validator(mode='after')
    def validate_passwords_match(cls, values):
        """Validate password confirmation"""
        new_password, confirm_password = values.get('new_password'), values.get('confirm_password')
        if new_password != confirm_password:
            raise ValueError('Passwords do not match')
        return values
    
    @field_validator('new_password')
    def validate_password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>\?]', v):
            raise ValueError('Password must contain at least one special character')
        return v

class LoginSchema(BaseModel):
    """Schema untuk login"""
    username: str
    password: str
    remember_me: bool = False

class UserSessionSchema(BaseModel):
    """Schema untuk UserSession model"""
    session_id: str
    user_id: int
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    is_active: bool = True
    logout_reason: Optional[str]
    
    user: Optional[UserSchema]
    
    @field_validator('user_agent')
    def user_agent_length(cls,v):
        if v and len(v) > 255:
            raise ValueError("user agent must be at most 255 characters")
        return v
    
    @field_validator('logout_reason')
    def logout_reason_valid(cls,v):
        if v and v not in ['MANUAL', 'TIMEOUT', 'FORCED', 'SECURITY']:
            raise ValueError("invalid logout reason")
        return v

class UserActivitySchema(BaseModel):
    """Schema untuk UserActivity model"""
    user_id: int
    activity_type: str
    entity_type: Optional[str]
    entity_id: Optional[int]
    description: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    additional_data: Optional[dict]
    timestamp: datetime
    
    user: Optional[UserSchema]

# Response schemas
class LoginResponseSchema(BaseModel):
    """Schema untuk login response"""
    access_token: str
    refresh_token: str
    token_type: str = 'Bearer'
    expires_in: int
    user: UserSchema

class RefreshTokenSchema(BaseModel):
    """Schema untuk refresh token"""
    refresh_token: str

class UserProfileSchema(UserSchema):
    """Schema untuk user profile (limited fields)"""
    class Config:
        exclude = ('password_hash', 'failed_login_attempts', 'locked_until', 'current_session_id',
                  'is_locked', 'must_change_password', 'password_expires_at')