"""
Sales Domain Schemas
====================

Schemas untuk SalesOrder, ShippingPlan, dan PackingSlip
"""

from pydantic import BaseModel, model_validator, field_validator
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from .base import BaseSchema, TimestampMixin, StatusMixin, ERPMixin
from .validators import validate_so_number, validate_ps_number

class PackingSlipSchema(BaseSchema, TimestampMixin, StatusMixin, ERPMixin):
    """Schema untuk PackingSlip model"""
    ps_number: str
    ps_date: date
    
    do_number: Optional[str] = None
    do_date: Optional[date] = None
    do_document_url: Optional[str] = None
    
    erp_ps_id: Optional[str] = None
    erp_do_id: Optional[str] = None
    
    status: str = 'PENDING'
    
    ps_document_url: Optional[str] = None
    
    total_sales_orders: Optional[int] = None
    total_picking_lists: Optional[int] = None
    total_quantity: Optional[int] = None

    @field_validator('ps_number')
    def validate_ps_number_field(cls, v):
        return validate_ps_number(v)

    @field_validator('do_number', 'erp_ps_id', 'erp_do_id')
    def string_fields_50(cls, v):
        if v and len(v) > 50:
            raise ValueError('field must be at most 50 characters')
        return v

    @field_validator('status')
    def status_valid(cls, v):
        if v not in ['PENDING', 'PROCESSED', 'SHIPPED', 'COMPLETED']:
            raise ValueError('Invalid status')
        return v
        
