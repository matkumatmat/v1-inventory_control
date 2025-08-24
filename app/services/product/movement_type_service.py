from sqlalchemy.orm import Session
from ..base import CRUDService
from ...models.helper import MovementType
from ...schemas.movement_type import MovementTypeCreateSchema, MovementTypeUpdateSchema, MovementTypeSchema

class MovementTypeService(CRUDService):
    """
    Service for managing Movement Types (master data).
    """
    model_class = MovementType
    create_schema = MovementTypeCreateSchema
    update_schema = MovementTypeUpdateSchema
    response_schema = MovementTypeSchema

    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(
            db_session=db_session,
            current_user=current_user,
            audit_service=audit_service,
            notification_service=notification_service
        )
