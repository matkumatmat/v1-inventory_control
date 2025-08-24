from sqlalchemy.orm import Session
from ..base import CRUDService
from ...models.helper import ShippingMethod
from ...schemas.shipping_method import ShippingMethodCreateSchema, ShippingMethodUpdateSchema, ShippingMethodSchema

class ShippingMethodService(CRUDService):
    """
    Service for managing Shipping Methods (master data).
    """
    model_class = ShippingMethod
    create_schema = ShippingMethodCreateSchema
    update_schema = ShippingMethodUpdateSchema
    response_schema = ShippingMethodSchema

    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(
            db_session=db_session,
            current_user=current_user,
            audit_service=audit_service,
            notification_service=notification_service
        )
