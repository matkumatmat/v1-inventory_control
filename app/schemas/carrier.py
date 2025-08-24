from pydantic import BaseModel, Field
from typing import Optional

class CarrierBase(BaseModel):
    name: str
    code: str = Field(max_length=10)
    contact_info: Optional[str] = None
    carrier_type_id: int
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    is_active: bool = True

class CarrierCreateSchema(CarrierBase):
    pass

class CarrierUpdateSchema(BaseModel):
    name: Optional[str] = None
    contact_info: Optional[str] = None
    carrier_type_id: Optional[int] = None
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    is_active: Optional[bool] = None

class CarrierSchema(CarrierBase):
    id: int

    class Config:
        orm_mode = True
