"""
Packing Domain Schemas
======================

Schemas untuk PackingOrder, PackingBox, dan PackingBoxItem
"""

from pydantic import BaseModel, model_validator, field_validator
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from .base import BaseSchema, TimestampMixin
from .validators import validate_positive_number, validate_non_negative_number

class PackingOrderSchema(BaseSchema, TimestampMixin):
    """Schema untuk PackingOrder model"""
    packing_order_number: Optional[str] = None
    packing_date: date
    
    picking_order_id: int
    
    customer_id: int
    
    total_items: int = 0
    total_quantity: int = 0
    total_boxes: int = 0
    
    requires_temperature_control: bool = False
    requires_fragile_handling: bool = False
    special_packing_instructions: Optional[str] = None
    
    status: str = 'PENDING'
    
    assigned_packer: Optional[str] = None
    
    estimated_duration_minutes: Optional[int] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    
    notes: Optional[str] = None
    
    started_by: Optional[str] = None
    completed_by: Optional[str] = None
    
    completion_percentage: Optional[float] = None
    actual_duration_minutes: Optional[int] = None
    total_weight_kg: Optional[Decimal] = None
    total_volume_m3: Optional[Decimal] = None

    @field_validator('picking_order_id', 'customer_id')
    def id_fields_positive(cls, v):
        if v < 1:
            raise ValueError('ID fields must be positive')
        return v

    @field_validator('total_items', 'total_quantity', 'total_boxes')
    def totals_non_negative(cls, v):
        if v < 0:
            raise ValueError('Total counts must be non-negative')
        return v
        
    @field_validator('assigned_packer', 'started_by', 'completed_by')
    def user_fields_length(cls,v):
        if v and len(v) > 50:
            raise ValueError('user fields must be at most 50 characters')
        return v

    @field_validator('status')
    def status_valid(cls, v):
        if v not in ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']:
            raise ValueError('Invalid status')
        return v
        
    @field_validator('estimated_duration_minutes')
    def duration_range(cls, v):
        if v and not 1 <= v <= 1440:
            raise ValueError('estimated_duration_minutes must be between 1 and 1440')
        return v

    @model_validator(mode='after')
    def validate_packing_timing(cls, values):
        """Validate timing constraints"""
        start_time, end_time = values.get('actual_start_time'), values.get('actual_end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise ValueError('Start time must be before end time')
        return values
        
class PackingBoxSchema(BaseSchema):
    """Schema untuk PackingBox model"""
    packing_order_id: int
    box_number: str
    box_type: Optional[str] = None
    
    packaging_material_id: Optional[int] = None
    
    length_cm: Optional[Decimal] = None
    width_cm: Optional[Decimal] = None
    height_cm: Optional[Decimal] = None
    weight_kg: Optional[Decimal] = None
    
    total_items: int = 0
    total_quantity: int = 0
    
    is_fragile: bool = False
    requires_upright: bool = False
    temperature_requirements: Optional[str] = None
    
    status: str = 'OPEN'
    
    packed_by: Optional[str] = None
    packed_date: Optional[datetime] = None
    sealed_by: Optional[str] = None
    sealed_date: Optional[datetime] = None
    
    volume_m3: Optional[Decimal] = None
    utilization_percentage: Optional[float] = None
    
    @field_validator('packing_order_id', 'packaging_material_id')
    def id_fields_positive(cls, v):
        if v is not None and v < 1:
            raise ValueError('ID fields must be positive')
        return v

    @field_validator('box_number', 'box_type', 'temperature_requirements', 'packed_by', 'sealed_by')
    def string_fields_50(cls, v):
        if v and len(v) > 50:
            raise ValueError('field must be at most 50 characters')
        return v
        
    @field_validator('box_number')
    def box_number_not_empty(cls,v):
        if len(v) < 1:
            raise ValueError("box number cannot be empty")
        return v

    @field_validator('length_cm', 'width_cm', 'height_cm', 'weight_kg')
    def dimensions_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError('Dimensions and weight must be non-negative')
        return v

    @field_validator('total_items', 'total_quantity')
    def totals_non_negative(cls, v):
        if v < 0:
            raise ValueError('Total counts must be non-negative')
        return v
        
    @field_validator('status')
    def status_valid(cls, v):
        if v not in ['OPEN', 'SEALED', 'SHIPPED']:
            raise ValueError('Invalid status')
        return v

class PackingBoxItemSchema(BaseSchema):
    """Schema untuk PackingBoxItem model"""
    packing_box_id: int
    picking_order_item_id: int
    product_id: int
    batch_id: int
    
    quantity_packed: int
    
    packing_sequence: Optional[int] = None
    special_handling_notes: Optional[str] = None
    
    packed_by: Optional[str] = None
    packed_at: Optional[datetime] = None
    
    @field_validator('packing_box_id', 'picking_order_item_id', 'product_id', 'batch_id', 'packing_sequence')
    def id_fields_positive(cls, v):
        if v is not None and v < 1:
            raise ValueError('ID fields and sequence must be positive')
        return v
        
    @field_validator('quantity_packed')
    def quantity_packed_positive(cls,v):
        if v <= 0:
            raise ValueError("quantity packed must be a positive number")
        return v
        
    @field_validator('packed_by')
    def packed_by_length(cls,v):
        if v and len(v) > 50:
            raise ValueError("packed by must be at most 50 characters")
        return v

# Input schemas
class PackingOrderCreateSchema(PackingOrderSchema):
    class Config:
        exclude = ('id', 'public_id', 'packing_order_number', 'created_date', 'created_by',
                  'started_by', 'completed_by', 'completion_percentage', 'actual_duration_minutes',
                  'total_weight_kg', 'total_volume_m3')

class PackingOrderUpdateSchema(PackingOrderSchema):
    packing_date: Optional[date]
    picking_order_id: Optional[int]
    customer_id: Optional[int]
    
    class Config:
        exclude = ('id', 'public_id', 'packing_order_number', 'created_date', 'created_by',
                  'started_by', 'completed_by', 'completion_percentage', 'actual_duration_minutes',
                  'total_weight_kg', 'total_volume_m3')

class PackingBoxCreateSchema(PackingBoxSchema):
    class Config:
        exclude = ('id', 'public_id', 'packed_by', 'packed_date', 'sealed_by', 'sealed_date',
                  'volume_m3', 'utilization_percentage')

class PackingBoxUpdateSchema(PackingBoxSchema):
    packing_order_id: Optional[int]
    box_number: Optional[str]
    
    class Config:
        exclude = ('id', 'public_id', 'packed_by', 'packed_date', 'sealed_by', 'sealed_date',
                  'volume_m3', 'utilization_percentage')

class PackingBoxItemCreateSchema(PackingBoxItemSchema):
    class Config:
        exclude = ('id', 'packed_by', 'packed_at')

class PackingBoxItemUpdateSchema(PackingBoxItemSchema):
    packing_box_id: Optional[int]
    picking_order_item_id: Optional[int]
    product_id: Optional[int]
    batch_id: Optional[int]
    quantity_packed: Optional[int]
    
    class Config:
        exclude = ('id', 'packed_by', 'packed_at')