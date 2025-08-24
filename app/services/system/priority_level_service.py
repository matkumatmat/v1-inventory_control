from sqlalchemy.orm import Session
from ..base import CRUDService
from ...models.helper import PriorityLevel
from ...schemas.priority_level import PriorityLevelCreateSchema, PriorityLevelUpdateSchema, PriorityLevelSchema

class PriorityLevelService(CRUDService):
    """
    Service for managing Priority Levels (master data).
    """
    model_class = PriorityLevel
    create_schema = PriorityLevelCreateSchema
    update_schema = PriorityLevelUpdateSchema
    response_schema = PriorityLevelSchema

    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(
            db_session=db_session,
            current_user=current_user,
            audit_service=audit_service,
            notification_service=notification_service
        )
