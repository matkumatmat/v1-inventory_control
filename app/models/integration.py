"""
Integration Models
==================

Models related to third-party integrations, such as ERP systems.
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, JSON
)
from .base import BaseModel

class ERPSyncLog(BaseModel):
    """Model to log ERP synchronization operations."""
    __tablename__ = 'erp_sync_logs'

    operation_type = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)
    details = Column(JSON)
    executed_by = Column(String(50))
    executed_at = Column(DateTime, nullable=False)

    def __repr__(self):
        return f'<ERPSyncLog {self.operation_type} - {self.status}>'
