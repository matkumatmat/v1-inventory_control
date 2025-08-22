from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from .base import BaseSchema, TimestampMixin, AddressMixin, ContactMixin
from .validators import validate_phone_number

# Enum Schemas
class DeliveryMethodSchema(BaseSchema):
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool = True
    
    @field_validator('code')
    def code_length(cls,v):
        if len(v) > 10:
            raise ValueError("code must be at most 10 chars")
        return v
        
    @field_validator('name')
    def name_length(cls, v):
        if len(v) > 50:
            raise ValueError('name must be at most 50 characters')
        return v

class CarrierTypeSchema(BaseSchema):
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool = True
    
    @field_validator('code')
    def code_length(cls,v):
        if len(v) > 10:
            raise ValueError("code must be at most 10 chars")
        return v
        
    @field_validator('name')
    def name_length(cls, v):
        if len(v) > 50:
            raise ValueError('name must be at most 50 characters')
        return v

class DocumentTypeSchema(BaseSchema):
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool = True

    @field_validator('code')
    def code_length(cls,v):
        if len(v) > 10:
            raise ValueError("code must be at most 10 chars")
        return v
        
    @field_validator('name')
    def name_length(cls, v):
        if len(v) > 50:
            raise ValueError('name must be at most 50 characters')
        return v

# Main Schemas
class CarrierSchema(BaseSchema, TimestampMixin, AddressMixin, ContactMixin):
    carrier_code: str
    name: str
    carrier_type_id: int
    is_active: bool = True

    @field_validator('carrier_code')
    def code_length(cls,v):
        if not 2 <= len(v) <= 20:
            raise ValueError('carrier code must be between 2 and 20 chars')
        return v

    @field_validator('name')
    def name_length(cls,v):
        if not 2 <= len(v) <= 100:
            raise ValueError('name must be between 2 and 100 chars')
        return v
    
    @field_validator('carrier_type_id')
    def id_positive(cls,v):
        if v < 1:
            raise ValueError('carrier_type_id must be a positive number')
        return v

class ShipmentSchema(BaseSchema, TimestampMixin):
    shipment_number: Optional[str]
    shipment_date: date
    packing_slip_id: int
    customer_id: int
    #... other fields

class ShipmentDocumentSchema(BaseSchema, TimestampMixin):
    shipment_id: int
    document_type_id: int
    document_name: str
    document_url: str
    #... other fields

class ShipmentTrackingSchema(BaseSchema):
    """Schema untuk ShipmentTracking model"""
    shipment_id: int
    
    tracking_date: datetime
    status: str
    location: Optional[str] = None
    description: Optional[str] = None
    
    source: str = 'MANUAL'
    external_reference: Optional[str] = None
    
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    
    carrier_status: Optional[str] = None
    carrier_description: Optional[str] = None
    estimated_delivery: Optional[datetime] = None
    
    notes: Optional[str] = None
    
    created_by: Optional[str] = None
    created_date: Optional[datetime] = None

    @field_validator('shipment_id')
    def shipment_id_positive(cls,v):
        if v < 1:
            raise ValueError("shipment id must be a positive number")
        return v

    @field_validator('status', 'created_by')
    def string_fields_50(cls,v):
        if v and len(v) > 50:
            raise ValueError("field must be at most 50 characters")
        return v

    @field_validator('location')
    def location_length(cls,v):
        if v and len(v) > 200:
            raise ValueError("location must be at most 200 characters")
        return v

    @field_validator('source')
    def source_valid(cls, v):
        if v not in ['MANUAL', 'CARRIER_API', 'SYSTEM']:
            raise ValueError('Invalid source')
        return v

    @field_validator('external_reference', 'carrier_status')
    def string_fields_100(cls,v):
        if v and len(v) > 100:
            raise ValueError("field must be at most 100 characters")
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

# Input schemas
class DeliveryMethodCreateSchema(DeliveryMethodSchema):
    class Config:
        exclude = ('id', 'created_date')

class DeliveryMethodUpdateSchema(DeliveryMethodSchema):
    code: Optional[str]
    name: Optional[str]
    
    class Config:
        exclude = ('id', 'created_date')

class CarrierTypeCreateSchema(CarrierTypeSchema):
    class Config:
        exclude = ('id', 'created_date')

class CarrierTypeUpdateSchema(CarrierTypeSchema):
    code: Optional[str]
    name: Optional[str]
    
    class Config:
        exclude = ('id', 'created_date')

class CarrierCreateSchema(CarrierSchema):
    class Config:
        exclude = ('id', 'public_id', 'created_date', 'created_by', 'last_modified_date', 'last_modified_by')

class CarrierUpdateSchema(CarrierSchema):
    carrier_code: Optional[str]
    name: Optional[str]
    carrier_type_id: Optional[int]
    
    class Config:
        exclude = ('id', 'public_id', 'created_date', 'created_by', 'last_modified_date', 'last_modified_by')

class DocumentTypeCreateSchema(DocumentTypeSchema):
    class Config:
        exclude = ('id', 'created_date')

class DocumentTypeUpdateSchema(DocumentTypeSchema):
    code: Optional[str]
    name: Optional[str]
    
    class Config:
        exclude = ('id', 'created_date')

class ShipmentCreateSchema(ShipmentSchema):
    class Config:
        exclude = ('id', 'public_id', 'shipment_number', 'created_date', 'created_by',
                  'shipped_by', 'shipped_date', 'delivered_confirmed_by', 'delivered_confirmed_date',
                  'final_delivery_address', 'final_contact_person', 'final_contact_phone', 'days_in_transit')

class ShipmentUpdateSchema(ShipmentSchema):
    shipment_date: Optional[date]
    packing_slip_id: Optional[int]
    customer_id: Optional[int]
    
    class Config:
        exclude = ('id', 'public_id', 'shipment_number', 'created_date', 'created_by',
                  'shipped_by', 'shipped_date', 'delivered_confirmed_by', 'delivered_confirmed_date',
                  'final_delivery_address', 'final_contact_person', 'final_contact_phone', 'days_in_transit')

class ShipmentDocumentCreateSchema(ShipmentDocumentSchema):
    class Config:
        exclude = ('id', 'public_id', 'created_date', 'uploaded_by', 'generated_by', 'generated_date')

class ShipmentDocumentUpdateSchema(ShipmentDocumentSchema):
    shipment_id: Optional[int]
    document_type_id: Optional[int]
    document_name: Optional[str]
    
    class Config:
        exclude = ('id', 'public_id', 'created_date', 'uploaded_by', 'generated_by', 'generated_date')

class ShipmentTrackingCreateSchema(ShipmentTrackingSchema):
    class Config:
        exclude = ('id', 'created_by', 'created_date')

class ShipmentTrackingUpdateSchema(ShipmentTrackingSchema):
    shipment_id: Optional[int]
    tracking_date: Optional[datetime]
    status: Optional[str]
    
    class Config:
        exclude = ('id', 'created_by', 'created_date')