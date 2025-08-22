"""
Consignment Domain Schemas
==========================

Schemas untuk Consignment, ConsignmentSale, ConsignmentReturn, dll
"""

from pydantic import BaseModel, field_validator,model_validator 
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from .base import BaseSchema, TimestampMixin
from .validators import validate_percentage

class ConsignmentAgreementSchema(BaseSchema, TimestampMixin):
    """Schema untuk ConsignmentAgreement model"""
    agreement_number: str
    customer_id: int
    
    agreement_date: date
    start_date: date
    end_date: Optional[date] = None
    
    commission_rate: Optional[Decimal] = None
    payment_terms_days: int = 30
    return_policy_days: int = 90
    
    status: str = 'ACTIVE'
    
    contract_document_url: Optional[str] = None
    terms_document_url: Optional[str] = None
    
    approved_by: Optional[str] = None
    approved_date: Optional[datetime] = None
    
    is_active: Optional[bool] = None
    days_remaining: Optional[int] = None

    @field_validator('agreement_number')
    def agreement_number_length(cls,v):
        if not 3 <= len(v) <= 50:
            raise ValueError('agreement number must be between 3 and 50 chars')
        return v
        
    @field_validator('customer_id')
    def customer_id_positive(cls,v):
        if v < 1:
            raise ValueError("customer_id must be a positive number")
        return v
        
    @field_validator('commission_rate')
    def validate_commission_rate(cls, v):
        if v is not None:
            return validate_percentage(v)
        return v

    @field_validator('payment_terms_days', 'return_policy_days')
    def days_range(cls, v):
        if not 1 <= v <= 365:
            raise ValueError('days must be between 1 and 365')
        return v

    @field_validator('status')
    def status_valid(cls, v):
        if v not in ['ACTIVE', 'SUSPENDED', 'TERMINATED', 'EXPIRED']:
            raise ValueError('Invalid status')
        return v

    @field_validator('approved_by')
    def approved_by_length(cls,v):
        if v and len(v) > 50:
            raise ValueError('approved_by must be at most 50 characters')
        return v
        
    @model_validator(mode='after')
    def validate_agreement_dates(cls, values):
        """Validate agreement date relationships"""
        agreement_date, start_date, end_date = values.get('agreement_date'), values.get('start_date'), values.get('end_date')
        
        if agreement_date and start_date and agreement_date > start_date:
            raise ValueError('Agreement date cannot be after start date')
        
        if start_date and end_date and start_date >= end_date:
            raise ValueError('Start date must be before end date')
        return values

class ConsignmentSchema(BaseSchema, TimestampMixin):
    """Schema untuk Consignment model"""
    consignment_number: Optional[str] = None
    
    agreement_id: int
    
    allocation_id: int
    
    shipment_id: Optional[int] = None
    
    consignment_date: date
    expected_return_date: Optional[date] = None
    actual_return_date: Optional[date] = None
    
    total_value: Optional[Decimal] = None
    commission_rate: Optional[Decimal] = None
    
    status: str = 'PENDING'
    
    notes: Optional[str] = None
    terms_conditions: Optional[str] = None
    
    shipped_by: Optional[str] = None
    shipped_date: Optional[datetime] = None
    
    total_quantity_shipped: Optional[int] = None
    total_quantity_sold: Optional[int] = None
    total_quantity_returned: Optional[int] = None
    sales_percentage: Optional[float] = None
    total_commission_earned: Optional[Decimal] = None
    
    agreement: Optional[ConsignmentAgreementSchema] = None

    @field_validator('agreement_id', 'allocation_id', 'shipment_id')
    def id_fields_positive(cls,v):
        if v is not None and v < 1:
            raise ValueError('ID fields must be a positive number')
        return v

    @field_validator('total_value')
    def value_non_negative(cls,v):
        if v is not None and v < 0:
            raise ValueError('total value must be non-negative')
        return v

    @field_validator('commission_rate')
    def validate_commission_rate(cls, v):
        if v is not None:
            return validate_percentage(v)
        return v

    @field_validator('status')
    def status_valid(cls, v):
        if v not in ['PENDING', 'SHIPPED', 'RECEIVED_BY_CUSTOMER', 'PARTIALLY_SOLD', 'FULLY_SOLD', 'RETURNED', 'CANCELLED']:
            raise ValueError('Invalid status')
        return v

    @field_validator('shipped_by')
    def shipped_by_length(cls,v):
        if v and len(v) > 50:
            raise ValueError("shipped by must be max 50 chars")
        return v
        
