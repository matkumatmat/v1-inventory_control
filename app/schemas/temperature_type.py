from pydantic import BaseModel, Field
from typing import Optional

class TemperatureTypeBase(BaseModel):
    code: str = Field(max_length=10)
    name: str = Field(max_length=50)
    description: Optional[str] = None
    is_active: bool = True
    min_celsius: Optional[float] = None
    max_celsius: Optional[float] = None
    optimal_celsius: Optional[float] = None
    celsius_display: Optional[str] = Field(None, max_length=20)
    humidity_range: Optional[str] = Field(None, max_length=20)
    special_storage_requirements: Optional[str] = None
    color_code: Optional[str] = Field(None, max_length=7)
    icon: Optional[str] = Field(None, max_length=50)

class TemperatureTypeCreateSchema(TemperatureTypeBase):
    pass

class TemperatureTypeUpdateSchema(BaseModel):
    code: Optional[str] = Field(None, max_length=10)
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    min_celsius: Optional[float] = None
    max_celsius: Optional[float] = None
    optimal_celsius: Optional[float] = None
    celsius_display: Optional[str] = Field(None, max_length=20)
    humidity_range: Optional[str] = Field(None, max_length=20)
    special_storage_requirements: Optional[str] = None
    color_code: Optional[str] = Field(None, max_length=7)
    icon: Optional[str] = Field(None, max_length=50)

class TemperatureTypeSchema(TemperatureTypeBase):
    id: int

    class Config:
        orm_mode = True
