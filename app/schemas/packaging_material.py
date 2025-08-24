from pydantic import BaseModel, Field
from typing import Optional

class PackagingMaterialBase(BaseModel):
    code: str = Field(max_length=10)
    name: str = Field(max_length=50)
    description: Optional[str] = None
    is_active: bool = True
    material_type: Optional[str] = Field(None, max_length=20)
    is_reusable: bool = False
    is_fragile_protection: bool = False
    is_temperature_protection: bool = False
    length_cm: Optional[float] = None
    width_cm: Optional[float] = None
    height_cm: Optional[float] = None
    weight_g: Optional[float] = None
    cost_per_unit: Optional[float] = None

class PackagingMaterialCreateSchema(PackagingMaterialBase):
    pass

class PackagingMaterialUpdateSchema(BaseModel):
    code: Optional[str] = Field(None, max_length=10)
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    material_type: Optional[str] = Field(None, max_length=20)
    is_reusable: Optional[bool] = None
    is_fragile_protection: Optional[bool] = None
    is_temperature_protection: Optional[bool] = None
    length_cm: Optional[float] = None
    width_cm: Optional[float] = None
    height_cm: Optional[float] = None
    weight_g: Optional[float] = None
    cost_per_unit: Optional[float] = None

class PackagingMaterialSchema(PackagingMaterialBase):
    id: int

    class Config:
        orm_mode = True
