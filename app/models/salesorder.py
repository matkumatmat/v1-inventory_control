# app/models/salesorder.py
# Model lengkap untuk Sales Order dan Shipping Plan sesuai flow kerja

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Text, DateTime, Date, Numeric, Boolean,
    func
)
from sqlalchemy.orm import relationship
from .base import BaseModel

class SalesOrder(BaseModel):
    """Model untuk Sales Order yang diinput manual dari ERP"""
    __tablename__ = 'sales_orders'
    
    public_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)
    so_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Customer information
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    customer = relationship('Customer', back_populates='sales_orders')
    
    # SO Details
    so_date = Column(Date, nullable=False)
    delivery_date = Column(Date)
    total_amount = Column(Numeric(15, 2))
    currency = Column(String(3), default='IDR')
    
    # Status tracking
    status = Column(String(50), default='PENDING', nullable=False)  
    # PENDING, CONFIRMED, PARTIALLY_PLANNED, FULLY_PLANNED, COMPLETED, CANCELLED
    
    # ERP Integration
    erp_so_id = Column(String(50))  # ID dari ERP pusat
    erp_sync_date = Column(DateTime)
    
    # Manual input tracking
    input_by = Column(String(50))  # User yang input manual
    input_date = Column(DateTime, default=func.current_timestamp())
    
    # Notes
    notes = Column(Text)
    special_instructions = Column(Text)
    
    # Relationships
    items = relationship('SalesOrderItem', back_populates='sales_order', cascade='all, delete-orphan')
    shipping_plans = relationship('ShippingPlan', back_populates='sales_order')

    # TAMBAHAN: Contract reference untuk tender SO
    tender_contract_id = Column(Integer, ForeignKey('tender_contracts.id'), nullable=True)
    tender_contract = relationship('TenderContract', back_populates='sales_orders')
    
    # TAMBAHAN: PS reference
    packing_slip_id = Column(Integer, ForeignKey('packing_slips.id'), nullable=True)
    packing_slip = relationship('PackingSlip', back_populates='sales_orders')
    
    # Flag untuk tipe SO
    is_tender_so = Column(Boolean, default=False)
    
    # Properties
    @property
    def so_type(self):
        return 'TENDER' if self.is_tender_so else 'REGULAR'    
    
    # Computed properties
    @property
    def total_quantity_requested(self):
        """Total quantity dari semua items dalam SO"""
        return sum(item.quantity_requested for item in self.items)
    
    @property
    def total_quantity_planned(self):
        """Total quantity yang sudah masuk shipping plan"""
        total = 0
        for item in self.items:
            total += sum(spi.quantity_to_fulfill for spi in item.shipping_plan_items)
        return total
    
    @property
    def is_fully_planned(self):
        """Apakah SO sudah fully planned"""
        return self.total_quantity_planned >= self.total_quantity_requested
    
    def __repr__(self):
        return f'<SalesOrder {self.so_number}>'

class SalesOrderItem(BaseModel):
    """Detail item dalam Sales Order"""
    __tablename__ = 'sales_order_items'
    
    line_number = Column(Integer)
    quantity_requested = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2))
    total_price = Column(Numeric(15, 2))
    
    # Product reference
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    product = relationship('Product', back_populates='sales_order_items')
    
    # SO reference
    sales_order_id = Column(Integer, ForeignKey('sales_orders.id'), nullable=False)
    sales_order = relationship('SalesOrder', back_populates='items')
    
    # Requirements
    required_delivery_date = Column(Date)
    temperature_requirement = Column(String(50))  # Cold, Frozen, Ambient
    special_handling = Column(Text)
    
    # Status tracking
    status = Column(String(50), default='PENDING')  # PENDING, PLANNED, COMPLETED
    
    # ERP details
    erp_item_id = Column(String(50))
    
    # Relationships
    shipping_plan_items = relationship('ShippingPlanItem', back_populates='sales_order_item', cascade='all, delete-orphan')
    
    # Computed properties
    @property
    def quantity_planned(self):
        """Total quantity yang sudah masuk shipping plan"""
        return sum(spi.quantity_to_fulfill for spi in self.shipping_plan_items)
    
    @property
    def quantity_remaining(self):
        """Quantity yang belum direncanakan"""
        return self.quantity_requested - self.quantity_planned
    
    @property
    def is_fully_planned(self):
        """Apakah item sudah fully planned"""
        return self.quantity_planned >= self.quantity_requested
    
    def __repr__(self):
        return f'<SalesOrderItem {self.sales_order.so_number}-{self.line_number}>'

