from pydantic import BaseModel, Field
from typing import Optional

class LocationTypeBase(BaseModel):
    code: str = Field(max_length=10)
    name: str = Field(max_length=50)
    description: Optional[str] = None
    is_active: bool = True
    is_storage_location: bool = True
    is_picking_location: bool = True
    is_staging_location: bool = False
    max_weight_capacity_kg: Optional[float] = None
    supports_temperature_control: bool = False
    requires_special_access: bool = False

class LocationTypeCreateSchema(LocationTypeBase):
    pass

class LocationTypeUpdateSchema(BaseModel):
    code: Optional[str] = Field(None, max_length=10)
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_storage_location: Optional[bool] = None
    is_picking_location: Optional[bool] = None
    is_staging_location: Optional[bool] = None
    max_weight_capacity_kg: Optional[float] = None
    supports_temperature_control: Optional[bool] = None
    requires_special_access: Optional[bool] = None

class LocationTypeSchema(LocationTypeBase):
    id: int

    class Config:
        orm_mode = True
