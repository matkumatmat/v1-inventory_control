from pydantic import BaseModel, Field
from typing import Optional

class NotificationTypeBase(BaseModel):
    code: str = Field(max_length=20)
    name: str = Field(max_length=50)
    description: Optional[str] = None
    is_active: bool = True
    is_email_enabled: bool = True
    is_sms_enabled: bool = False
    is_push_enabled: bool = True
    is_system_notification: bool = True
    email_template: Optional[str] = Field(None, max_length=100)
    sms_template: Optional[str] = Field(None, max_length=100)
    push_template: Optional[str] = Field(None, max_length=100)
    retry_count: int = 3
    retry_interval_minutes: int = 5

class NotificationTypeCreateSchema(NotificationTypeBase):
    pass

class NotificationTypeUpdateSchema(BaseModel):
    code: Optional[str] = Field(None, max_length=20)
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_email_enabled: Optional[bool] = None
    is_sms_enabled: Optional[bool] = None
    is_push_enabled: Optional[bool] = None
    is_system_notification: Optional[bool] = None
    email_template: Optional[str] = Field(None, max_length=100)
    sms_template: Optional[str] = Field(None, max_length=100)
    push_template: Optional[str] = Field(None, max_length=100)
    retry_count: Optional[int] = None
    retry_interval_minutes: Optional[int] = None

class NotificationTypeSchema(NotificationTypeBase):
    id: int

    class Config:
        orm_mode = True