class ConsignmentItemSchema(BaseSchema):
    """Schema untuk ConsignmentItem model"""
    consignment_id: int
    product_id: int
    batch_id: int
    
    quantity_shipped: int
    quantity_sold: int = 0
    quantity_returned: int = 0
    
    unit_value: Optional[Decimal] = None
    total_value: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    
    status: str = 'SHIPPED'
    
    expiry_date: Optional[date] = None
    lot_number: Optional[str] = None
    
    notes: Optional[str] = None
    
    quantity_remaining: Optional[int] = None
    sales_percentage: Optional[float] = None

    @field_validator('consignment_id', 'product_id', 'batch_id')
    def id_fields_positive(cls,v):
        if v < 1:
            raise ValueError("ID fields must be positive")
        return v
        
    @field_validator('quantity_shipped')
    def shipped_quantity_positive(cls, v):
        if v <= 0:
            raise ValueError("quantity shipped must be a positive number")
        return v
        
    @field_validator('quantity_sold', 'quantity_returned')
    def non_negative_quantities(cls,v):
        if v < 0:
            raise ValueError('sold and returned quantities must be non-negative')
        return v

    @field_validator('unit_value', 'total_value', 'selling_price')
    def value_non_negative(cls,v):
        if v is not None and v < 0:
            raise ValueError('value fields must be non-negative')
        return v

    @field_validator('status')
    def status_valid(cls, v):
        if v not in ['SHIPPED', 'PARTIALLY_SOLD', 'SOLD', 'RETURNED']:
            raise ValueError('Invalid status')
        return v

    @field_validator('lot_number')
    def lot_number_length(cls,v):
        if v and len(v) > 50:
            raise ValueError('lot number must be at most 50 characters')
        return v
        
    @model_validator(mode='after')
    def validate_consignment_item_quantities(cls, values):
        """Validate consignment item quantities"""
        shipped, sold, returned = values.get('quantity_shipped', 0), values.get('quantity_sold', 0), values.get('quantity_returned', 0)
        
        if sold + returned > shipped:
            raise ValueError('Sold + Returned cannot exceed Shipped quantity')
        return values

class ConsignmentSaleSchema(BaseSchema, TimestampMixin):
    """Schema untuk ConsignmentSale model"""
    sale_number: Optional[str] = None
    consignment_id: int
    consignment_item_id: int
    
    sale_date: date
    quantity_sold: int
    unit_price: Decimal
    total_value: Decimal
    
    commission_rate: Optional[Decimal] = None
    commission_amount: Optional[Decimal] = None
    net_amount: Optional[Decimal] = None
    
    end_customer_name: Optional[str] = None
    end_customer_info: Optional[str] = None
    
    invoice_number: Optional[str] = None
    receipt_document_url: Optional[str] = None
    
    status: str = 'CONFIRMED'
    
    reported_by: Optional[str] = None
    reported_date: Optional[datetime] = None
    verified_by: Optional[str] = None
    verified_date: Optional[datetime] = None

    @field_validator('consignment_id', 'consignment_item_id')
    def id_fields_positive(cls,v):
        if v < 1:
            raise ValueError('ID fields must be positive')
        return v
        
    @field_validator('quantity_sold')
    def sold_quantity_positive(cls, v):
        if v <= 0:
            raise ValueError('quantity sold must be positive')
        return v

    @field_validator('unit_price', 'total_value', 'commission_amount', 'net_amount')
    def value_non_negative(cls,v):
        if v is not None and v < 0:
            raise ValueError('value fields must be non-negative')
        return v
        
    @field_validator('commission_rate')
    def validate_commission_rate(cls, v):
        if v is not None:
            return validate_percentage(v)
        return v

    @field_validator('end_customer_name')
    def customer_name_length(cls,v):
        if v and len(v) > 100:
            raise ValueError("customer name must be max 100 chars")
        return v
        
    @field_validator('invoice_number', 'reported_by', 'verified_by')
    def string_fields_50(cls,v):
        if v and len(v) > 50:
            raise ValueError('field must be at most 50 characters')
        return v

    @field_validator('status')
    def status_valid(cls, v):
        if v not in ['PENDING', 'CONFIRMED', 'PAID', 'CANCELLED']:
            raise ValueError('Invalid status')
        return v

