from pydantic import BaseModel, Field
from typing import Optional

class CarrierTypeBase(BaseModel):
    code: str = Field(max_length=10)
    name: str = Field(max_length=50)
    description: Optional[str] = None
    is_active: bool = True
    has_api_integration: bool = False
    api_type: Optional[str] = Field(None, max_length=20)
    supports_real_time_tracking: bool = False
    supports_same_day: bool = False
    supports_next_day: bool = False
    supports_international: bool = False
    supports_temperature_controlled: bool = False

class CarrierTypeCreateSchema(CarrierTypeBase):
    pass

class CarrierTypeUpdateSchema(BaseModel):
    code: Optional[str] = Field(None, max_length=10)
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    has_api_integration: Optional[bool] = None
    api_type: Optional[str] = Field(None, max_length=20)
    supports_real_time_tracking: Optional[bool] = None
    supports_same_day: Optional[bool] = None
    supports_next_day: Optional[bool] = None
    supports_international: Optional[bool] = None
    supports_temperature_controlled: Optional[bool] = None

class CarrierTypeSchema(CarrierTypeBase):
    id: int

    class Config:
        orm_mode = True
