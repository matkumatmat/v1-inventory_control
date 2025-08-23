import uuid
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Text, DateTime, func
)
from sqlalchemy.orm import relationship
from .base import BaseModel

class Warehouse(BaseModel):
    __tablename__ = 'warehouses'
    
    public_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(10), unique=True, nullable=False)
    address = Column(Text)
    status = Column(String(50), default='active')
    
    racks = relationship('Rack', back_populates='warehouse')

class Rack(BaseModel):

    __tablename__ = 'racks'
    
    public_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    quantity = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default='active')
    
    # Location details
    zone = Column(String(10))  # Zone A, B, C
    row = Column(String(10))   # Row 1, 2, 3
    level = Column(String(10)) # Level 1, 2, 3
    
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False)
    warehouse = relationship('Warehouse', back_populates='racks')
    
    # PENTING: Rack terkait dengan allocation (bukan batch langsung)
    allocation_id = Column(Integer, ForeignKey('allocations.id'), nullable=True)
    allocation = relationship('Allocation', back_populates='racks')
    allocations = relationship("RackAllocation", back_populates="rack", cascade="all, delete-orphan")


    location_type_id = Column(Integer, ForeignKey('location_types.id'), nullable=True)
    location_type = relationship('LocationType')
    
    # TAMBAHAN: Relationships untuk tracking
    picking_order_items = relationship('PickingOrderItem', back_populates='rack')
    picking_list_items = relationship('PickingListItem', back_populates='rack')
    stock_movements = relationship('StockMovement', back_populates='rack')
    
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


class RackAllocation(BaseModel):
    """Association table between Rack and Allocation"""
    __tablename__ = 'rack_allocations'
    
    
    rack_id = Column(Integer, ForeignKey('racks.id'), nullable=False)
    allocation_id = Column(Integer, ForeignKey('allocations.id'), nullable=False)
    
    quantity = Column(Integer, nullable=False)
    
    placement_date = Column(DateTime, default=func.current_timestamp())
    placed_by = Column(String(50))
    position_details = Column(String(255))
    
    # Relationships
    rack = relationship('Rack', back_populates='allocations')
    allocation = relationship('Allocation', back_populates='rack_allocations')

    def __repr__(self):
        return f"<RackAllocation rack={self.rack.code} alloc_id={self.allocation_id} qty={self.quantity}>"
