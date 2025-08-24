from sqlalchemy.orm import Session
from ..base import CRUDService
from ...models.helper import NotificationType
from ...schemas.notification_type import NotificationTypeCreateSchema, NotificationTypeUpdateSchema

class NotificationTypeService(CRUDService):
    """
    Service for managing Notification Types (master data).
    """
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(
            db_session=db_session,
            model_class=NotificationType,
            create_schema=NotificationTypeCreateSchema,
            update_schema=NotificationTypeUpdateSchema,
            current_user=current_user,
            audit_service=audit_service,
            notification_service=notification_service
        )
