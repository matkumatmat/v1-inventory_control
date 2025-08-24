from sqlalchemy.orm import Session
from ..base import CRUDService
from ...models.helper import LocationType
from ...schemas.location_type import LocationTypeCreateSchema, LocationTypeUpdateSchema

class LocationTypeService(CRUDService):
    """
    Service for managing Location Types (master data).
    """
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(
            db_session=db_session,
            model_class=LocationType,
            create_schema=LocationTypeCreateSchema,
            update_schema=LocationTypeUpdateSchema,
            current_user=current_user,
            audit_service=audit_service,
            notification_service=notification_service
        )
