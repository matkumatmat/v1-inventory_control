from app.models.base import BaseModel, db
from sqlalchemy.dialects.postgresql import UUID 
import uuid

class PickingList(BaseModel):
    """Model untuk Picking List yang dibuat oleh admin office"""
    __tablename__ = 'picking_lists'
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    picking_list_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    status = db.Column(db.String(50), default='PENDING', nullable=False)  # PENDING, APPROVED, COMPLETED
    created_by = db.Column(db.String(50))  # Admin office gudang
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Reference ke shipping plan
    shipping_plan_id = db.Column(db.Integer, db.ForeignKey('shipping_plans.id'), nullable=False)
    shipping_plan = db.relationship('ShippingPlan', back_populates='picking_lists')
    
    # Items dengan batch dan rack yang sudah ditentukan
    items = db.relationship('PickingListItem', back_populates='picking_list', cascade='all, delete-orphan')
    picking_orders = db.relationship('PickingOrder', back_populates='picking_list')
    packing_slip_id = db.Column(db.Integer, db.ForeignKey('packing_slips.id'), nullable=True)
    packing_slip = db.relationship('PackingSlip', back_populates='picking_lists')    

class PickingListItem(BaseModel):
    """Detail item dalam picking list dengan allocation dan rack yang sudah ditentukan"""
    __tablename__ = 'picking_list_items'
    
    id = db.Column(db.Integer, primary_key=True)
    quantity_to_pick = db.Column(db.Integer, nullable=False)
    
    # KUNCI: Reference ke allocation (yang menentukan batch+customer)
    allocation_id = db.Column(db.Integer, db.ForeignKey('allocations.id'), nullable=False)
    allocation = db.relationship('Allocation')
    
    # Rack yang dipilih untuk picking
    rack_id = db.Column(db.Integer, db.ForeignKey('racks.id'), nullable=False)
    rack = db.relationship('Rack')
    
    # Reference ke shipping plan item
    shipping_plan_item_id = db.Column(db.Integer, db.ForeignKey('shipping_plan_items.id'), nullable=False)
    shipping_plan_item = db.relationship('ShippingPlanItem')
    
    picking_list_id = db.Column(db.Integer, db.ForeignKey('picking_lists.id'), nullable=False)
    picking_list = db.relationship('PickingList', back_populates='items')
    
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

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    picking_order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    status = db.Column(db.String(50), default='PENDING', nullable=False)  # PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    
    # Reference ke picking list
    picking_list_id = db.Column(db.Integer, db.ForeignKey('picking_lists.id'), nullable=False)
    picking_list = db.relationship('PickingList', back_populates='picking_orders')
    
    # Optional: Reference ke shipment jika sudah sampai tahap shipment
    shipment_id = db.Column(db.Integer, db.ForeignKey('shipments.id'), nullable=True)
    shipment = db.relationship('Shipment', back_populates='picking_orders')
    
    # Tracking
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    picked_by = db.Column(db.String(50))  # Worker yang melakukan picking
    
    items = db.relationship('PickingOrderItem', back_populates='picking_order', cascade='all, delete-orphan')
    packing_orders = db.relationship('PackingOrder', back_populates='picking_order')

class PickingOrderItem(BaseModel):
    """Detail item yang akan/sudah dipick oleh tim gudang"""
    __tablename__ = 'picking_order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    quantity_requested = db.Column(db.Integer, nullable=False)
    quantity_picked = db.Column(db.Integer, default=0, nullable=False)
    
    # PERBAIKAN: Reference ke allocation (bukan batch langsung)
    allocation_id = db.Column(db.Integer, db.ForeignKey('allocations.id'), nullable=False)
    allocation = db.relationship('Allocation')
    
    # Rack reference
    rack_id = db.Column(db.Integer, db.ForeignKey('racks.id'), nullable=False)
    rack = db.relationship('Rack')
    
    # Product reference untuk kemudahan query
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product = db.relationship('Product')
    
    # Reference ke picking list item
    picking_list_item_id = db.Column(db.Integer, db.ForeignKey('picking_list_items.id'), nullable=True)
    picking_list_item = db.relationship('PickingListItem')
    
    # Tracking fields
    scanned_at = db.Column(db.DateTime)
    scanned_by = db.Column(db.String(50))
    status = db.Column(db.String(50), default='PENDING')  # PENDING, PICKED, SHORTAGE, DAMAGED
    notes = db.Column(db.Text)  # Catatan jika ada masalah
    
    picking_order_id = db.Column(db.Integer, db.ForeignKey('picking_orders.id'), nullable=False)
    picking_order = db.relationship('PickingOrder', back_populates='items')
    
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
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    packing_order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    status = db.Column(db.String(50), default='PENDING', nullable=False)  # PENDING, IN_PROGRESS, COMPLETED
    
    # Grouping berdasarkan customer
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    customer = db.relationship('Customer')
    
    # Dari picking order yang sudah selesai
    picking_order_id = db.Column(db.Integer, db.ForeignKey('picking_orders.id'), nullable=False)
    picking_order = db.relationship('PickingOrder', back_populates='packing_orders')
    
    # Tracking
    created_by = db.Column(db.String(50))  # Tim packing
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    completed_at = db.Column(db.DateTime)
    
    boxes = db.relationship('PackingBox', back_populates='packing_order', cascade='all, delete-orphan')

class PackingBox(BaseModel):
    """Model untuk Box dalam packing order"""
    __tablename__ = 'packing_boxes'
    
    id = db.Column(db.Integer, primary_key=True)
    box_number = db.Column(db.String(50), nullable=False)  # Box 1, Box 2, dst
    box_type = db.Column(db.String(50))  # Jenis box yang digunakan
    total_weight = db.Column(db.Float)
    notes = db.Column(db.Text)
    
    packing_order_id = db.Column(db.Integer, db.ForeignKey('packing_orders.id'), nullable=False)
    packing_order = db.relationship('PackingOrder', back_populates='boxes')
    packaging_material_id = db.Column(db.Integer, db.ForeignKey('packaging_materials.id'), nullable=True)
    packaging_material = db.relationship('PackagingMaterial')    
    
    items = db.relationship('PackingBoxItem', back_populates='box', cascade='all, delete-orphan')

class PackingBoxItem(BaseModel):
    """Detail item dalam setiap box"""
    __tablename__ = 'packing_box_items'
    
    id = db.Column(db.Integer, primary_key=True)
    quantity_packed = db.Column(db.Integer, nullable=False)
    
    box_id = db.Column(db.Integer, db.ForeignKey('packing_boxes.id'), nullable=False)
    box = db.relationship('PackingBox', back_populates='items')
    
    # Reference ke picked item
    picking_order_item_id = db.Column(db.Integer, db.ForeignKey('picking_order_items.id'), nullable=False)
    picking_order_item = db.relationship('PickingOrderItem')
    
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