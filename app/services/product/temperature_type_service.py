from sqlalchemy.orm import Session
from ..base import CRUDService
from ...models.helper import TemperatureType
from ...schemas.temperature_type import TemperatureTypeCreateSchema, TemperatureTypeUpdateSchema, TemperatureTypeSchema

class TemperatureTypeService(CRUDService):
    """
    Service for managing Temperature Types (master data).
    """
    model_class = TemperatureType
    create_schema = TemperatureTypeCreateSchema
    update_schema = TemperatureTypeUpdateSchema
    response_schema = TemperatureTypeSchema

    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(
            db_session=db_session,
            current_user=current_user,
            audit_service=audit_service,
            notification_service=notification_service
        )