class SalesOrderSchema(BaseSchema, TimestampMixin, StatusMixin, ERPMixin):
    """Schema untuk SalesOrder model"""
    so_number: str
    so_date: date
    
    customer_id: int
    
    tender_contract_id: Optional[int] = None
    
    packing_slip_id: Optional[int] = None
    
    total_quantity: int = 0
    total_value: Optional[Decimal] = None
    currency: str = 'IDR'
    
    requested_delivery_date: Optional[date] = None
    promised_delivery_date: Optional[date] = None
    delivery_instructions: Optional[str] = None
    
    priority_level: int = 5
    is_urgent: bool = False
    
    is_tender_so: bool = False
    requires_special_handling: bool = False
    
    status: str = 'PENDING'
    
    payment_terms_days: Optional[int] = None
    payment_method: Optional[str] = None
    
    notes: Optional[str] = None
    special_instructions: Optional[str] = None
    
    confirmed_by: Optional[str] = None
    confirmed_date: Optional[datetime] = None
    
    erp_so_id: Optional[str] = None
    
    so_type: Optional[str] = None
    total_items: Optional[int] = None
    completion_percentage: Optional[float] = None
    
    packing_slip: Optional[PackingSlipSchema] = None

    @field_validator('so_number')
    def validate_so_number_field(cls, v):
        return validate_so_number(v)

    @field_validator('customer_id', 'tender_contract_id', 'packing_slip_id')
    def id_fields_positive(cls, v):
        if v is not None and v < 1:
            raise ValueError('ID fields must be positive')
        return v

    @field_validator('total_quantity')
    def quantity_non_negative(cls, v):
        if v < 0:
            raise ValueError('total_quantity must be non-negative')
        return v

    @field_validator('total_value')
    def value_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError('total_value must be non-negative')
        return v

    @field_validator('currency')
    def currency_length(cls, v):
        if len(v) > 3:
            raise ValueError('currency must be at most 3 characters')
        return v

    @field_validator('priority_level')
    def priority_level_range(cls, v):
        if not 1 <= v <= 9:
            raise ValueError('priority_level must be between 1 and 9')
        return v

    @field_validator('status')
    def status_valid(cls, v):
        if v not in ['PENDING', 'CONFIRMED', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED']:
            raise ValueError('Invalid status')
        return v

    @field_validator('payment_terms_days')
    def payment_terms_range(cls, v):
        if v and not 1 <= v <= 365:
            raise ValueError('payment_terms_days must be between 1 and 365')
        return v

    @field_validator('payment_method', 'confirmed_by', 'erp_so_id')
    def string_fields_50(cls, v):
        if v and len(v) > 50:
            raise ValueError('field must be at most 50 characters')
        return v
        
    @model_validator(mode='after')
    def validate_so_dates(cls, values):
        """Validate SO date relationships"""
        so_date, requested_delivery, promised_delivery = values.get('so_date'), values.get('requested_delivery_date'), values.get('promised_delivery_date')
        
        if so_date and requested_delivery and so_date > requested_delivery:
            raise ValueError('SO date cannot be after requested delivery date')
        
        if requested_delivery and promised_delivery and promised_delivery < requested_delivery:
            raise ValueError('Promised delivery cannot be before requested delivery')
        return values

class SalesOrderItemSchema(BaseSchema):
    """Schema untuk SalesOrderItem model"""
    sales_order_id: int
    product_id: int
    
    line_number: int
    quantity_ordered: int
    quantity_shipped: int = 0
    quantity_cancelled: int = 0
    
    unit_price: Optional[Decimal] = None
    line_total: Optional[Decimal] = None
    discount_percent: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    
    requested_delivery_date: Optional[date] = None
    
    preferred_batch_id: Optional[int] = None
    min_expiry_date: Optional[date] = None
    
    notes: Optional[str] = None
    
    status: str = 'PENDING'
    
    quantity_remaining: Optional[int] = None
    completion_percentage: Optional[float] = None

    @field_validator('sales_order_id', 'product_id', 'line_number', 'preferred_batch_id')
    def id_fields_positive(cls, v):
        if v is not None and v < 1:
            raise ValueError('ID and line number fields must be positive')
        return v
        
    @field_validator('quantity_ordered')
    def ordered_quantity_positive(cls,v):
        if v <= 0:
            raise ValueError('ordered quantity must be a positive number')
        return v

    @field_validator('quantity_shipped', 'quantity_cancelled')
    def shipped_cancelled_non_negative(cls, v):
        if v < 0:
            raise ValueError('quantity shipped and cancelled must be non-negative')
        return v
    
    @field_validator('unit_price', 'line_total', 'discount_amount')
    def price_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError('price fields must be non-negative')
        return v

    @field_validator('discount_percent')
    def discount_percent_range(cls, v):
        if v is not None and not 0 <= v <= 100:
            raise ValueError('discount_percent must be between 0 and 100')
        return v

    @field_validator('status')
    def status_valid(cls, v):
        if v not in ['PENDING', 'CONFIRMED', 'SHIPPED', 'CANCELLED']:
            raise ValueError('Invalid status')
        return v

    @model_validator(mode='after')
    def validate_so_item_quantities(cls, values):
        """Validate SO item quantity business rules"""
        ordered, shipped, cancelled = values.get('quantity_ordered', 0), values.get('quantity_shipped', 0), values.get('quantity_cancelled', 0)
        
        if shipped + cancelled > ordered:
            raise ValueError('Shipped + Cancelled cannot exceed Ordered quantity')
        return values
        
class ShippingPlanSchema(BaseSchema, TimestampMixin):
    """Schema untuk ShippingPlan model"""
    sales_order_id: int
    plan_number: Optional[str] = None
    plan_date: date
    planned_delivery_date: date
    
    delivery_method: Optional[str] = None
    shipping_method: Optional[str] = None
    estimated_delivery_days: Optional[int] = None
    
    priority_level: int = 5
    is_express: bool = False
    
    status: str = 'PLANNED'
    
    notes: Optional[str] = None
    special_delivery_instructions: Optional[str] = None
    
    approved_by: Optional[str] = None
    approved_date: Optional[datetime] = None
    
    total_items: Optional[int] = None
    total_planned_quantity: Optional[int] = None
    
    @field_validator('sales_order_id')
    def sales_order_id_positive(cls,v):
        if v < 1:
            raise ValueError('sales_order_id must be a positive number')
        return v

    @field_validator('delivery_method', 'shipping_method', 'approved_by')
    def string_fields_50(cls, v):
        if v and len(v) > 50:
            raise ValueError('field must be at most 50 characters')
        return v

    @field_validator('estimated_delivery_days')
    def estimated_delivery_days_range(cls, v):
        if v and not 1 <= v <= 30:
            raise ValueError('estimated_delivery_days must be between 1 and 30')
        return v

    @field_validator('priority_level')
    def priority_level_range(cls, v):
        if not 1 <= v <= 9:
            raise ValueError('priority_level must be between 1 and 9')
        return v

    @field_validator('status')
    def status_valid(cls, v):
        if v not in ['PLANNED', 'APPROVED', 'PROCESSING', 'COMPLETED', 'CANCELLED']:
            raise ValueError('Invalid status')
        return v
        
    @model_validator(mode='after')
    def validate_shipping_plan_dates(cls, values):
        """Validate shipping plan dates"""
        plan_date, planned_delivery = values.get('plan_date'), values.get('planned_delivery_date')
        
        if plan_date and planned_delivery and plan_date > planned_delivery:
            raise ValueError('Plan date cannot be after planned delivery date')
        return values

class ShippingPlanItemSchema(BaseSchema):
    """Schema untuk ShippingPlanItem model"""
    shipping_plan_id: int
    sales_order_item_id: int
    product_id: int
    
    planned_quantity: int
    allocated_quantity: int = 0
    picked_quantity: int = 0
    
    allocation_type_preference: Optional[str] = None
    batch_selection_method: str = 'FIFO'
    
    notes: Optional[str] = None
    
    remaining_quantity: Optional[int] = None
    allocation_percentage: Optional[float] = None

    @field_validator('shipping_plan_id', 'sales_order_item_id', 'product_id')
    def id_fields_positive(cls,v):
        if v < 1:
            raise ValueError('ID fields must be a positive number')
        return v

    @field_validator('planned_quantity')
    def planned_quantity_positive(cls,v):
        if v <= 0:
            raise ValueError('planned quantity must be a positive number')
        return v
        
    @field_validator('allocated_quantity', 'picked_quantity')
    def non_negative_quantities(cls,v):
        if v < 0:
            raise ValueError('allocated and picked quantities must be non-negative')
        return v

    @field_validator('allocation_type_preference')
    def allocation_type_valid(cls, v):
        if v and v not in ['REG', 'TENDER']:
            raise ValueError('Invalid allocation_type_preference')
        return v

    @field_validator('batch_selection_method')
    def batch_selection_valid(cls, v):
        if v not in ['FIFO', 'FEFO', 'SPECIFIC']:
            raise ValueError('Invalid batch_selection_method')
        return v
        
    @model_validator(mode='after')
    def validate_shipping_plan_item_quantities(cls, values):
        """Validate shipping plan item quantities"""
        planned, allocated, picked = values.get('planned_quantity', 0), values.get('allocated_quantity', 0), values.get('picked_quantity', 0)
        
        if allocated > planned:
            raise ValueError('Allocated cannot exceed Planned quantity')
        
        if picked > allocated:
            raise ValueError('Picked cannot exceed Allocated quantity')
        return values

# Input schemas
class PackingSlipCreateSchema(PackingSlipSchema):
    class Config:
        exclude = ('id', 'public_id', 'created_date', 'created_by', 'erp_sync_date',
                  'total_sales_orders', 'total_picking_lists', 'total_quantity')

class PackingSlipUpdateSchema(PackingSlipSchema):
    ps_number: Optional[str]
    ps_date: Optional[date]
    
    class Config:
        exclude = ('id', 'public_id', 'created_date', 'created_by', 'erp_sync_date',
                  'total_sales_orders', 'total_picking_lists', 'total_quantity')

class SalesOrderCreateSchema(SalesOrderSchema):
    class Config:
        exclude = ('id', 'public_id', 'created_date', 'created_by', 'confirmed_by', 'confirmed_date',
                  'erp_sync_date', 'so_type', 'total_items', 'completion_percentage')

class SalesOrderUpdateSchema(SalesOrderSchema):
    so_number: Optional[str]
    so_date: Optional[date]
    customer_id: Optional[int]
    
    class Config:
        exclude = ('id', 'public_id', 'created_date', 'created_by', 'confirmed_by', 'confirmed_date',
                  'erp_sync_date', 'so_type', 'total_items', 'completion_percentage')

class SalesOrderItemCreateSchema(SalesOrderItemSchema):
    class Config:
        exclude = ('id', 'quantity_remaining', 'completion_percentage')

class SalesOrderItemUpdateSchema(SalesOrderItemSchema):
    sales_order_id: Optional[int]
    product_id: Optional[int]
    line_number: Optional[int]
    quantity_ordered: Optional[int]
    
    class Config:
        exclude = ('id', 'quantity_remaining', 'completion_percentage')

class ShippingPlanCreateSchema(ShippingPlanSchema):
    class Config:
        exclude = ('id', 'public_id', 'plan_number', 'created_date', 'created_by',
                  'approved_by', 'approved_date', 'total_items', 'total_planned_quantity')

class ShippingPlanUpdateSchema(ShippingPlanSchema):
    sales_order_id: Optional[int]
    plan_date: Optional[date]
    planned_delivery_date: Optional[date]
    
    class Config:
        exclude = ('id', 'public_id', 'plan_number', 'created_date', 'created_by',
                  'approved_by', 'approved_date', 'total_items', 'total_planned_quantity')

class ShippingPlanItemCreateSchema(ShippingPlanItemSchema):
    class Config:
        exclude = ('id', 'remaining_quantity', 'allocation_percentage')

class ShippingPlanItemUpdateSchema(ShippingPlanItemSchema):
    shipping_plan_id: Optional[int]
    sales_order_item_id: Optional[int]
    product_id: Optional[int]
    planned_quantity: Optional[int]
    
    class Config:
        exclude = ('id', 'remaining_quantity', 'allocation_percentage')