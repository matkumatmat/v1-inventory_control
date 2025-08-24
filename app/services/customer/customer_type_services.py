from sqlalchemy.orm import Session
from ..base import CRUDService
from ...models.helper import CustomerType
from ...schemas.customer_type import CustomerTypeCreateSchema, CustomerTypeUpdateSchema, CustomerTypeSchema

class CustomerTypeService(CRUDService):
    """
    Service for managing Customer Types (master data).
    """
    model_class = CustomerType
    create_schema = CustomerTypeCreateSchema
    update_schema = CustomerTypeUpdateSchema
    response_schema = CustomerTypeSchema

    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(
            db_session=db_session,
            current_user=current_user,
            audit_service=audit_service,
            notification_service=notification_service
        )
