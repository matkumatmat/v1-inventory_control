from pydantic import BaseModel, Field
from typing import Optional

class CustomerTypeBase(BaseModel):
    code: str = Field(max_length=10)
    name: str = Field(max_length=50)
    description: Optional[str] = None
    is_active: bool = True
    allows_tender_allocation: bool = False
    requires_pre_approval: bool = False
    default_credit_limit: Optional[float] = None
    default_discount_percent: Optional[float] = None
    default_payment_terms_days: int = 30

class CustomerTypeCreateSchema(CustomerTypeBase):
    pass

class CustomerTypeUpdateSchema(BaseModel):
    code: Optional[str] = Field(None, max_length=10)
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    allows_tender_allocation: Optional[bool] = None
    requires_pre_approval: Optional[bool] = None
    default_credit_limit: Optional[float] = None
    default_discount_percent: Optional[float] = None
    default_payment_terms_days: Optional[int] = None

class CustomerTypeSchema(CustomerTypeBase):
    id: int

    class Config:
        orm_mode = True
