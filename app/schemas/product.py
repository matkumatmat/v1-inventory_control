"""
Product Domain Schemas
======================

Schemas untuk Product, Batch, Allocation, dan StockMovement
"""

from pydantic import BaseModel, model_validator, field_validator
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from .base import BaseSchema, TimestampMixin, StatusMixin, ERPMixin
from .validators import (
    validate_product_code, validate_batch_number, validate_expiry_date,
    validate_manufacturing_date, validate_positive_number, validate_non_negative_number,
    validate_allocation_quantities, validate_nie_number
)

class ProductTypeSchema(BaseSchema):
    """Schema untuk ProductType enum"""
    code: str
    name: str
    description: Optional[str] = None
    requires_batch_tracking: bool = True
    requires_expiry_tracking: bool = True
    shelf_life_days: Optional[int] = None
    is_active: bool = True
    sort_order: int = 0

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
        
    @field_validator('shelf_life_days')
    def shelf_life_days_positive(cls, v):
        if v is not None and v < 1:
            raise ValueError('shelf_life_days must be at least 1')
        return v

class PackageTypeSchema(BaseSchema):
    """Schema untuk PackageType enum"""
    code: str
    name: str
    description: Optional[str] = None
    is_fragile: bool = False
    is_stackable: bool = True
    max_stack_height: Optional[int] = None
    standard_length: Optional[float] = None
    standard_width: Optional[float] = None
    standard_height: Optional[float] = None
    standard_weight: Optional[float] = None
    special_handling_required: bool = False
    handling_instructions: Optional[str] = None
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
    
    @field_validator('max_stack_height')
    def stack_height_positive(cls, v):
        if v is not None and v < 1:
            raise ValueError('max_stack_height must be at least 1')
        return v

    @field_validator('standard_length', 'standard_width', 'standard_height', 'standard_weight')
    def standard_dimensions_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError('standard dimensions/weight must be non-negative')
        return v

class TemperatureTypeSchema(BaseSchema):
    """Schema untuk TemperatureType enum"""
    code: str
    name: str
    description: Optional[str] = None
    min_celsius: Optional[float] = None
    max_celsius: Optional[float] = None
    optimal_celsius: Optional[float] = None
    celsius_display: Optional[str] = None
    humidity_range: Optional[str] = None
    special_storage_requirements: Optional[str] = None
    color_code: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool = True

    @field_validator('code')
    def code_length(cls, v):
        if len(v) > 10:
            raise ValueError('code must be at most 10 characters')
        return v

    @field_validator('name', 'icon')
    def name_icon_length(cls, v):
        if v and len(v) > 50:
            raise ValueError('name and icon must be at most 50 characters')
        return v

    @field_validator('celsius_display', 'humidity_range')
    def display_range_length(cls, v):
        if v and len(v) > 20:
            raise ValueError('display and range fields must be at most 20 characters')
        return v

    @field_validator('color_code')
    def color_code_length(cls, v):
        if v and len(v) > 7:
            raise ValueError('color_code must be at most 7 characters')
        return v

    @model_validator(mode='after')
    def validate_temperature_range(cls, values):
        """Validate temperature range"""
        min_temp, max_temp = values.get('min_celsius'), values.get('max_celsius')
        if min_temp is not None and max_temp is not None and min_temp > max_temp:
            raise ValueError('Min temperature cannot be greater than max temperature')
        return values

class ProductTypeCreateSchema(ProductTypeSchema):
    class Config:
        exclude = ('id',)

class ProductTypeUpdateSchema(ProductTypeSchema):
    code: Optional[str]
    name: Optional[str]
    
    class Config:
        exclude = ('id',)

class PackageTypeCreateSchema(PackageTypeSchema):
    class Config:
        exclude = ('id',)

class PackageTypeUpdateSchema(PackageTypeSchema):
    code: Optional[str]
    name: Optional[str]
    
    class Config:
        exclude = ('id',)

class TemperatureTypeCreateSchema(TemperatureTypeSchema):
    class Config:
        exclude = ('id',)

class TemperatureTypeUpdateSchema(TemperatureTypeSchema):
    code: Optional[str]
    name: Optional[str]
    
    class Config:
        exclude = ('id',)

