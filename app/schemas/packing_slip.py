from pydantic import BaseModel
from typing import Optional
from datetime import date

# Based on the PackingSlipService, not the model, to satisfy the route's dependencies.

class PackingSlipBase(BaseModel):
    ps_number: Optional[str] = None
    ps_date: date
    delivery_address: Optional[str] = None
    notes: Optional[str] = None
    status: str = "DRAFT"

class PackingSlipCreateSchema(PackingSlipBase):
    sales_order_id: int

class PackingSlipUpdateSchema(BaseModel):
    delivery_address: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None

class PackingSlipSchema(PackingSlipBase):
    id: int
    customer_id: int
    sales_order_id: int
    finalized_by: Optional[str] = None
    finalized_date: Optional[date] = None

    class Config:
        orm_mode = True
