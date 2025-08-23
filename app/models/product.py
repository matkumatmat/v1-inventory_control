import uuid
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Float, Date, DateTime, Numeric, Text,
    func
)
from sqlalchemy.orm import relationship
from .base import BaseModel

class Product(BaseModel):
    __tablename__ = 'products'
    
    public_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)
    product_code = Column(String(25), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    manufacturer = Column(String(100))
    product_type_id = Column(Integer, ForeignKey('product_types.id'), nullable=False)
    package_type_id = Column(Integer, ForeignKey('package_types.id'), nullable=False)
    temperature_type_id = Column(Integer, ForeignKey('temperature_types.id'), nullable=False)
    
    # Relationships
    batches = relationship('Batch', back_populates='product')
    product_type = relationship('ProductType', back_populates='products')
    package_type = relationship('PackageType', back_populates='products')     
    temperature_type = relationship('TemperatureType', back_populates='products')
    
    sales_order_items = relationship('SalesOrderItem', back_populates='product')
    picking_order_items = relationship('PickingOrderItem', back_populates='product')

class Batch(BaseModel):
    __tablename__ = 'batches'

    public_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)
    lot_number = Column(String(50), nullable=False)
    expiry_date = Column(Date, nullable=False)
    NIE = Column(String(50), nullable=False)
    received_quantity = Column(Integer, nullable=False)
    receipt_document = Column(String(25), nullable=False)
    receipt_date = Column(Date, nullable=False)
    receipt_pic = Column(String(25))
    receipt_doc_url = Column(String(255))
    length = Column(Float)
    width = Column(Float)
    height = Column(Float)
    weight = Column(Float)

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

    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    product = relationship('Product', back_populates='batches')
    
    allocations = relationship('Allocation', back_populates='batch')
    stock_movements = relationship('StockMovement', back_populates='batch')

class Allocation(BaseModel):
    __tablename__ = 'allocations'
    
    public_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)
    allocated_quantity = Column(Integer, default=0) 
    shipped_quantity = Column(Integer, default=0)   
    reserved_quantity = Column(Integer, default=0)
    status = Column(String(50), default='active')

    # Tambahan dari skema
    allocation_number = Column(String(50), unique=True, nullable=True, index=True)
    allocation_date = Column(Date, nullable=False, default=func.current_date())
    expiry_date = Column(Date)
    priority_level = Column(Integer, default=5)
    special_instructions = Column(Text)
    handling_requirements = Column(Text)
    unit_cost = Column(Numeric(10, 2))
    total_value = Column(Numeric(10, 2))

    @property
    def last_stock(self):
        """'Stock Terakhir' di dalam alokasi ini."""
        return self.allocated_quantity - self.shipped_quantity

    @property
    def available_stock(self):
        """'Available Stock' di dalam alokasi ini."""
        return self.last_stock - self.reserved_quantity

    # --- Relasi ---
    batch_id = Column(Integer, ForeignKey('batches.id'), nullable=False)
    batch = relationship('Batch', back_populates='allocations')
    allocation_type_id = Column(Integer, ForeignKey('allocation_types.id'), nullable=False)
    allocation_type = relationship('AllocationType', back_populates='allocations')
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True) 
    customer = relationship('Customer', back_populates='allocations')  
    
    # TAMBAHAN: Relationship ke picking dan stock movement
    picking_order_items = relationship('PickingOrderItem', back_populates='allocation')
    picking_list_items = relationship('PickingListItem', back_populates='allocation')
    consignments = relationship('Consignment', back_populates='allocation')
    stock_movements = relationship('StockMovement', back_populates='allocation')
    racks = relationship('Rack', back_populates='allocation')
    rack_allocations = relationship("RackAllocation", back_populates="allocation", cascade="all, delete-orphan")


    # TAMBAHAN: Contract reference untuk tender
    tender_contract_id = Column(Integer, ForeignKey('tender_contracts.id'), nullable=True)
    tender_contract = relationship('TenderContract', back_populates='allocations')
    
    # Breakdown untuk tender allocation
    original_reserved_quantity = Column(Integer, default=0)  # Original dari contract
    customer_allocated_quantity = Column(Integer, default=0)  # Yang sudah dialokasikan ke customer
    
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
    
    quantity = Column(Integer, nullable=False)
    movement_date = Column(DateTime, default=func.current_timestamp())
    notes = Column(Text)
    
    # Reference ke movement type
    movement_type_id = Column(Integer, ForeignKey('movement_types.id'), nullable=False)
    movement_type = relationship('MovementType', back_populates='stock_movements')
    
    # PERBAIKAN: Reference ke allocation (unit stock yang berubah)
    allocation_id = Column(Integer, ForeignKey('allocations.id'), nullable=False)
    allocation = relationship('Allocation', back_populates='stock_movements')
    
    # Reference ke batch untuk reporting
    batch_id = Column(Integer, ForeignKey('batches.id'), nullable=False)
    batch = relationship('Batch', back_populates='stock_movements')
    
    # TAMBAHAN: Tracking context
    picking_order_item_id = Column(Integer, ForeignKey('picking_order_items.id'), nullable=True)
    picking_order_item = relationship('PickingOrderItem')
    
    rack_id = Column(Integer, ForeignKey('racks.id'), nullable=True)
    rack = relationship('Rack')
    
    # User yang melakukan movement
    created_by = Column(String(50))