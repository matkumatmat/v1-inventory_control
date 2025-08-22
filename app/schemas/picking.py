"""
Picking Domain Schemas
======================

Schemas untuk PickingList, PickingOrder, dan related models
"""

from pydantic import BaseModel, model_validator, field_validator
from typing import Optional
from datetime import date, datetime
from .base import BaseSchema, TimestampMixin
from .validators import validate_priority_level

class PickingListSchema(BaseSchema, TimestampMixin):
    """Schema untuk PickingList model"""
    picking_list_number: Optional[str] = None
    picking_date: date
    
    shipping_plan_id: int
    packing_slip_id: Optional[int] = None
    warehouse_id: int
    
    priority_level: int = 5
    scheduled_pick_date: Optional[date] = None
    estimated_duration_minutes: Optional[int] = None
    
    status: str = 'PENDING'
    
    assigned_to: Optional[str] = None
    assigned_date: Optional[datetime] = None
    
    total_items: int = 0
    completed_items: int = 0
    
    notes: Optional[str] = None
    special_instructions: Optional[str] = None
    
    approved_by: Optional[str] = None
    approved_date: Optional[datetime] = None
    started_by: Optional[str] = None
    started_date: Optional[datetime] = None
    completed_by: Optional[str] = None
    completed_date: Optional[datetime] = None
    
    completion_percentage: Optional[float] = None
    total_quantity_to_pick: Optional[int] = None
    estimated_end_time: Optional[datetime] = None

    @field_validator('priority_level')
    def validate_priority_level_field(cls, v):
        return validate_priority_level(v)

    @field_validator('shipping_plan_id', 'packing_slip_id', 'warehouse_id')
    def id_fields_positive(cls, v):
        if v is not None and v < 1:
            raise ValueError('ID fields must be positive')
        return v

    @field_validator('estimated_duration_minutes')
    def duration_range(cls, v):
        if v and not 1 <= v <= 1440:
            raise ValueError('estimated_duration_minutes must be between 1 and 1440')
        return v

    @field_validator('status')
    def status_valid(cls, v):
        if v not in ['PENDING', 'APPROVED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']:
            raise ValueError('Invalid status')
        return v
        
    @field_validator('assigned_to', 'approved_by', 'started_by', 'completed_by')
    def user_field_length(cls, v):
        if v and len(v) > 50:
            raise ValueError("user fields must be max 50 chars")
        return v

    @field_validator('total_items', 'completed_items')
    def item_counts_non_negative(cls, v):
        if v < 0:
            raise ValueError('Item counts must be non-negative')
        return v
        
class PickingListItemSchema(BaseSchema):
    """Schema untuk PickingListItem model"""
    picking_list_id: int
    shipping_plan_item_id: int
    product_id: int
    allocation_id: int
    rack_id: int
    
    quantity_to_pick: int
    quantity_picked: int = 0
    
    pick_sequence: Optional[int] = None
    pick_instructions: Optional[str] = None
    
    status: str = 'PENDING'
    
    notes: Optional[str] = None
    
    quantity_remaining: Optional[int] = None
    pick_completion_percentage: Optional[float] = None

    @field_validator('picking_list_id', 'shipping_plan_item_id', 'product_id', 'allocation_id', 'rack_id', 'pick_sequence')
    def id_fields_positive(cls, v):
        if v is not None and v < 1:
            raise ValueError('ID fields and sequence must be positive')
        return v
    
    @field_validator('quantity_to_pick')
    def quantity_to_pick_positive(cls,v):
        if v <= 0:
            raise ValueError('quantity to pick must be positive')
        return v
        
    @field_validator('quantity_picked')
    def quantity_picked_non_negative(cls,v):
        if v < 0:
            raise ValueError('quantity picked must be non-negative')
        return v

    @field_validator('status')
    def status_valid(cls, v):
        if v not in ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']:
            raise ValueError('Invalid status')
        return v
        
    @model_validator(mode='after')
    def validate_picking_quantities(cls, values):
        """Validate picking quantities"""
        to_pick, picked = values.get('quantity_to_pick', 0), values.get('quantity_picked', 0)
        
        if picked > to_pick:
            raise ValueError('Picked quantity cannot exceed quantity to pick')
        return values

