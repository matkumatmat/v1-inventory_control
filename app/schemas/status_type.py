from pydantic import BaseModel, Field
from typing import Optional

class StatusTypeBase(BaseModel):
    entity_type: str = Field(max_length=50)
    code: str = Field(max_length=20)
    name: str = Field(max_length=50)
    description: Optional[str] = None
    is_active: bool = True
    is_initial_status: bool = False
    is_final_status: bool = False
    is_error_status: bool = False
    sort_order: int = 0
    color_code: Optional[str] = Field(None, max_length=7)
    icon: Optional[str] = Field(None, max_length=50)
    css_class: Optional[str] = Field(None, max_length=50)
    auto_transition_after_hours: Optional[int] = None
    requires_approval: bool = False
    sends_notification: bool = False

class StatusTypeCreateSchema(StatusTypeBase):
    pass

class StatusTypeUpdateSchema(BaseModel):
    entity_type: Optional[str] = Field(None, max_length=50)
    code: Optional[str] = Field(None, max_length=20)
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_initial_status: Optional[bool] = None
    is_final_status: Optional[bool] = None
    is_error_status: Optional[bool] = None
    sort_order: Optional[int] = None
    color_code: Optional[str] = Field(None, max_length=7)
    icon: Optional[str] = Field(None, max_length=50)
    css_class: Optional[str] = Field(None, max_length=50)
    auto_transition_after_hours: Optional[int] = None
    requires_approval: Optional[bool] = None
    sends_notification: Optional[bool] = None

class StatusTypeSchema(StatusTypeBase):
    id: int

    class Config:
        orm_mode = True