class ProductSchema(BaseSchema, TimestampMixin, StatusMixin, ERPMixin):
    """Schema untuk Product model"""
    product_code: str
    name: str
    generic_name: Optional[str] = None
    strength: Optional[str] = None
    dosage_form: Optional[str] = None
    
    product_type_id: int
    package_type_id: Optional[int] = None
    temperature_type_id: Optional[int] = None
    
    manufacturer: Optional[str] = None
    country_origin: Optional[str] = None
    registration_number: Optional[str] = None
    
    unit_of_measure: str = 'PCS'
    weight_per_unit: Optional[Decimal] = None
    volume_per_unit: Optional[Decimal] = None
    
    unit_cost: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    
    erp_product_id: Optional[str] = None
    
    product_type: Optional[ProductTypeSchema] = None
    package_type: Optional[PackageTypeSchema] = None
    temperature_type: Optional[TemperatureTypeSchema] = None

    @field_validator('product_code')
    def validate_product_code_field(cls, v):
        return validate_product_code(v)

    @field_validator('name', 'generic_name', 'manufacturer')
    def name_length(cls, v):
        if v and len(v) > 200:
            raise ValueError('name, generic_name, and manufacturer must be at most 200 characters')
        if v and len(v) < 3:
             raise ValueError('name must be at least 3 characters')
        return v

    @field_validator('strength', 'dosage_form', 'country_origin', 'registration_number')
    def string_field_length_100(cls, v):
        if v and len(v) > 100:
            raise ValueError('field must be at most 100 characters')
        return v

    @field_validator('product_type_id', 'package_type_id', 'temperature_type_id')
    def id_fields_positive(cls, v):
        if v is not None and v < 1:
            raise ValueError('ID fields must be positive')
        return v
    
    @field_validator('unit_of_measure', 'erp_product_id')
    def uom_erp_id_length(cls, v):
        if v and len(v) > 50:
            raise ValueError('unit_of_measure and erp_product_id must be at most 50 characters')
        return v
        
    @field_validator('weight_per_unit', 'volume_per_unit', 'unit_cost', 'selling_price')
    def decimal_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError('Decimal fields must be non-negative')
        return v

class BatchSchema(BaseSchema, TimestampMixin, ERPMixin):
    """Schema untuk Batch model"""
    product_id: int
    batch_number: str
    lot_number: Optional[str] = None
    serial_number: Optional[str] = None
    
    nie_number: Optional[str] = None
    registration_number: Optional[str] = None
    
    received_quantity: int
    
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    received_date: date
    
    qc_status: str = 'PENDING'
    qc_date: Optional[datetime] = None
    qc_notes: Optional[str] = None
    qc_by: Optional[str] = None
    
    supplier_name: Optional[str] = None
    supplier_batch_number: Optional[str] = None
    purchase_order_number: Optional[str] = None
    
    unit_cost: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    
    status: str = 'ACTIVE'
    
    erp_batch_id: Optional[str] = None
    
    product: Optional[ProductSchema] = None

    @field_validator('batch_number')
    def validate_batch_number_field(cls, v):
        return validate_batch_number(v)

    @field_validator('nie_number')
    def validate_nie_number_field(cls, v):
        return validate_nie_number(v)

    @field_validator('received_quantity')
    def validate_received_quantity_field(cls, v):
        return validate_positive_number(v)

    @field_validator('manufacturing_date')
    def validate_manufacturing_date_field(cls, v):
        return validate_manufacturing_date(v)

    @field_validator('expiry_date')
    def validate_expiry_date_field(cls, v):
        return validate_expiry_date(v)
    
    @field_validator('product_id')
    def product_id_positive(cls,v):
        if v < 1:
            raise ValueError("product_id must be positive")
        return v
        
    @field_validator('lot_number', 'serial_number', 'registration_number', 'supplier_batch_number', 'purchase_order_number')
    def string_field_length_100(cls, v):
        if v and len(v) > 100:
            raise ValueError('field must be at most 100 characters')
        return v

    @field_validator('qc_status')
    def qc_status_valid(cls, v):
        if v not in ['PENDING', 'PASSED', 'FAILED', 'QUARANTINE']:
            raise ValueError('Invalid qc_status')
        return v
        
    @field_validator('qc_by', 'erp_batch_id')
    def qc_by_erp_id_length(cls,v):
        if v and len(v) > 50:
            raise ValueError("field must be at most 50 characters")
        return v
            
    @field_validator('supplier_name')
    def supplier_name_length(cls, v):
        if v and len(v) > 200:
            raise ValueError('supplier_name must be at most 200 characters')
        return v

    @field_validator('unit_cost', 'total_cost')
    def cost_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError('Cost fields must be non-negative')
        return v

    @field_validator('status')
    def status_valid(cls, v):
        if v not in ['ACTIVE', 'CONSUMED', 'EXPIRED', 'RECALLED']:
            raise ValueError('Invalid status')
        return v

    @model_validator(mode='after')
    def validate_dates(cls, values):
        """Validate date relationships"""
        manufacturing_date, expiry_date = values.get('manufacturing_date'), values.get('expiry_date')
        if manufacturing_date and expiry_date and manufacturing_date >= expiry_date:
            raise ValueError('Manufacturing date must be before expiry date')
        return values

