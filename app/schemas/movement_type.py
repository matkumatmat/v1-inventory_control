from pydantic import BaseModel, Field
from typing import Optional

class MovementTypeBase(BaseModel):
    code: str = Field(max_length=10)
    name: str = Field(max_length=50)
    description: Optional[str] = None
    is_active: bool = True
    direction: str = Field(max_length=10)
    affects_stock: bool = True
    auto_generate_document: bool = False
    document_prefix: Optional[str] = Field(None, max_length=10)
    requires_approval: bool = False
    approval_level: int = 1

class MovementTypeCreateSchema(MovementTypeBase):
    pass

class MovementTypeUpdateSchema(BaseModel):
    code: Optional[str] = Field(None, max_length=10)
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    direction: Optional[str] = Field(None, max_length=10)
    affects_stock: Optional[bool] = None
    auto_generate_document: Optional[bool] = None
    document_prefix: Optional[str] = Field(None, max_length=10)
    requires_approval: Optional[bool] = None
    approval_level: Optional[int] = None

class MovementTypeSchema(MovementTypeBase):
    id: int

    class Config:
        orm_mode = True