class ShippingPlan(BaseModel):
    """Model untuk Rencana Pengiriman yang dibuat tim penjualan"""
    __tablename__ = 'shipping_plans'
    
    public_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)
    plan_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Planning details
    planned_delivery_date = Column(Date, nullable=False)
    actual_delivery_date = Column(Date)
    
    # Reference ke SO
    sales_order_id = Column(Integer, ForeignKey('sales_orders.id'), nullable=False)
    sales_order = relationship('SalesOrder', back_populates='shipping_plans')
    
    # Customer (dari SO, tapi diambil untuk kemudahan query)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    customer = relationship('Customer')
    
    # Planning details
    priority = Column(String(20), default='NORMAL')  # HIGH, NORMAL, LOW
    shipping_method = Column(String(50))  # Express, Regular, Economy
    
    # Status tracking
    status = Column(String(50), default='PENDING', nullable=False)
    # PENDING, CONFIRMED, PICKING_LIST_CREATED, IN_PROGRESS, COMPLETED, CANCELLED
    
    # Tracking
    created_by = Column(String(50))  # Tim penjualan yang buat plan
    created_date = Column(DateTime, default=func.current_timestamp())
    confirmed_by = Column(String(50))
    confirmed_date = Column(DateTime)
    
    # Notes
    notes = Column(Text)
    delivery_address = Column(Text)
    contact_person = Column(String(100))
    contact_phone = Column(String(20))
    
    # Relationships
    items = relationship('ShippingPlanItem', back_populates='shipping_plan', cascade='all, delete-orphan')
    picking_lists = relationship('PickingList', back_populates='shipping_plan')
    shipment = relationship('Shipment', back_populates='shipping_plan', uselist=False)
    
    # Computed properties
    @property
    def total_quantity(self):
        """Total quantity dalam shipping plan"""
        return sum(item.quantity_to_fulfill for item in self.items)
    
    @property
    def total_products(self):
        """Total jenis produk dalam shipping plan"""
        return len(self.items)
    
    @property
    def has_picking_list(self):
        """Apakah sudah ada picking list"""
        return len(self.picking_lists) > 0
    
    def __repr__(self):
        return f'<ShippingPlan {self.plan_number}>'

class ShippingPlanItem(BaseModel):
    """Detail item dalam Shipping Plan"""
    __tablename__ = 'shipping_plan_items'
    
    quantity_to_fulfill = Column(Integer, nullable=False)
    
    # References
    shipping_plan_id = Column(Integer, ForeignKey('shipping_plans.id'), nullable=False)
    shipping_plan = relationship('ShippingPlan', back_populates='items')
    
    sales_order_item_id = Column(Integer, ForeignKey('sales_order_items.id'), nullable=False)
    sales_order_item = relationship('SalesOrderItem', back_populates='shipping_plan_items')
    
    # Planning details
    line_number = Column(Integer)  # Urutan dalam shipping plan
    planned_date = Column(Date)
    
    # Requirements (copied from SO item untuk kemudahan)
    temperature_requirement = Column(String(50))
    special_handling = Column(Text)
    
    # Status tracking
    status = Column(String(50), default='PENDING')  # PENDING, PICKING_LIST_CREATED, COMPLETED
    
    # Notes
    notes = Column(Text)
    
    # Relationships
    picking_list_items = relationship('PickingListItem', back_populates='shipping_plan_item')
    
    # Properties untuk kemudahan akses
    @property
    def product(self):
        """Get product dari SO item"""
        return self.sales_order_item.product if self.sales_order_item else None
    
    @property
    def sales_order(self):
        """Get sales order dari SO item"""
        return self.sales_order_item.sales_order if self.sales_order_item else None
    
    @property
    def customer(self):
        """Get customer dari shipping plan"""
        return self.shipping_plan.customer if self.shipping_plan else None
    
    @property
    def is_picking_list_created(self):
        """Apakah sudah ada picking list untuk item ini"""
        return len(self.picking_list_items) > 0
    
    def __repr__(self):
        return f'<ShippingPlanItem {self.shipping_plan.plan_number}-{self.line_number}>'