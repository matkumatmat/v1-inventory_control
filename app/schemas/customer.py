"""
Customer Domain Schemas
=======================

Schemas untuk Customer dan CustomerAddress
"""

from pydantic import BaseModel, model_validator, field_validator
from typing import Optional, List
from decimal import Decimal
from .base import BaseSchema, TimestampMixin, StatusMixin, ERPMixin, AddressMixin, ContactMixin
from .validators import (
    validate_customer_code, validate_phone_number, validate_postal_code
)

class SectorTypeSchema(BaseSchema):
    """Schema untuk SectorType enum"""
    code: str
    name: str
    description: Optional[str] = None
    requires_special_handling: bool = False
    default_payment_terms: Optional[int] = None
    default_delivery_terms: Optional[str] = None
    requires_temperature_monitoring: bool = False
    requires_chain_of_custody: bool = False
    special_documentation: Optional[str] = None
    is_active: bool = True

    @field_validator('code')
    def code_length(cls,v):
        if len(v) > 10:
            raise ValueError("code must be max 10 chars")
        return v
        
    @field_validator('name', 'default_delivery_terms')
    def name_length(cls, v):
        if v and len(v) > 50:
            raise ValueError('name and default_delivery_terms must be max 50 chars')
        return v
    
    @field_validator('default_payment_terms')
    def payment_terms_range(cls, v):
        if v and not 1 <= v <= 365:
            raise ValueError('default_payment_terms must be between 1 and 365')
        return v

class CustomerTypeSchema(BaseSchema):
    """Schema untuk CustomerType enum"""
    code: str
    name: str
    description: Optional[str] = None
    allows_tender_allocation: bool = False
    requires_pre_approval: bool = False
    default_credit_limit: Optional[Decimal] = None
    default_discount_percent: Optional[Decimal] = None
    default_payment_terms_days: int = 30
    is_active: bool = True

    @field_validator('code')
    def code_length(cls, v):
        if len(v) > 10:
            raise ValueError('code must be at most 10 characters')
        return v

    @field_validator('name')
    def name_length(cls, v):
        if len(v) > 50:
            raise ValueError('name must be at most 50 characters')
        return v

    @field_validator('default_credit_limit')
    def credit_limit_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError('default_credit_limit must be non-negative')
        return v

    @field_validator('default_discount_percent')
    def discount_percent_range(cls, v):
        if v is not None and not 0 <= v <= 100:
            raise ValueError('default_discount_percent must be between 0 and 100')
        return v

    @field_validator('default_payment_terms_days')
    def payment_terms_range(cls, v):
        if not 1 <= v <= 365:
            raise ValueError('default_payment_terms_days must be between 1 and 365')
        return v
        
class CustomerAddressSchema(BaseSchema, TimestampMixin, AddressMixin, ContactMixin):
    """Schema untuk CustomerAddress model"""
    customer_id: int
    
    address_name: str
    address_type: str = 'DELIVERY'
    
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    
    delivery_instructions: Optional[str] = None
    special_requirements: Optional[str] = None
    
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    
    is_default: bool = False
    is_active: bool = True

    @field_validator('contact_phone')
    def validate_phone_field(cls, v):
        return validate_phone_number(v)

    @field_validator('customer_id')
    def customer_id_positive(cls, v):
        if v < 1:
            raise ValueError('customer_id must be positive')
        return v
        
    @field_validator('address_name', 'contact_person')
    def name_length(cls, v):
        if v and len(v) > 100:
            raise ValueError('name fields must be at most 100 characters')
        if v and len(v) < 2:
            raise ValueError('address_name must be at least 2 characters')
        return v

    @field_validator('address_type')
    def address_type_valid(cls, v):
        if v not in ['BILLING', 'DELIVERY', 'WAREHOUSE', 'OFFICE']:
            raise ValueError('Invalid address_type')
        return v

    @field_validator('latitude')
    def latitude_range(cls, v):
        if v is not None and not -90 <= v <= 90:
            raise ValueError('latitude must be between -90 and 90')
        return v

    @field_validator('longitude')
    def longitude_range(cls, v):
        if v is not None and not -180 <= v <= 180:
            raise ValueError('longitude must be between -180 and 180')
        return v

