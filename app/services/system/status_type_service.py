from sqlalchemy.orm import Session
from ..base import CRUDService
from ...models.helper import StatusType
from ...schemas.status_type import StatusTypeCreateSchema, StatusTypeUpdateSchema

class StatusTypeService(CRUDService):
    """
    Service for managing Status Types (master data).
    """
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(
            db_session=db_session,
            model_class=StatusType,
            create_schema=StatusTypeCreateSchema,
            update_schema=StatusTypeUpdateSchema,
            current_user=current_user,
            audit_service=audit_service,
            notification_service=notification_service
        )
