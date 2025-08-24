from pydantic import BaseModel, Field
from typing import Optional

class PackageTypeBase(BaseModel):
    code: str = Field(max_length=10)
    name: str = Field(max_length=50)
    description: Optional[str] = None
    is_active: bool = True
    is_fragile: bool = False
    is_stackable: bool = True
    max_stack_height: Optional[int] = None
    standard_length: Optional[float] = None
    standard_width: Optional[float] = None
    standard_height: Optional[float] = None
    standard_weight: Optional[float] = None
    special_handling_required: bool = False
    handling_instructions: Optional[str] = None

class PackageTypeCreateSchema(PackageTypeBase):
    pass

class PackageTypeUpdateSchema(BaseModel):
    code: Optional[str] = Field(None, max_length=10)
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_fragile: Optional[bool] = None
    is_stackable: Optional[bool] = None
    max_stack_height: Optional[int] = None
    standard_length: Optional[float] = None
    standard_width: Optional[float] = None
    standard_height: Optional[float] = None
    standard_weight: Optional[float] = None
    special_handling_required: Optional[bool] = None
    handling_instructions: Optional[str] = None

class PackageTypeSchema(PackageTypeBase):
    id: int

    class Config:
        orm_mode = True
