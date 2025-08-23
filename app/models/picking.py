import uuid
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Text, DateTime, Float,
    func
)
from sqlalchemy.orm import relationship
from .base import BaseModel

class PickingList(BaseModel):
    """Model untuk Picking List yang dibuat oleh admin office"""
    __tablename__ = 'picking_lists'
    
    public_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)
    picking_list_number = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(String(50), default='PENDING', nullable=False)  # PENDING, APPROVED, COMPLETED
    created_by = Column(String(50))  # Admin office gudang
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Reference ke shipping plan
    shipping_plan_id = Column(Integer, ForeignKey('shipping_plans.id'), nullable=False)
    shipping_plan = relationship('ShippingPlan', back_populates='picking_lists')
    
    # Items dengan batch dan rack yang sudah ditentukan
    items = relationship('PickingListItem', back_populates='picking_list', cascade='all, delete-orphan')
    picking_orders = relationship('PickingOrder', back_populates='picking_list')
    packing_slip_id = Column(Integer, ForeignKey('packing_slips.id'), nullable=True)
    packing_slip = relationship('PackingSlip', back_populates='picking_lists')

class PickingListItem(BaseModel):
    """Detail item dalam picking list dengan allocation dan rack yang sudah ditentukan"""
    __tablename__ = 'picking_list_items'
    
    quantity_to_pick = Column(Integer, nullable=False)
    
    # KUNCI: Reference ke allocation (yang menentukan batch+customer)
    allocation_id = Column(Integer, ForeignKey('allocations.id'), nullable=False)
    allocation = relationship('Allocation')
    
    # Rack yang dipilih untuk picking
    rack_id = Column(Integer, ForeignKey('racks.id'), nullable=False)
    rack = relationship('Rack')
    
    # Reference ke shipping plan item
    shipping_plan_item_id = Column(Integer, ForeignKey('shipping_plan_items.id'), nullable=False)
    shipping_plan_item = relationship('ShippingPlanItem')
    
    picking_list_id = Column(Integer, ForeignKey('picking_lists.id'), nullable=False)
    picking_list = relationship('PickingList', back_populates='items')
    
    # Properties untuk info produk dan batch
    @property
    def product(self):
        return self.allocation.batch.product if self.allocation and self.allocation.batch else None
    
    @property
    def batch(self):
        return self.allocation.batch if self.allocation else None
    
    @property
    def customer(self):
        return self.allocation.customer if self.allocation else None

class PickingOrder(BaseModel):
    """Model untuk Picking Order yang dieksekusi oleh tim gudang"""
    __tablename__ = 'picking_orders'

    public_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)
    picking_order_number = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(String(50), default='PENDING', nullable=False)  # PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    
    # Reference ke picking list
    picking_list_id = Column(Integer, ForeignKey('picking_lists.id'), nullable=False)
    picking_list = relationship('PickingList', back_populates='picking_orders')
    
    # Optional: Reference ke shipment jika sudah sampai tahap shipment
    shipment_id = Column(Integer, ForeignKey('shipments.id'), nullable=True)
    shipment = relationship('Shipment', back_populates='picking_orders')
    
    # Tracking
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    picked_by = Column(String(50))  # Worker yang melakukan picking
    
    items = relationship('PickingOrderItem', back_populates='picking_order', cascade='all, delete-orphan')
    packing_orders = relationship('PackingOrder', back_populates='picking_order')

class PickingOrderItem(BaseModel):
    """Detail item yang akan/sudah dipick oleh tim gudang"""
    __tablename__ = 'picking_order_items'
    
    quantity_requested = Column(Integer, nullable=False)
    quantity_picked = Column(Integer, default=0, nullable=False)
    
    # PERBAIKAN: Reference ke allocation (bukan batch langsung)
    allocation_id = Column(Integer, ForeignKey('allocations.id'), nullable=False)
    allocation = relationship('Allocation')
    
    # Rack reference
    rack_id = Column(Integer, ForeignKey('racks.id'), nullable=False)
    rack = relationship('Rack')
    
    # Product reference untuk kemudahan query
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    product = relationship('Product')
    
    # Reference ke picking list item
    picking_list_item_id = Column(Integer, ForeignKey('picking_list_items.id'), nullable=True)
    picking_list_item = relationship('PickingListItem')
    
    # Tracking fields
    scanned_at = Column(DateTime)
    scanned_by = Column(String(50))
    status = Column(String(50), default='PENDING')  # PENDING, PICKED, SHORTAGE, DAMAGED
    notes = Column(Text)  # Catatan jika ada masalah
    
    picking_order_id = Column(Integer, ForeignKey('picking_orders.id'), nullable=False)
    picking_order = relationship('PickingOrder', back_populates='items')
    
    # Property untuk mendapatkan batch info
    @property
    def batch(self):
        return self.allocation.batch if self.allocation else None
    
    @property
    def customer(self):
        return self.allocation.customer if self.allocation else None

class PackingOrder(BaseModel):
    """Model untuk Packing Order yang mengelompokkan berdasarkan customer"""
    __tablename__ = 'packing_orders'
    
    public_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)
    packing_order_number = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(String(50), default='PENDING', nullable=False)  # PENDING, IN_PROGRESS, COMPLETED
    
    # Grouping berdasarkan customer
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    customer = relationship('Customer')
    
    # Dari picking order yang sudah selesai
    picking_order_id = Column(Integer, ForeignKey('picking_orders.id'), nullable=False)
    picking_order = relationship('PickingOrder', back_populates='packing_orders')
    
    # Tracking
    created_by = Column(String(50))  # Tim packing
    created_at = Column(DateTime, default=func.current_timestamp())
    completed_at = Column(DateTime)
    
    boxes = relationship('PackingBox', back_populates='packing_order', cascade='all, delete-orphan')

class PackingBox(BaseModel):
    """Model untuk Box dalam packing order"""
    __tablename__ = 'packing_boxes'
    
    box_number = Column(String(50), nullable=False)  # Box 1, Box 2, dst
    box_type = Column(String(50))  # Jenis box yang digunakan
    total_weight = Column(Float)
    notes = Column(Text)
    
    packing_order_id = Column(Integer, ForeignKey('packing_orders.id'), nullable=False)
    packing_order = relationship('PackingOrder', back_populates='boxes')
    packaging_material_id = Column(Integer, ForeignKey('packaging_materials.id'), nullable=True)
    packaging_material = relationship('PackagingMaterial')    
    
    items = relationship('PackingBoxItem', back_populates='box', cascade='all, delete-orphan')

class PackingBoxItem(BaseModel):
    """Detail item dalam setiap box"""
    __tablename__ = 'packing_box_items'
    
    quantity_packed = Column(Integer, nullable=False)
    
    box_id = Column(Integer, ForeignKey('packing_boxes.id'), nullable=False)
    box = relationship('PackingBox', back_populates='items')
    
    # Reference ke picked item
    picking_order_item_id = Column(Integer, ForeignKey('picking_order_items.id'), nullable=False)
    picking_order_item = relationship('PickingOrderItem')
    
    # Properties untuk kemudahan akses data
    @property
    def product(self):
        return self.picking_order_item.product if self.picking_order_item else None
    
    @property
    def batch(self):
        return self.picking_order_item.batch if self.picking_order_item else None
    
    @property
    def allocation(self):
        return self.picking_order_item.allocation if self.picking_order_item else None