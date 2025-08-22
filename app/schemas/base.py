"""
Base Pydantic Schemas
========================

Provides base classes and common functionality for all schemas using Pydantic V2.
"""

from pydantic import BaseModel, ConfigDict, field_validator, model_validator, EmailStr, Field
from datetime import datetime, date
from typing import Optional, Any
import uuid

class BaseSchema(BaseModel):
    """Base schema dengan common fields dan methods, versi Pydantic V2."""
    
    id: Optional[int] = None
    public_id: Optional[uuid.UUID] = None
    created_date: Optional[datetime] = None
    created_by: Optional[str] = None

    # class Config diganti jadi model_config
    # orm_mode diganti jadi from_attributes
    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore',
        json_encoders={
            datetime: lambda v: v.strftime('%Y-%m-%dT%H:%M:%S'),
            date: lambda v: v.strftime('%Y-%m-%d')
        }
    )
        
    # @validator('*', pre=True) diganti jadi @model_validator(mode='before')
    @model_validator(mode='before')
    @classmethod
    def strip_whitespace(cls, data: Any) -> Any:
        """Strip whitespace dari string fields sebelum validasi."""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    data[key] = value.strip()
        return data

    # @validator diganti jadi @field_validator
    @field_validator('created_date')
    @classmethod
    def validate_created_date(cls, v: datetime) -> datetime:
        """Validate created_date tidak boleh future."""
        if v and v > datetime.utcnow():
            raise ValueError('Created date cannot be in the future')
        return v

class PaginationSchema(BaseModel):
    """Schema untuk pagination response, versi Pydantic V2."""
    page: int = Field(gt=0, description="Page must be at least 1")
    per_page: int = Field(gt=0, le=100, description="Per page must be between 1 and 100")
    pages: int
    total: int
    has_next: bool
    has_prev: bool

class TimestampMixin(BaseModel):
    """Mixin untuk timestamp fields."""
    created_date: Optional[datetime] = None
    last_modified_date: Optional[datetime] = None
    created_by: Optional[str] = None
    last_modified_by: Optional[str] = None

class StatusMixin(BaseModel):
    """Mixin untuk status fields."""
    status: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None

class ERPMixin(BaseModel):
    """Mixin untuk ERP integration fields."""
    erp_sync_date: Optional[datetime] = None

class AddressMixin(BaseModel):
    """Mixin untuk address fields."""
    address_line1: Optional[str] = Field(None, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=50)
    state_province: Optional[str] = Field(None, max_length=50)
    postal_code: Optional[str] = Field(None, max_length=10)
    country: str = Field('Indonesia', max_length=50)

class ContactMixin(BaseModel):
    """Mixin untuk contact fields."""
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None # Gunakan tipe EmailStr untuk validasi email otomatis