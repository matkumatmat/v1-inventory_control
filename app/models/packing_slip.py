import uuid
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Text, DateTime, Date,
    func
)
from sqlalchemy.orm import relationship
from .base import BaseModel

class PackingSlip(BaseModel):
    """Model untuk PS (Packing Slip) dari ERP - sebagai grouping dokumen"""
    __tablename__ = 'packing_slips'
    
    public_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)
    
    # PS details dari ERP
    ps_number = Column(String(50), unique=True, nullable=False, index=True)
    ps_date = Column(Date, nullable=False)
    
    # DO details (optional - kadang ada kadang tidak)
    do_number = Column(String(50), nullable=True, index=True)
    do_date = Column(Date, nullable=True)
    do_document_url = Column(String(255))
    
    # ERP Integration
    erp_ps_id = Column(String(50))
    erp_do_id = Column(String(50))
    erp_sync_date = Column(DateTime)
    
    # Status
    status = Column(String(20), default='PENDING')
    
    # Document references
    ps_document_url = Column(String(255))
    
    # Tracking
    created_by = Column(String(50))
    created_date = Column(DateTime, default=func.current_timestamp())
    
    # Relationships - PS bisa berisi multiple SO dan multiple PL
    sales_orders = relationship('SalesOrder', back_populates='packing_slip')
    picking_lists = relationship('PickingList', back_populates='packing_slip')
    shipments = relationship('Shipment', back_populates='packing_slip')
    
    @property
    def total_sales_orders(self):
        return len(self.sales_orders)
    
    @property
    def total_picking_lists(self):
        return len(self.picking_lists)
    
    @property
    def total_quantity(self):
        total = 0
        for pl in self.picking_lists:
            total += sum(item.quantity_to_pick for item in pl.items)
        return total
    
    def __repr__(self):
        return f'<PackingSlip {self.ps_number}>'