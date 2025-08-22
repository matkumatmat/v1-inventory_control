from app.models.base import BaseModel, db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class PackingSlip(BaseModel):
    """Model untuk PS (Packing Slip) dari ERP - sebagai grouping dokumen"""
    __tablename__ = 'packing_slips'
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    
    # PS details dari ERP
    ps_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    ps_date = db.Column(db.Date, nullable=False)
    
    # DO details (optional - kadang ada kadang tidak)
    do_number = db.Column(db.String(50), nullable=True, index=True)
    do_date = db.Column(db.Date, nullable=True)
    do_document_url = db.Column(db.String(255))
    
    # ERP Integration
    erp_ps_id = db.Column(db.String(50))
    erp_do_id = db.Column(db.String(50))
    erp_sync_date = db.Column(db.DateTime)
    
    # Status
    status = db.Column(db.String(20), default='PENDING')
    
    # Document references
    ps_document_url = db.Column(db.String(255))
    
    # Tracking
    created_by = db.Column(db.String(50))
    created_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationships - PS bisa berisi multiple SO dan multiple PL
    sales_orders = db.relationship('SalesOrder', back_populates='packing_slip')
    picking_lists = db.relationship('PickingList', back_populates='packing_slip')
    shipments = db.relationship('Shipment', back_populates='packing_slip')
    
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