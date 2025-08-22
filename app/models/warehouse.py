from .base import BaseModel, db
from sqlalchemy.dialects.postgresql import UUID 
import uuid

class Warehouse(BaseModel):
    __tablename__ = 'warehouses'
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    address = db.Column(db.Text)
    status = db.Column(db.String(50), default='active')
    
    racks = db.relationship('Rack', back_populates='warehouse')

class Rack(BaseModel):

    __tablename__ = 'racks'
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    quantity = db.Column(db.Integer, default=0, nullable=False)
    status = db.Column(db.String(50), default='active')
    
    # Location details
    zone = db.Column(db.String(10))  # Zone A, B, C
    row = db.Column(db.String(10))   # Row 1, 2, 3
    level = db.Column(db.String(10)) # Level 1, 2, 3
    
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    warehouse = db.relationship('Warehouse', back_populates='racks')
    
    # PENTING: Rack terkait dengan allocation (bukan batch langsung)
    allocation_id = db.Column(db.Integer, db.ForeignKey('allocations.id'), nullable=True)
    allocation = db.relationship('Allocation', back_populates='racks')
    allocations = db.relationship("RackAllocation", back_populates="rack", cascade="all, delete-orphan")


    location_type_id = db.Column(db.Integer, db.ForeignKey('location_types.id'), nullable=True)
    location_type = db.relationship('LocationType')    
    
    # TAMBAHAN: Relationships untuk tracking
    picking_order_items = db.relationship('PickingOrderItem', back_populates='rack')
    picking_list_items = db.relationship('PickingListItem', back_populates='rack')
    stock_movements = db.relationship('StockMovement', back_populates='rack')
    
    # Properties untuk info batch dan product
    @property
    def batch(self):
        """Get batch info dari allocation"""
        return self.allocation.batch if self.allocation else None
    
    @property
    def product(self):
        """Get product info dari allocation.batch"""
        return self.allocation.batch.product if self.allocation and self.allocation.batch else None
    
    @property
    def customer(self):
        """Get customer info dari allocation"""
        return self.allocation.customer if self.allocation else None
    
    @property
    def allocation_type(self):
        """Get allocation type (reguler/tender)"""
        return self.allocation.allocation_type if self.allocation else None
    
    def __repr__(self):
        return f"<Rack {self.code} - Qty: {self.quantity}>"
    
