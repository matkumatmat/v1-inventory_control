from sqlalchemy.orm import Session
from ..base import CRUDService
from ...models.helper import AllocationType
from ...schemas.allocation_type import AllocationTypeCreateSchema, AllocationTypeUpdateSchema

class AllocationTypeService(CRUDService):
    """
    Service for managing Allocation Types (master data).
    """
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(
            db_session=db_session,
            model_class=AllocationType,
            create_schema=AllocationTypeCreateSchema,
            update_schema=AllocationTypeUpdateSchema,
            current_user=current_user,
            audit_service=audit_service,
            notification_service=notification_service
        )
