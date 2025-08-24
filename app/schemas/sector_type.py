from pydantic import BaseModel, Field
from typing import Optional

class SectorTypeBase(BaseModel):
    code: str = Field(max_length=10)
    name: str = Field(max_length=50)
    description: Optional[str] = None
    is_active: bool = True
    requires_special_handling: bool = False
    default_payment_terms: Optional[int] = None
    default_delivery_terms: Optional[str] = Field(None, max_length=50)
    requires_temperature_monitoring: bool = False
    requires_chain_of_custody: bool = False
    special_documentation: Optional[str] = None

class SectorTypeCreateSchema(SectorTypeBase):
    pass

class SectorTypeUpdateSchema(BaseModel):
    code: Optional[str] = Field(None, max_length=10)
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    requires_special_handling: Optional[bool] = None
    default_payment_terms: Optional[int] = None
    default_delivery_terms: Optional[str] = Field(None, max_length=50)
    requires_temperature_monitoring: Optional[bool] = None
    requires_chain_of_custody: Optional[bool] = None
    special_documentation: Optional[str] = None

class SectorTypeSchema(SectorTypeBase):
    id: int

    class Config:
        orm_mode = True