class AllocationTypeSchema(BaseSchema):
    """Schema untuk AllocationType enum"""
    code: str
    name: str
    description: Optional[str] = None
    requires_customer: bool = False
    is_reservable: bool = True
    auto_assign_customer: bool = False
    priority_level: int = 1
    max_allocation_days: Optional[int] = None
    color_code: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool = True

    @field_validator('code')
    def code_length(cls,v):
        if len(v) > 10:
            raise ValueError("code must be at most 10 characters")
        return v
        
    @field_validator('name', 'icon')
    def name_icon_length(cls, v):
        if v and len(v) > 50:
            raise ValueError('name and icon must be at most 50 characters')
        return v

    @field_validator('priority_level')
    def priority_level_range(cls, v):
        if not 1 <= v <= 9:
            raise ValueError('priority_level must be between 1 and 9')
        return v
        
    @field_validator('max_allocation_days')
    def max_allocation_days_positive(cls, v):
        if v is not None and v < 1:
            raise ValueError("max_allocation_days must be positive")
        return v

    @field_validator('color_code')
    def color_code_length(cls, v):
        if v and len(v) > 7:
            raise ValueError('color_code must be at most 7 characters')
        return v

class AllocationSchema(BaseSchema, TimestampMixin):
    """Schema untuk Allocation model"""
    allocation_number: Optional[str] = None
    
    batch_id: int
    allocation_type_id: int
    customer_id: Optional[int] = None
    tender_contract_id: Optional[int] = None
    
    allocated_quantity: int
    shipped_quantity: int = 0
    reserved_quantity: int = 0
    
    original_reserved_quantity: int = 0
    customer_allocated_quantity: int = 0
    
    status: str = 'active'
    allocation_date: date
    expiry_date: Optional[date] = None
    
    priority_level: int = 5
    special_instructions: Optional[str] = None
    handling_requirements: Optional[str] = None
    
    unit_cost: Optional[Decimal] = None
    total_value: Optional[Decimal] = None
    
    available_stock: Optional[int] = None
    remaining_for_allocation: Optional[int] = None
    
    batch: Optional[BatchSchema] = None
    allocation_type: Optional[AllocationTypeSchema] = None

    @field_validator('allocated_quantity')
    def validate_allocated_quantity_field(cls, v):
        return validate_positive_number(v)

    @field_validator('shipped_quantity')
    def validate_shipped_quantity_field(cls, v):
        return validate_non_negative_number(v)

    @field_validator('reserved_quantity')
    def validate_reserved_quantity_field(cls, v):
        return validate_non_negative_number(v)

    @field_validator('original_reserved_quantity')
    def validate_original_reserved_quantity_field(cls, v):
        return validate_non_negative_number(v)

    @field_validator('customer_allocated_quantity')
    def validate_customer_allocated_quantity_field(cls, v):
        return validate_non_negative_number(v)

    @field_validator('batch_id', 'allocation_type_id', 'customer_id', 'tender_contract_id')
    def id_fields_positive(cls, v):
        if v is not None and v < 1:
            raise ValueError('ID fields must be positive')
        return v

    @field_validator('status')
    def status_valid(cls, v):
        if v not in ['active', 'shipped', 'consumed', 'expired']:
            raise ValueError('Invalid status')
        return v

    @field_validator('priority_level')
    def priority_level_range(cls, v):
        if not 1 <= v <= 9:
            raise ValueError('priority_level must be between 1 and 9')
        return v

    @field_validator('unit_cost', 'total_value')
    def cost_value_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError('Cost and value fields must be non-negative')
        return v

    @model_validator(mode='after')
    def validate_allocation_business_rules(cls, values):
        """Validate business rules"""
        allocated = values.get('allocated_quantity', 0)
        shipped = values.get('shipped_quantity', 0)
        reserved = values.get('reserved_quantity', 0)
        
        if shipped + reserved > allocated:
            raise ValueError('Shipped + Reserved cannot exceed Allocated quantity')
        
        original_reserved = values.get('original_reserved_quantity', 0)
        customer_allocated = values.get('customer_allocated_quantity', 0)
        
        if original_reserved > 0 and customer_allocated > original_reserved:
            raise ValueError('Customer allocated cannot exceed original reserved quantity')
        return values

