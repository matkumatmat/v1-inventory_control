from pydantic import BaseModel, Field
from typing import Optional

class DocumentTypeBase(BaseModel):
    code: str = Field(max_length=10)
    name: str = Field(max_length=50)
    description: Optional[str] = None
    is_active: bool = True
    is_mandatory: bool = False
    is_customer_visible: bool = True
    max_file_size_mb: int = 10
    allowed_extensions: Optional[str] = Field(None, max_length=100)
    auto_generate: bool = False
    template_path: Optional[str] = Field(None, max_length=255)

class DocumentTypeCreateSchema(DocumentTypeBase):
    pass

class DocumentTypeUpdateSchema(BaseModel):
    code: Optional[str] = Field(None, max_length=10)
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_mandatory: Optional[bool] = None
    is_customer_visible: Optional[bool] = None
    max_file_size_mb: Optional[int] = None
    allowed_extensions: Optional[str] = Field(None, max_length=100)
    auto_generate: Optional[bool] = None
    template_path: Optional[str] = Field(None, max_length=255)

class DocumentTypeSchema(DocumentTypeBase):
    id: int

    class Config:
        orm_mode = True
