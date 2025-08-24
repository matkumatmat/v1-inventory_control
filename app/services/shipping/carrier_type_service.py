from sqlalchemy.orm import Session
from ..base import CRUDService
from ...models.helper import CarrierType
from ...schemas.carrier_type import CarrierTypeCreateSchema, CarrierTypeUpdateSchema

class CarrierTypeService(CRUDService):
    """
    Service for managing Carrier Types (master data).
    """
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(
            db_session=db_session,
            model_class=CarrierType,
            create_schema=CarrierTypeCreateSchema,
            update_schema=CarrierTypeUpdateSchema,
            current_user=current_user,
            audit_service=audit_service,
            notification_service=notification_service
        )