class PickingOrderSchema(BaseSchema, TimestampMixin):
    """Schema untuk PickingOrder model"""
    picking_order_number: Optional[str] = None
    picking_date: date
    
    picking_list_id: int
    
    warehouse_id: int
    assigned_picker: Optional[str] = None
    
    status: str = 'PENDING'
    
    total_items: int = 0
    completed_items: int = 0
    
    estimated_duration_minutes: Optional[int] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    
    requires_qc_check: bool = False
    qc_status: Optional[str] = None
    qc_by: Optional[str] = None
    qc_date: Optional[datetime] = None
    qc_notes: Optional[str] = None
    
    notes: Optional[str] = None
    
    started_by: Optional[str] = None
    completed_by: Optional[str] = None
    
    completion_percentage: Optional[float] = None
    actual_duration_minutes: Optional[int] = None
    efficiency_percentage: Optional[float] = None

    @field_validator('picking_list_id', 'warehouse_id')
    def id_fields_positive(cls,v):
        if v < 1:
            raise ValueError('ID fields must be positive')
        return v
        
    @field_validator('assigned_picker', 'qc_by', 'started_by', 'completed_by')
    def user_fields_length(cls,v):
        if v and len(v) > 50:
            raise ValueError("User fields must be max 50 chars")
        return v

    @field_validator('status')
    def status_valid(cls, v):
        if v not in ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']:
            raise ValueError('Invalid status')
        return v

    @field_validator('total_items', 'completed_items')
    def item_counts_non_negative(cls, v):
        if v < 0:
            raise ValueError('Item counts must be non-negative')
        return v

    @field_validator('estimated_duration_minutes')
    def duration_range(cls, v):
        if v and not 1 <= v <= 1440:
            raise ValueError('estimated_duration_minutes must be between 1 and 1440')
        return v

    @field_validator('qc_status')
    def qc_status_valid(cls, v):
        if v and v not in ['PENDING', 'PASSED', 'FAILED']:
            raise ValueError('Invalid qc_status')
        return v
        
    @model_validator(mode='after')
    def validate_picking_order_timing(cls, values):
        """Validate timing constraints"""
        start_time, end_time = values.get('actual_start_time'), values.get('actual_end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise ValueError('Start time must be before end time')
        return values

class PickingOrderItemSchema(BaseSchema):
    """Schema untuk PickingOrderItem model"""
    picking_order_id: int
    picking_list_item_id: int
    product_id: int
    allocation_id: int
    rack_id: int
    
    quantity_requested: int
    quantity_picked: int
    quantity_variance: int = 0
    
    batch_id: int
    batch_number: Optional[str] = None
    expiry_date: Optional[date] = None
    
    pick_sequence: Optional[int] = None
    picked_at: Optional[datetime] = None
    picked_by: Optional[str] = None
    
    condition_notes: Optional[str] = None
    variance_reason: Optional[str] = None
    
    status: str = 'PICKED'
    
    variance_percentage: Optional[float] = None
    
    @field_validator('picking_order_id', 'picking_list_item_id', 'product_id', 'allocation_id', 'rack_id', 'batch_id', 'pick_sequence')
    def id_fields_positive(cls,v):
        if v is not None and v < 1:
            raise ValueError('ID fields and sequence must be positive')
        return v
        
    @field_validator('quantity_requested')
    def quantity_requested_positive(cls,v):
        if v <= 0:
            raise ValueError("quantity requested must be positive")
        return v
    
    @field_validator('quantity_picked')
    def quantity_picked_non_negative(cls,v):
        if v < 0:
            raise ValueError("quantity picked must be non negative")
        return v

    @field_validator('batch_number')
    def batch_number_length(cls,v):
        if v and len(v) > 100:
            raise ValueError('batch_number must be at most 100 characters')
        return v
        
    @field_validator('picked_by')
    def picked_by_length(cls,v):
        if v and len(v) > 50:
            raise ValueError('picked_by must be at most 50 characters')
        return v

    @field_validator('status')
    def status_valid(cls, v):
        if v not in ['PICKED', 'QC_PASSED', 'QC_FAILED', 'REJECTED']:
            raise ValueError('Invalid status')
        return v
        
    @model_validator(mode='after')
    def calculate_variance(cls, values):
        """Auto-calculate variance"""
        if 'quantity_requested' in values and 'quantity_picked' in values:
            values['quantity_variance'] = values['quantity_picked'] - values['quantity_requested']
        return values

# Input schemas
class PickingListCreateSchema(PickingListSchema):
    class Config:
        exclude = ('id', 'public_id', 'picking_list_number', 'created_date', 'created_by',
                  'approved_by', 'approved_date', 'started_by', 'started_date', 'completed_by',
                  'completed_date', 'completion_percentage', 'total_quantity_to_pick', 'estimated_end_time')

class PickingListUpdateSchema(PickingListSchema):
    picking_date: Optional[date]
    shipping_plan_id: Optional[int]
    warehouse_id: Optional[int]
    
    class Config:
        exclude = ('id', 'public_id', 'picking_list_number', 'created_date', 'created_by',
                  'approved_by', 'approved_date', 'started_by', 'started_date', 'completed_by',
                  'completed_date', 'completion_percentage', 'total_quantity_to_pick', 'estimated_end_time')

class PickingListItemCreateSchema(PickingListItemSchema):
    class Config:
        exclude = ('id', 'quantity_remaining', 'pick_completion_percentage')

class PickingListItemUpdateSchema(PickingListItemSchema):
    picking_list_id: Optional[int]
    shipping_plan_item_id: Optional[int]
    product_id: Optional[int]
    allocation_id: Optional[int]
    rack_id: Optional[int]
    quantity_to_pick: Optional[int]
    
    class Config:
        exclude = ('id', 'quantity_remaining', 'pick_completion_percentage')

class PickingOrderCreateSchema(PickingOrderSchema):
    class Config:
        exclude = ('id', 'public_id', 'picking_order_number', 'created_date', 'created_by',
                  'started_by', 'completed_by', 'completion_percentage', 'actual_duration_minutes',
                  'efficiency_percentage')

class PickingOrderUpdateSchema(PickingOrderSchema):
    picking_date: Optional[date]
    picking_list_id: Optional[int]
    warehouse_id: Optional[int]
    
    class Config:
        exclude = ('id', 'public_id', 'picking_order_number', 'created_date', 'created_by',
                  'started_by', 'completed_by', 'completion_percentage', 'actual_duration_minutes',
                  'efficiency_percentage')

class PickingOrderItemCreateSchema(PickingOrderItemSchema):
    class Config:
        exclude = ('id', 'variance_percentage')

class PickingOrderItemUpdateSchema(PickingOrderItemSchema):
    picking_order_id: Optional[int]
    picking_list_item_id: Optional[int]
    product_id: Optional[int]
    allocation_id: Optional[int]
    rack_id: Optional[int]
    quantity_requested: Optional[int]
    quantity_picked: Optional[int]
    batch_id: Optional[int]
    
    class Config:
        exclude = ('id', 'variance_percentage')