class CustomerSchema(BaseSchema, TimestampMixin, StatusMixin, ERPMixin, AddressMixin, ContactMixin):
    """Schema untuk Customer model"""
    customer_code: str
    name: str
    legal_name: Optional[str] = None
    
    customer_type_id: int
    sector_type_id: int
    
    fax: Optional[str] = None
    website: Optional[str] = None
    
    tax_id: Optional[str] = None
    business_license: Optional[str] = None
    industry: Optional[str] = None
    
    credit_limit: Optional[Decimal] = None
    payment_terms_days: int = 30
    currency: str = 'IDR'
    
    is_tender_eligible: bool = False
    requires_approval: bool = False
    
    default_delivery_method: Optional[str] = None
    special_delivery_instructions: Optional[str] = None
    
    erp_customer_id: Optional[str] = None
    
    customer_type: Optional[CustomerTypeSchema] = None
    sector_type: Optional[SectorTypeSchema] = None
    addresses: List[CustomerAddressSchema] = []
    default_address: Optional[CustomerAddressSchema] = None
    delivery_addresses: List[CustomerAddressSchema] = []

    @field_validator('customer_code')
    def validate_customer_code_field(cls, v):
        return validate_customer_code(v)

    @field_validator('name', 'industry')
    def name_length(cls,v):
        if v and len(v) > 100:
            raise ValueError("name and industry must be at most 100 chars")
        if v and len(v) < 2:
            raise ValueError("name must be at least 2 chars")
        return v

    @field_validator('legal_name')
    def legal_name_length(cls, v):
        if v and len(v) > 150:
            raise ValueError('legal_name must be at most 150 characters')
        return v

    @field_validator('customer_type_id', 'sector_type_id')
    def id_fields_positive(cls, v):
        if v < 1:
            raise ValueError('ID fields must be positive')
        return v

    @field_validator('fax')
    def fax_length(cls, v):
        if v and len(v) > 20:
            raise ValueError('fax must be at most 20 characters')
        return v

    @field_validator('tax_id', 'business_license', 'default_delivery_method', 'erp_customer_id')
    def string_fields_50(cls, v):
        if v and len(v) > 50:
            raise ValueError('field must be at most 50 characters')
        return v

    @field_validator('credit_limit')
    def credit_limit_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError('credit_limit must be non-negative')
        return v

    @field_validator('payment_terms_days')
    def payment_terms_range(cls, v):
        if not 1 <= v <= 365:
            raise ValueError('payment_terms_days must be between 1 and 365')
        return v

    @field_validator('currency')
    def currency_length(cls, v):
        if len(v) > 3:
            raise ValueError('currency must be at most 3 characters')
        return v

# Input schemas
class CustomerCreateSchema(CustomerSchema):
    class Config:
        exclude = {'id', 'public_id', 'created_date', 'created_by', 'last_modified_date', 
                  'last_modified_by', 'erp_sync_date', 'addresses', 'default_address', 'delivery_addresses'}

class CustomerUpdateSchema(CustomerSchema):
    customer_code: Optional[str]
    name: Optional[str]
    customer_type_id: Optional[int]
    sector_type_id: Optional[int]
    
    class Config:
        exclude = ('id', 'public_id', 'created_date', 'created_by', 'last_modified_date',
                  'last_modified_by', 'erp_sync_date', 'addresses', 'default_address', 'delivery_addresses')

class CustomerAddressCreateSchema(CustomerAddressSchema):
    class Config:
        exclude = ('id', 'public_id', 'created_date', 'created_by')

class CustomerAddressUpdateSchema(CustomerAddressSchema):
    customer_id: Optional[int]
    address_name: Optional[str]
    
    class Config:
        exclude = ('id', 'public_id', 'created_date', 'created_by')