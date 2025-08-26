from sqlalchemy.ext.asyncio import AsyncSession
from ..base import CRUDService
from ...models.helper import SectorType
from ...schemas.sector_type import SectorTypeCreateSchema, SectorTypeUpdateSchema

class SectorTypeService(CRUDService):
    """
    Service for managing Sector Types (master data).
    """
    def __init__(self, db_session: AsyncSession, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(
            db_session=db_session,
            model_class=SectorType,
            create_schema=SectorTypeCreateSchema,
            update_schema=SectorTypeUpdateSchema,
            current_user=current_user,
            audit_service=audit_service,
            notification_service=notification_service
        )
