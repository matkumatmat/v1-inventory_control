from sqlalchemy.orm import Session
from ..base import CRUDService
from ...models.helper import PackageType
from ...schemas.package_type import PackageTypeCreateSchema, PackageTypeUpdateSchema, PackageTypeSchema

class PackageTypeService(CRUDService):
    """
    Service for managing Package Types (master data).
    """
    model_class = PackageType
    create_schema = PackageTypeCreateSchema
    update_schema = PackageTypeUpdateSchema
    response_schema = PackageTypeSchema

    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(
            db_session=db_session,
            current_user=current_user,
            audit_service=audit_service,
            notification_service=notification_service
        )