class MovementTypeSchema(BaseSchema):
    """Schema untuk MovementType enum"""
    code: str
    name: str
    description: Optional[str] = None
    direction: str
    affects_stock: bool = True
    auto_generate_document: bool = False
    document_prefix: Optional[str] = None
    requires_approval: bool = False
    approval_level: int = 1
    is_active: bool = True

    @field_validator('code', 'document_prefix')
    def code_prefix_length(cls,v):
        if v and len(v)>10:
            raise ValueError("code and document prefix must be at most 10 characters")
        return v
        
    @field_validator('name')
    def name_length(cls, v):
        if len(v) > 50:
            raise ValueError('name must be at most 50 characters')
        return v

    @field_validator('direction')
    def direction_valid(cls, v):
        if v not in ['IN', 'OUT', 'TRANSFER']:
            raise ValueError('Invalid direction')
        return v

    @field_validator('approval_level')
    def approval_level_range(cls, v):
        if not 1 <= v <= 5:
            raise ValueError('approval_level must be between 1 and 5')
        return v

class StockMovementSchema(BaseSchema, TimestampMixin):
    """Schema untuk StockMovement model"""
    movement_number: Optional[str] = None
    
    allocation_id: int
    movement_type_id: int
    
    quantity: int
    movement_date: datetime = datetime.now()
    
    source_rack_id: Optional[int] = None
    destination_rack_id: Optional[int] = None
    
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    reference_number: Optional[str] = None
    
    requested_by: Optional[str] = None
    approved_by: Optional[str] = None
    executed_by: Optional[str] = None
    
    status: str = 'COMPLETED'
    
    notes: Optional[str] = None
    reason: Optional[str] = None
    
    allocation: Optional[AllocationSchema] = None
    movement_type: Optional[MovementTypeSchema] = None

    @field_validator('allocation_id', 'movement_type_id', 'source_rack_id', 'destination_rack_id', 'reference_id')
    def id_fields_positive(cls, v):
        if v is not None and v < 1:
            raise ValueError('ID fields must be positive')
        return v
    
    @field_validator('reference_type', 'requested_by', 'approved_by', 'executed_by')
    def string_fields_50(cls, v):
        if v and len(v) > 50:
            raise ValueError("field must be at most 50 characters")
        return v
            
    @field_validator('reference_number')
    def reference_number_length(cls, v):
        if v and len(v) > 100:
            raise ValueError('reference_number must be at most 100 characters')
        return v

    @field_validator('status')
    def status_valid(cls, v):
        if v not in ['PENDING', 'APPROVED', 'COMPLETED', 'CANCELLED']:
            raise ValueError('Invalid status')
        return v

    @field_validator('reason')
    def reason_length(cls, v):
        if v and len(v) > 200:
            raise ValueError('reason must be at most 200 characters')
        return v

# Input schemas for create/update operations
class ProductCreateSchema(ProductSchema):
    class Config:
        exclude = {'id', 'public_id', 'created_date', 'created_by', 'last_modified_date', 'last_modified_by'}

class ProductUpdateSchema(ProductSchema):
    product_code: Optional[str]
    name: Optional[str]
    product_type_id: Optional[int]
    
    class Config:
        exclude = {'id', 'public_id', 'created_date', 'created_by', 'last_modified_date', 'last_modified_by'}

class BatchCreateSchema(BatchSchema):
    class Config:
        exclude = {'id', 'public_id', 'created_date', 'created_by'}

class BatchUpdateSchema(BatchSchema):
    product_id: Optional[int]
    batch_number: Optional[str]
    received_quantity: Optional[int]
    received_date: Optional[date]
    
    class Config:
        exclude = {'id', 'public_id', 'created_date', 'created_by'}

class AllocationCreateSchema(AllocationSchema):
    class Config:
        exclude = {'id', 'public_id', 'allocation_number', 'created_date', 'created_by', 
                  'last_modified_date', 'last_modified_by', 'available_stock', 'remaining_for_allocation'}

class AllocationUpdateSchema(AllocationSchema):
    batch_id: Optional[int]
    allocation_type_id: Optional[int]
    allocated_quantity: Optional[int]
    allocation_date: Optional[date]
    
    class Config:
        exclude = ('id', 'public_id', 'allocation_number', 'created_date', 'created_by',
                  'last_modified_date', 'last_modified_by', 'available_stock', 'remaining_for_allocation')

class StockMovementCreateSchema(StockMovementSchema):
    class Config:
        exclude = ('id', 'public_id', 'movement_number', 'created_date', 'created_by')

class StockMovementUpdateSchema(StockMovementSchema):
    allocation_id: Optional[int]
    movement_type_id: Optional[int]
    quantity: Optional[int]
    movement_date: Optional[datetime]

    class Config:
        exclude = ('id', 'public_id', 'movement_number', 'created_date', 'created_by')