from sqlalchemy.orm import Session
from ..base import CRUDService
from ...models.helper import ProductType
from ...schemas.product_type import ProductTypeCreateSchema, ProductTypeUpdateSchema, ProductTypeSchema

class ProductTypeService(CRUDService):
    """
    Service for managing Product Types (master data).
    """
    model_class = ProductType
    create_schema = ProductTypeCreateSchema
    update_schema = ProductTypeUpdateSchema
    response_schema = ProductTypeSchema

    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(
            db_session=db_session,
            current_user=current_user,
            audit_service=audit_service,
            notification_service=notification_service
        )
