from pydantic import BaseModel, Field
from typing import Optional

class ShippingMethodBase(BaseModel):
    code: str = Field(max_length=10)
    name: str = Field(max_length=50)
    description: Optional[str] = None
    is_active: bool = True
    estimated_delivery_days: int
    max_weight_kg: Optional[float] = None
    max_dimensions_cm: Optional[str] = Field(None, max_length=20)
    base_cost: Optional[float] = None
    cost_per_kg: Optional[float] = None
    cost_per_km: Optional[float] = None
    fuel_surcharge_percent: Optional[float] = None
    includes_insurance: bool = False
    includes_tracking: bool = True
    requires_signature: bool = False
    supports_cod: bool = False

class ShippingMethodCreateSchema(ShippingMethodBase):
    pass

class ShippingMethodUpdateSchema(BaseModel):
    code: Optional[str] = Field(None, max_length=10)
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    estimated_delivery_days: Optional[int] = None
    max_weight_kg: Optional[float] = None
    max_dimensions_cm: Optional[str] = Field(None, max_length=20)
    base_cost: Optional[float] = None
    cost_per_kg: Optional[float] = None
    cost_per_km: Optional[float] = None
    fuel_surcharge_percent: Optional[float] = None
    includes_insurance: Optional[bool] = None
    includes_tracking: Optional[bool] = None
    requires_signature: Optional[bool] = None
    supports_cod: Optional[bool] = None

class ShippingMethodSchema(ShippingMethodBase):
    id: int

    class Config:
        orm_mode = True
