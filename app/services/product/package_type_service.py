from sqlalchemy.orm import Session
from ..base import CRUDService
from ...models.helper import PackageType
from ...schemas.package_type import PackageTypeCreateSchema, PackageTypeUpdateSchema

class PackageTypeService(CRUDService):
    """
    Service for managing Package Types (master data).
    """
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(
            db_session=db_session,
            model_class=PackageType,
            create_schema=PackageTypeCreateSchema,
            update_schema=PackageTypeUpdateSchema,
            current_user=current_user,
            audit_service=audit_service,
            notification_service=notification_service
        )
