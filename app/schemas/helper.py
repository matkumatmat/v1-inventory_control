"""
Helper Domain Schemas
=====================

Schemas untuk semua enum dan helper models
"""

from pydantic import BaseModel, model_validator, field_validator
from typing import Optional, List, Any
from datetime import datetime, date
import uuid
from .base import BaseSchema, PaginationSchema

# Base schema untuk enum types
class BaseEnumSchema(BaseSchema):
    """Base schema untuk semua enum types"""
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0

# System Configuration
class SystemConfigurationSchema(BaseSchema):
    """Schema untuk SystemConfiguration model"""
    config_key: str
    config_value: Optional[str]
    config_type: str = 'STRING'
    category: Optional[str]
    description: Optional[str]
    is_sensitive: bool = False
    validation_rule: Optional[str]
    default_value: Optional[str]
    is_user_editable: bool = True
    required_role: str = 'admin'
    last_modified_by: Optional[str]
    last_modified_date: Optional[datetime]

# Notification Types
class NotificationTypeSchema(BaseSchema):
    """Schema untuk NotificationType model"""
    code: str
    name: str
    description: Optional[str]
    is_email_enabled: bool = True
    is_sms_enabled: bool = False
    is_push_enabled: bool = True
    is_system_notification: bool = True
    email_template: Optional[str]
    sms_template: Optional[str]
    push_template: Optional[str]
    retry_count: int = 3
    retry_interval_minutes: int = 5
    is_active: bool = True

class NotificationLogSchema(BaseSchema):
    """Schema untuk NotificationLog model"""
    notification_type_id: int
    recipient_type: str
    recipient_id: Optional[int]
    recipient_email: Optional[str]
    recipient_phone: Optional[str]
    subject: Optional[str]
    message_body: Optional[str]
    delivery_method: str
    delivery_status: str = 'PENDING'
    delivery_attempts: int = 0
    entity_type: Optional[str]
    entity_id: Optional[int]
    external_message_id: Optional[str]
    external_response: Optional[Any]  # JSON
    created_at: Optional[datetime]
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    failed_at: Optional[datetime]
    error_message: Optional[str]
    error_code: Optional[str]

# Audit Logs
class AuditLogSchema(BaseSchema):
    """Schema untuk AuditLog model"""
    entity_type: str
    entity_id: int
    action: str
    user_id: Optional[int]
    username: Optional[str]
    old_values: Optional[Any]  # JSON
    new_values: Optional[Any]  # JSON
    changed_fields: Optional[Any]  # JSON
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_id: Optional[uuid.UUID]
    notes: Optional[str]
    severity: str = 'INFO'
    timestamp: Optional[datetime]

class SystemLogSchema(BaseSchema):
    """Schema untuk SystemLog model"""
    level: str
    logger_name: Optional[str]
    message: str
    module: Optional[str]
    function: Optional[str]
    line_number: Optional[int]
    exception_type: Optional[str]
    exception_message: Optional[str]
    stack_trace: Optional[str]
    request_id: Optional[uuid.UUID]
    user_id: Optional[int]
    ip_address: Optional[str]
    extra_data: Optional[Any]  # JSON
    timestamp: Optional[datetime]

# API Response schemas
class ErrorResponseSchema(BaseModel):
    """Schema untuk error responses"""
    error: bool = True
    message: str
    error_code: Optional[str]
    details: Optional[Any]
    timestamp: datetime = datetime.now()
    request_id: Optional[uuid.UUID]

class SuccessResponseSchema(BaseModel):
    """Schema untuk success responses"""
    success: bool = True
    message: Optional[str]
    data: Optional[Any]
    timestamp: datetime = datetime.now()
    request_id: Optional[uuid.UUID]

class PaginatedResponseSchema(BaseModel):
    """Schema untuk paginated responses"""
    success: bool = True
    data: List[Any]
    pagination: PaginationSchema
    message: Optional[str]
    timestamp: datetime = datetime.now()
    request_id: Optional[uuid.UUID]

# Search and Filter schemas
class SearchSchema(BaseModel):
    """Schema untuk search parameters"""
    q: Optional[str]
    page: int = 1
    per_page: int = 20
    sort_by: Optional[str]
    sort_order: str = 'asc'

    @field_validator('sort_order')
    def sort_order_valid(cls, v):
        if v.lower() not in ['asc', 'desc']:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        return v.lower()

class DateRangeSchema(BaseModel):
    """Schema untuk date range filters"""
    start_date: Optional[date]
    end_date: Optional[date]
    
    @model_validator(mode='after')
    def validate_date_range(cls, values):
        start_date, end_date = values.get('start_date'), values.get('end_date')
        if start_date and end_date and start_date > end_date:
            raise ValueError('Start date must be before end date')
        return values

# Input schemas for enum types
class BaseEnumCreateSchema(BaseEnumSchema):
    class Config:
        exclude = ('id', 'created_date')

class BaseEnumUpdateSchema(BaseEnumSchema):
    code: Optional[str]
    name: Optional[str]
    
    class Config:
        exclude = ('id', 'created_date')

class SystemConfigurationCreateSchema(SystemConfigurationSchema):
    class Config:
        exclude = ('id', 'last_modified_by', 'last_modified_date')

class SystemConfigurationUpdateSchema(SystemConfigurationSchema):
    config_key: Optional[str]
    
    class Config:
        exclude = ('id', 'last_modified_by', 'last_modified_date')

class NotificationTypeCreateSchema(NotificationTypeSchema):
    class Config:
        exclude = ('id', 'created_date')

class NotificationTypeUpdateSchema(NotificationTypeSchema):
    code: Optional[str]
    name: Optional[str]
    
    class Config:
        exclude = ('id', 'created_date')

class NotificationLogCreateSchema(NotificationLogSchema):
    class Config:
        exclude = ('id', 'created_at', 'sent_at', 'delivered_at', 'failed_at')

class AuditLogCreateSchema(AuditLogSchema):
    class Config:
        exclude = ('id', 'timestamp')

class SystemLogCreateSchema(SystemLogSchema):
    class Config:
        exclude = ('id', 'timestamp')