from pydantic import BaseModel, Field
from typing import Optional

class ProductTypeBase(BaseModel):
    code: str = Field(max_length=10)
    name: str = Field(max_length=50)
    description: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0
    requires_batch_tracking: bool = True
    requires_expiry_tracking: bool = True
    shelf_life_days: Optional[int] = None

class ProductTypeCreateSchema(ProductTypeBase):
    pass

class ProductTypeUpdateSchema(BaseModel):
    code: Optional[str] = Field(None, max_length=10)
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    requires_batch_tracking: Optional[bool] = None
    requires_expiry_tracking: Optional[bool] = None
    shelf_life_days: Optional[int] = None

class ProductTypeSchema(ProductTypeBase):
    id: int

    class Config:
        orm_mode = True