class ConsignmentReturnSchema(BaseSchema, TimestampMixin):
    """Schema untuk ConsignmentReturn model"""
    return_number: Optional[str] = None
    consignment_id: int
    consignment_item_id: int
    
    return_date: date
    quantity_returned: int
    
    return_reason: Optional[str] = None
    condition: Optional[str] = None
    
    qc_status: Optional[str] = None
    qc_notes: Optional[str] = None
    qc_by: Optional[str] = None
    qc_date: Optional[datetime] = None
    
    disposition: Optional[str] = None
    restocked_quantity: int = 0
    disposed_quantity: int = 0
    
    return_document_url: Optional[str] = None
    photos_url: Optional[str] = None
    
    status: str = 'PENDING'
    
    initiated_by: Optional[str] = None
    received_by: Optional[str] = None
    received_date: Optional[datetime] = None
    
    notes: Optional[str] = None

    @field_validator('consignment_id', 'consignment_item_id')
    def id_fields_positive(cls, v):
        if v < 1:
            raise ValueError("ID fields must be positive")
        return v
        
    @field_validator('quantity_returned')
    def quantity_returned_positive(cls,v):
        if v <= 0:
            raise ValueError('quantity returned must be a positive number')
        return v
        
    @field_validator('return_reason')
    def reason_valid(cls, v):
        if v and v not in ['EXPIRED', 'DAMAGED', 'UNSOLD', 'RECALL']:
            raise ValueError('Invalid return_reason')
        return v
        
    @field_validator('condition')
    def condition_valid(cls, v):
        if v and v not in ['GOOD', 'DAMAGED', 'EXPIRED']:
            raise ValueError('Invalid condition')
        return v
        
    @field_validator('qc_status')
    def qc_status_valid(cls, v):
        if v and v not in ['PENDING', 'PASSED', 'FAILED']:
            raise ValueError('Invalid qc_status')
        return v
        
    @field_validator('qc_by', 'initiated_by', 'received_by')
    def user_fields_length(cls,v):
        if v and len(v) > 50:
            raise ValueError('user fields must be at most 50 characters')
        return v

    @field_validator('disposition')
    def disposition_valid(cls, v):
        if v and v not in ['RESTOCK', 'QUARANTINE', 'DISPOSE', 'REWORK']:
            raise ValueError('Invalid disposition')
        return v
        
    @field_validator('restocked_quantity', 'disposed_quantity')
    def quantity_non_negative(cls,v):
        if v < 0:
            raise ValueError('quantities must be non-negative')
        return v

    @field_validator('status')
    def status_valid(cls, v):
        if v not in ['PENDING', 'RECEIVED', 'QC_DONE', 'PROCESSED']:
            raise ValueError('Invalid status')
        return v

    @model_validator(mode='after')
    def validate_return_quantities(cls, values):
        """Validate return quantities"""
        returned, restocked, disposed = values.get('quantity_returned', 0), values.get('restocked_quantity', 0), values.get('disposed_quantity', 0)
        
        if restocked + disposed > returned:
            raise ValueError('Restocked + Disposed cannot exceed Returned quantity')
        return values

class ConsignmentStatementSchema(BaseSchema, TimestampMixin):
    """Schema untuk ConsignmentStatement model"""
    statement_number: Optional[str] = None
    agreement_id: int
    customer_id: int
    
    period_start: date
    period_end: date
    
    total_shipped_value: Optional[Decimal] = None
    total_sold_value: Optional[Decimal] = None
    total_returned_value: Optional[Decimal] = None
    total_commission: Optional[Decimal] = None
    net_amount_due: Optional[Decimal] = None
    
    payment_status: str = 'PENDING'
    payment_due_date: Optional[date] = None
    payment_received_date: Optional[date] = None
    payment_amount: Optional[Decimal] = None
    
    statement_document_url: Optional[str] = None
    
    status: str = 'DRAFT'
    
    generated_by: Optional[str] = None
    sent_date: Optional[datetime] = None
    
    @field_validator('agreement_id', 'customer_id')
    def id_fields_positive(cls,v):
        if v < 1:
            raise ValueError("ID fields must be positive")
        return v

    @field_validator('total_shipped_value', 'total_sold_value', 'total_returned_value', 'total_commission', 'net_amount_due', 'payment_amount')
    def value_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError('value fields must be non-negative')
        return v
        
    @field_validator('payment_status')
    def payment_status_valid(cls, v):
        if v not in ['PENDING', 'PARTIAL', 'PAID', 'OVERDUE']:
            raise ValueError('Invalid payment_status')
        return v

    @field_validator('status')
    def status_valid(cls, v):
        if v not in ['DRAFT', 'SENT', 'CONFIRMED', 'PAID']:
            raise ValueError('Invalid status')
        return v

    @field_validator('generated_by')
    def generated_by_length(cls,v):
        if v and len(v) > 50:
            raise ValueError('generated_by must be at most 50 characters')
        return v

    @model_validator(mode='after')
    def validate_statement_dates(cls, values):
        """Validate statement period dates"""
        start_date, end_date = values.get('period_start'), values.get('period_end')
        
        if start_date and end_date and start_date >= end_date:
            raise ValueError('Period start must be before period end')
        return values
        
