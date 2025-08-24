from sqlalchemy.orm import Session
from ..base import CRUDService
from ...models.helper import PackagingMaterial
from ...schemas.packaging_material import PackagingMaterialCreateSchema, PackagingMaterialUpdateSchema

class PackagingMaterialService(CRUDService):
    """
    Service for managing Packaging Materials (master data).
    """
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(
            db_session=db_session,
            model_class=PackagingMaterial,
            create_schema=PackagingMaterialCreateSchema,
            update_schema=PackagingMaterialUpdateSchema,
            current_user=current_user,
            audit_service=audit_service,
            notification_service=notification_service
        )
