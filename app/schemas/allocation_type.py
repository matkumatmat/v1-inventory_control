from pydantic import BaseModel, Field
from typing import Optional

class AllocationTypeBase(BaseModel):
    code: str = Field(max_length=10)
    name: str = Field(max_length=50)
    description: Optional[str] = None
    is_active: bool = True
    requires_customer: bool = False
    is_reservable: bool = True
    auto_assign_customer: bool = False
    priority_level: int = 1
    max_allocation_days: Optional[int] = None
    color_code: Optional[str] = Field(None, max_length=7)
    icon: Optional[str] = Field(None, max_length=50)

class AllocationTypeCreateSchema(AllocationTypeBase):
    pass

class AllocationTypeUpdateSchema(BaseModel):
    code: Optional[str] = Field(None, max_length=10)
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    requires_customer: Optional[bool] = None
    is_reservable: Optional[bool] = None
    auto_assign_customer: Optional[bool] = None
    priority_level: Optional[int] = None
    max_allocation_days: Optional[int] = None
    color_code: Optional[str] = Field(None, max_length=7)
    icon: Optional[str] = Field(None, max_length=50)

class AllocationTypeSchema(AllocationTypeBase):
    id: int

    class Config:
        orm_mode = True
