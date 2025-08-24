from sqlalchemy.orm import Session
from ..base import CRUDService
from ...models.helper import ShippingMethod
from ...schemas.shipping_method import ShippingMethodCreateSchema, ShippingMethodUpdateSchema

class ShippingMethodService(CRUDService):
    """
    Service for managing Shipping Methods (master data).
    """
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(
            db_session=db_session,
            model_class=ShippingMethod,
            create_schema=ShippingMethodCreateSchema,
            update_schema=ShippingMethodUpdateSchema,
            current_user=current_user,
            audit_service=audit_service,
            notification_service=notification_service
        )