# Input schemas
class ConsignmentAgreementCreateSchema(ConsignmentAgreementSchema):
    class Config:
        exclude = ('id', 'public_id', 'created_date', 'created_by', 'approved_by', 'approved_date',
                  'is_active', 'days_remaining')

class ConsignmentAgreementUpdateSchema(ConsignmentAgreementSchema):
    agreement_number: Optional[str]
    customer_id: Optional[int]
    agreement_date: Optional[date]
    start_date: Optional[date]
    
    class Config:
        exclude = ('id', 'public_id', 'created_date', 'created_by', 'approved_by', 'approved_date',
                  'is_active', 'days_remaining')

class ConsignmentCreateSchema(ConsignmentSchema):
    class Config:
        exclude = ('id', 'public_id', 'consignment_number', 'created_date', 'created_by',
                  'shipped_by', 'shipped_date', 'total_quantity_shipped', 'total_quantity_sold',
                  'total_quantity_returned', 'sales_percentage', 'total_commission_earned')

class ConsignmentUpdateSchema(ConsignmentSchema):
    agreement_id: Optional[int]
    allocation_id: Optional[int]
    consignment_date: Optional[date]
    
    class Config:
        exclude = ('id', 'public_id', 'consignment_number', 'created_date', 'created_by',
                  'shipped_by', 'shipped_date', 'total_quantity_shipped', 'total_quantity_sold',
                  'total_quantity_returned', 'sales_percentage', 'total_commission_earned')

class ConsignmentItemCreateSchema(ConsignmentItemSchema):
    class Config:
        exclude = ('id', 'quantity_remaining', 'sales_percentage')

class ConsignmentItemUpdateSchema(ConsignmentItemSchema):
    consignment_id: Optional[int]
    product_id: Optional[int]
    batch_id: Optional[int]
    quantity_shipped: Optional[int]
    
    class Config:
        exclude = ('id', 'quantity_remaining', 'sales_percentage')

class ConsignmentSaleCreateSchema(ConsignmentSaleSchema):
    class Config:
        exclude = ('id', 'public_id', 'sale_number', 'created_date', 'reported_by', 'reported_date',
                  'verified_by', 'verified_date')

class ConsignmentSaleUpdateSchema(ConsignmentSaleSchema):
    consignment_id: Optional[int]
    consignment_item_id: Optional[int]
    sale_date: Optional[date]
    quantity_sold: Optional[int]
    unit_price: Optional[Decimal]
    total_value: Optional[Decimal]
    
    class Config:
        exclude = ('id', 'public_id', 'sale_number', 'created_date', 'reported_by', 'reported_date',
                  'verified_by', 'verified_date')

class ConsignmentReturnCreateSchema(ConsignmentReturnSchema):
    class Config:
        exclude = ('id', 'public_id', 'return_number', 'created_date', 'initiated_by',
                  'received_by', 'received_date')

class ConsignmentReturnUpdateSchema(ConsignmentReturnSchema):
    consignment_id: Optional[int]
    consignment_item_id: Optional[int]
    return_date: Optional[date]
    quantity_returned: Optional[int]
    
    class Config:
        exclude = ('id', 'public_id', 'return_number', 'created_date', 'initiated_by',
                  'received_by', 'received_date')

class ConsignmentStatementCreateSchema(ConsignmentStatementSchema):
    class Config:
        exclude = ('id', 'public_id', 'statement_number', 'created_date', 'generated_by', 'sent_date')

class ConsignmentStatementUpdateSchema(ConsignmentStatementSchema):
    agreement_id: Optional[int]
    customer_id: Optional[int]
    period_start: Optional[date]
    period_end: Optional[date]
    
    class Config:
        exclude = ('id', 'public_id', 'statement_number', 'created_date', 'generated_by', 'sent_date')