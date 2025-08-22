"""
Warehouse Domain Schemas
========================

Schemas untuk Warehouse, Rack, dan RackAllocation
"""

from pydantic import BaseModel, model_validator, field_validator
from typing import Optional
from decimal import Decimal
from datetime import datetime
from .base import BaseSchema, TimestampMixin, StatusMixin, AddressMixin
from .validators import validate_rack_code

class WarehouseSchema(BaseSchema, TimestampMixin, StatusMixin, AddressMixin):
    """Schema untuk Warehouse model"""
    warehouse_code: str
    name: str
    description: Optional[str] = None
    
    total_capacity: Optional[Decimal] = None
    temperature_controlled: bool = False
    humidity_controlled: bool = False
    security_level: str = 'STANDARD'
    
    operating_hours: Optional[str] = None
    time_zone: str = 'Asia/Jakarta'
    
    manager_name: Optional[str] = None
    manager_phone: Optional[str] = None
    manager_email: Optional[str] = None

    @field_validator('warehouse_code')
    def warehouse_code_length(cls, v):
        if not 2 <= len(v) <= 20:
            raise ValueError('warehouse_code must be between 2 and 20 characters')
        return v

    @field_validator('name', 'operating_hours', 'manager_name')
    def name_length(cls, v):
        if v and not 2 <= len(v) <= 100:
            raise ValueError('name fields must be between 2 and 100 characters')
        return v

    @field_validator('total_capacity')
    def capacity_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError('total_capacity must be non-negative')
        return v

    @field_validator('security_level')
    def security_level_valid(cls, v):
        if v not in ['BASIC', 'STANDARD', 'HIGH', 'MAXIMUM']:
            raise ValueError('Invalid security_level')
        return v

    @field_validator('time_zone')
    def time_zone_length(cls, v):
        if len(v) > 50:
            raise ValueError('time_zone must be at most 50 characters')
        return v
        
    @field_validator('manager_phone')
    def manager_phone_length(cls, v):
        if v and len(v) > 20:
            raise ValueError('manager_phone must be at most 20 characters')
        return v

class RackSchema(BaseSchema, TimestampMixin, StatusMixin):
    """Schema untuk Rack model"""
    warehouse_id: int
    
    rack_code: str
    zone: Optional[str] = None
    aisle: Optional[str] = None
    section: Optional[str] = None
    level: Optional[str] = None
    position: Optional[str] = None
    
    max_capacity: Optional[int] = None
    current_quantity: int = 0
    
    length_cm: Optional[Decimal] = None
    width_cm: Optional[Decimal] = None
    height_cm: Optional[Decimal] = None
    
    temperature_controlled: bool = False
    humidity_controlled: bool = False
    special_conditions: Optional[str] = None
    
    access_level: str = 'STANDARD'
    requires_authorization: bool = False
    
    available_capacity: Optional[int] = None
    utilization_percentage: Optional[float] = None
    
    warehouse: Optional[WarehouseSchema] = None

    @field_validator('rack_code')
    def validate_rack_code_field(cls, v):
        return validate_rack_code(v)

    @field_validator('warehouse_id')
    def warehouse_id_positive(cls, v):
        if v < 1:
            raise ValueError('warehouse_id must be positive')
        return v

    @field_validator('zone')
    def zone_length(cls, v):
        if v and len(v) > 20:
            raise ValueError('zone must be at most 20 characters')
        return v

    @field_validator('aisle', 'section', 'level', 'position')
    def location_part_length(cls, v):
        if v and len(v) > 10:
            raise ValueError('aisle, section, level, and position must be at most 10 characters')
        return v

    @field_validator('max_capacity', 'current_quantity', 'length_cm', 'width_cm', 'height_cm')
    def numeric_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError('Numeric properties must be non-negative')
        return v

    @field_validator('access_level')
    def access_level_valid(cls, v):
        if v not in ['STANDARD', 'RESTRICTED', 'SECURE']:
            raise ValueError('Invalid access_level')
        return v
        
    @model_validator(mode='after')
    def validate_capacity_constraints(cls, values):
        """Validate capacity constraints"""
        current_qty, max_capacity = values.get('current_quantity', 0), values.get('max_capacity')
        if max_capacity is not None and current_qty > max_capacity:
            raise ValueError('Current quantity cannot exceed max capacity')
        return values

class RackAllocationSchema(BaseSchema):
    """Schema untuk RackAllocation model"""
    allocation_id: int
    rack_id: int
    quantity: int
    
    placement_date: Optional[datetime] = None
    placed_by: Optional[str] = None
    position_details: Optional[str] = None
    
    rack: Optional[RackSchema] = None

    @field_validator('allocation_id', 'rack_id')
    def id_fields_positive(cls, v):
        if v < 1:
            raise ValueError('ID fields must be positive')
        return v

    @field_validator('quantity')
    def quantity_positive(cls, v):
        if v <= 0:
            raise ValueError('quantity must be positive')
        return v

# Input schemas
class WarehouseCreateSchema(WarehouseSchema):
    class Config:
        exclude = ('id', 'public_id', 'created_date', 'created_by', 'last_modified_date', 'last_modified_by')

class WarehouseUpdateSchema(WarehouseSchema):
    warehouse_code: Optional[str]
    name: Optional[str]
    
    class Config:
        exclude = ('id', 'public_id', 'created_date', 'created_by', 'last_modified_date', 'last_modified_by')

class RackCreateSchema(RackSchema):
    class Config:
        exclude = ('id', 'public_id', 'created_date', 'created_by', 'last_modified_date', 
                  'last_modified_by', 'available_capacity', 'utilization_percentage')

class RackUpdateSchema(RackSchema):
    warehouse_id: Optional[int]
    rack_code: Optional[str]
    
    class Config:
        exclude = ('id', 'public_id', 'created_date', 'created_by', 'last_modified_date',
                  'last_modified_by', 'available_capacity', 'utilization_percentage')

class RackAllocationCreateSchema(RackAllocationSchema):
    class Config:
        exclude = ('id', 'placement_date', 'placed_by')