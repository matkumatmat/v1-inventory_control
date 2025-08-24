from pydantic import BaseModel, Field
from typing import Optional

class PriorityLevelBase(BaseModel):
    code: str = Field(max_length=10)
    name: str = Field(max_length=50)
    description: Optional[str] = None
    is_active: bool = True
    level: int
    sla_hours: Optional[int] = None
    escalation_hours: Optional[int] = None
    color_code: Optional[str] = Field(None, max_length=7)
    icon: Optional[str] = Field(None, max_length=50)

class PriorityLevelCreateSchema(PriorityLevelBase):
    pass

class PriorityLevelUpdateSchema(BaseModel):
    code: Optional[str] = Field(None, max_length=10)
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    level: Optional[int] = None
    sla_hours: Optional[int] = None
    escalation_hours: Optional[int] = None
    color_code: Optional[str] = Field(None, max_length=7)
    icon: Optional[str] = Field(None, max_length=50)

class PriorityLevelSchema(PriorityLevelBase):
    id: int

    class Config:
        orm_mode = True
