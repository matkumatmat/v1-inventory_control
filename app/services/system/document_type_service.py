from sqlalchemy.orm import Session
from ..base import CRUDService
from ...models.helper import DocumentType
from ...schemas.document_type import DocumentTypeCreateSchema, DocumentTypeUpdateSchema

class DocumentTypeService(CRUDService):
    """
    Service for managing Document Types (master data).
    """
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(
            db_session=db_session,
            model_class=DocumentType,
            create_schema=DocumentTypeCreateSchema,
            update_schema=DocumentTypeUpdateSchema,
            current_user=current_user,
            audit_service=audit_service,
            notification_service=notification_service
        )
