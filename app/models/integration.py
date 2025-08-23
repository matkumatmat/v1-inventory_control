"""
Integration Models
==================

Models related to third-party integrations, such as ERP systems.
"""

from .base import BaseModel, db
from sqlalchemy.dialects.postgresql import JSONB

class ERPSyncLog(BaseModel):
    """Model to log ERP synchronization operations."""
    __tablename__ = 'erp_sync_logs'

    id = db.Column(db.Integer, primary_key=True)
    operation_type = db.Column(db.String(50), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, index=True)
    details = db.Column(JSONB)
    executed_by = db.Column(db.String(50))
    executed_at = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<ERPSyncLog {self.operation_type} - {self.status}>'
