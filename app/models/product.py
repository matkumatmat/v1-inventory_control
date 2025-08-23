from app.models.base import BaseModel, db
from sqlalchemy.dialects.postgresql import UUID 
import uuid

class Product(BaseModel):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    product_code = db.Column(db.String(25), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    manufacturer = db.Column(db.String(100))
    product_type_id = db.Column(db.Integer, db.ForeignKey('product_types.id'), nullable=False)
    package_type_id = db.Column(db.Integer, db.ForeignKey('package_types.id'), nullable=False)
    temperature_type_id = db.Column(db.Integer, db.ForeignKey('temperature_types.id'), nullable=False)
    
    # Relationships
    batches = db.relationship('Batch', back_populates='product')
    product_type = db.relationship('ProductType', back_populates='products')
    package_type = db.relationship('PackageType', back_populates='products')     
    temperature_type = db.relationship('TemperatureType', back_populates='products')
    
    # TAMBAHAN: Relationship ke sales order items dan picking order items
    sales_order_items = db.relationship('SalesOrderItem', back_populates='product')
    picking_order_items = db.relationship('PickingOrderItem', back_populates='product')

class Batch(BaseModel):
    __tablename__ = 'batches'

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)    
    lot_number = db.Column(db.String(50), nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    NIE = db.Column(db.String(50), nullable=False)
    received_quantity = db.Column(db.Integer, nullable=False)
    receipt_document = db.Column(db.String(25), nullable=False)
    receipt_date = db.Column(db.Date, nullable=False)
    receipt_pic = db.Column(db.String(25))
    receipt_doc_url = db.Column(db.String(255))
    length = db.Column(db.Float)
    width = db.Column(db.Float)
    height = db.Column(db.Float)
    weight = db.Column(db.Float)

    @property
    def volume(self):
        if self.length is not None and self.width is not None and self.height is not None:
            return self.length * self.width * self.height
        return None
    
    @property
    def total_shipped(self):
        """Total 'Distribusi' dari batch ini (rekap dari semua alokasi)."""
        return sum(alloc.shipped_quantity for alloc in self.allocations)

    @property
    def last_stock(self):
        """'Stock Terakhir' dari batch ini (rekap dari semua alokasi)."""
        return sum(alloc.last_stock for alloc in self.allocations)

    @property
    def total_reserved(self):
        """Total stok yang di-reserve dari batch ini (rekap dari semua alokasi)."""
        return sum(alloc.reserved_quantity for alloc in self.allocations)

    @property
    def available_stock(self):
        """'Available Stock' dari batch ini (rekap dari semua alokasi)."""
        return sum(alloc.available_stock for alloc in self.allocations)

    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product = db.relationship('Product', back_populates='batches')
    
    allocations = db.relationship('Allocation', back_populates='batch')
    stock_movements = db.relationship('StockMovement', back_populates='batch')

class Allocation(BaseModel):
    __tablename__ = 'allocations'
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)    
    allocated_quantity = db.Column(db.Integer, default=0) 
    shipped_quantity = db.Column(db.Integer, default=0)   
    reserved_quantity = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default='active')

    # Tambahan dari skema
    allocation_number = db.Column(db.String(50), unique=True, nullable=True, index=True)
    allocation_date = db.Column(db.Date, nullable=False, default=db.func.current_date())
    expiry_date = db.Column(db.Date)
    priority_level = db.Column(db.Integer, default=5)
    special_instructions = db.Column(db.Text)
    handling_requirements = db.Column(db.Text)
    unit_cost = db.Column(db.Numeric(10, 2))
    total_value = db.Column(db.Numeric(10, 2))

    @property
    def last_stock(self):
        """'Stock Terakhir' di dalam alokasi ini."""
        return self.allocated_quantity - self.shipped_quantity

    @property
    def available_stock(self):
        """'Available Stock' di dalam alokasi ini."""
        return self.last_stock - self.reserved_quantity

    # --- Relasi ---
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=False)
    batch = db.relationship('Batch', back_populates='allocations')
    allocation_type_id = db.Column(db.Integer, db.ForeignKey('allocation_types.id'), nullable=False)
    allocation_type = db.relationship('AllocationType', back_populates='allocations')
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True) 
    customer = db.relationship('Customer', back_populates='allocations')  
    
    # TAMBAHAN: Relationship ke picking dan stock movement
    picking_order_items = db.relationship('PickingOrderItem', back_populates='allocation')
    picking_list_items = db.relationship('PickingListItem', back_populates='allocation')
    consignments = db.relationship('Consignment', back_populates='allocation')
    stock_movements = db.relationship('StockMovement', back_populates='allocation')
    racks = db.relationship('Rack', back_populates='allocation')
    rack_allocations = db.relationship("RackAllocation", back_populates="allocation", cascade="all, delete-orphan")


    # TAMBAHAN: Contract reference untuk tender
    tender_contract_id = db.Column(db.Integer, db.ForeignKey('tender_contracts.id'), nullable=True)
    tender_contract = db.relationship('TenderContract', back_populates='allocations')
    
    # Breakdown untuk tender allocation
    original_reserved_quantity = db.Column(db.Integer, default=0)  # Original dari contract
    customer_allocated_quantity = db.Column(db.Integer, default=0)  # Yang sudah dialokasikan ke customer
    
    @property
    def remaining_for_allocation(self):
        """Untuk tender: sisa yang bisa dialokasikan ke customer lain"""
        if self.allocation_type.code == 'TENDER':
            return self.original_reserved_quantity - self.customer_allocated_quantity
        return 0
    
    # Enhanced available stock calculation
    @property
    def available_stock(self):
        if self.allocation_type.code == 'TENDER':
            # Untuk tender: available = allocated to customer - shipped - reserved for picking
            return self.allocated_quantity - self.shipped_quantity - self.reserved_quantity
        else:
            # Untuk regular: tetap sama
            return self.allocated_quantity - self.shipped_quantity - self.reserved_quantity    

class StockMovement(BaseModel):
    """Model untuk tracking pergerakan stock"""
    __tablename__ = 'stock_movements'
    
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    movement_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    notes = db.Column(db.Text)
    
    # Reference ke movement type
    movement_type_id = db.Column(db.Integer, db.ForeignKey('movement_types.id'), nullable=False)
    movement_type = db.relationship('MovementType', back_populates='stock_movements')
    
    # PERBAIKAN: Reference ke allocation (unit stock yang berubah)
    allocation_id = db.Column(db.Integer, db.ForeignKey('allocations.id'), nullable=False)
    allocation = db.relationship('Allocation', back_populates='stock_movements')
    
    # Reference ke batch untuk reporting
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=False)
    batch = db.relationship('Batch', back_populates='stock_movements')
    
    # TAMBAHAN: Tracking context
    picking_order_item_id = db.Column(db.Integer, db.ForeignKey('picking_order_items.id'), nullable=True)
    picking_order_item = db.relationship('PickingOrderItem')
    
    rack_id = db.Column(db.Integer, db.ForeignKey('racks.id'), nullable=True)
    rack = db.relationship('Rack')
    
    # User yang melakukan movement
    created_by = db.Column(db.String(50))