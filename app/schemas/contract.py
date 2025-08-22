"""
Contract Domain Schemas
=======================

Schemas untuk TenderContract dan ContractReservation
"""

from pydantic import BaseModel, model_validator, field_validator
from typing import Optional
from datetime import date
from decimal import Decimal
from .base import BaseSchema, TimestampMixin, ERPMixin
from .validators import validate_contract_number

class TenderContractSchema(BaseSchema, TimestampMixin, ERPMixin):
    """Schema untuk TenderContract model"""
    contract_number: str
    contract_date: date
    contract_value: Optional[Decimal] = None
    
    start_date: date
    end_date: date
    
    tender_reference: Optional[str] = None
    tender_winner: Optional[str] = None
    
    status: str = 'ACTIVE'
    
    erp_contract_id: Optional[str] = None
    
    contract_document_url: Optional[str] = None
    
    is_active: Optional[bool] = None
    remaining_days: Optional[int] = None
    total_reserved_value: Optional[Decimal] = None

    @field_validator('contract_number')
    def validate_contract_number_field(cls, v):
        return validate_contract_number(v)

    @field_validator('contract_value')
    def value_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError('contract_value must be non-negative')
        return v

    @field_validator('tender_reference', 'tender_winner')
    def tender_info_length(cls, v):
        if v and len(v) > 100:
            raise ValueError('Tender info must be at most 100 characters')
        return v

    @field_validator('status')
    def status_valid(cls, v):
        if v not in ['ACTIVE', 'COMPLETED', 'CANCELLED', 'SUSPENDED']:
            raise ValueError('Invalid status')
        return v
        
    @field_validator('erp_contract_id')
    def erp_id_length(cls, v):
        if v and len(v) > 50:
            raise ValueError('erp_contract_id must be at most 50 characters')
        return v

    @model_validator(mode='after')
    def validate_contract_dates(cls, values):
        """Validate contract date relationships"""
        start_date, end_date, contract_date = values.get('start_date'), values.get('end_date'), values.get('contract_date')
        
        if start_date and end_date and start_date >= end_date:
            raise ValueError('Start date must be before end date')
        
        if contract_date and start_date and contract_date > start_date:
            raise ValueError('Contract date cannot be after start date')
        return values

class ContractReservationSchema(BaseSchema):
    """Schema untuk ContractReservation model"""
    contract_id: int
    product_id: int
    batch_id: int
    allocation_id: int
    
    reserved_quantity: int
    allocated_quantity: int = 0
    remaining_quantity: int
    
    available_for_allocation: Optional[int] = None
    allocation_percentage: Optional[float] = None
    
    contract: Optional[TenderContractSchema] = None

    @field_validator('contract_id', 'product_id', 'batch_id', 'allocation_id')
    def id_fields_positive(cls, v):
        if v < 1:
            raise ValueError('ID fields must be positive')
        return v

    @field_validator('reserved_quantity')
    def reserved_quantity_positive(cls, v):
        if v <= 0:
            raise ValueError('reserved_quantity must be positive')
        return v

    @field_validator('allocated_quantity', 'remaining_quantity')
    def quantity_non_negative(cls, v):
        if v < 0:
            raise ValueError('Quantities must be non-negative')
        return v

    @model_validator(mode='after')
    def validate_reservation_quantities(cls, values):
        """Validate reservation quantity business rules"""
        reserved = values.get('reserved_quantity', 0)
        allocated = values.get('allocated_quantity', 0)
        remaining = values.get('remaining_quantity', 0)
        
        if allocated > reserved:
            raise ValueError('Allocated quantity cannot exceed reserved quantity')
        
        if remaining != (reserved - allocated):
            raise ValueError('Remaining quantity must equal reserved minus allocated')
        return values

# Input schemas
class TenderContractCreateSchema(TenderContractSchema):
    class Config:
        exclude = ('id', 'public_id', 'created_date', 'created_by', 'erp_sync_date',
                  'is_active', 'remaining_days', 'total_reserved_value')

class TenderContractUpdateSchema(TenderContractSchema):
    contract_number: Optional[str]
    contract_date: Optional[date]
    start_date: Optional[date]
    end_date: Optional[date]
    
    class Config:
        exclude = ('id', 'public_id', 'created_date', 'created_by', 'erp_sync_date',
                  'is_active', 'remaining_days', 'total_reserved_value')

class ContractReservationCreateSchema(ContractReservationSchema):
    class Config:
        exclude = ('id', 'created_date', 'available_for_allocation', 'allocation_percentage')

class ContractReservationUpdateSchema(ContractReservationSchema):
    contract_id: Optional[int]
    product_id: Optional[int]
    batch_id: Optional[int]
    allocation_id: Optional[int]
    reserved_quantity: Optional[int]
    remaining_quantity: Optional[int]
    
    class Config:
        exclude = ('id', 'created_date', 'available_for_allocation', 'allocation_percentage')
