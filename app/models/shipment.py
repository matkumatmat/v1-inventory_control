# app/models/shipment.py
# Model untuk Shipment yang mengikuti flow Picking → Packing → Shipment

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Text, DateTime, Date, Numeric, Boolean,
    Float, func
)
from sqlalchemy.orm import relationship
from .base import BaseModel


class Shipment(BaseModel):
    """Model untuk Shipment final setelah proses packing selesai"""
    __tablename__ = 'shipments'
    
    public_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)
    shipment_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Reference ke shipping plan yang jadi dasar shipment
    shipping_plan_id = Column(Integer, ForeignKey('shipping_plans.id'), nullable=False)
    
    # Customer info (dari shipping plan, tapi dicopy untuk kemudahan)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    
    # Shipping details
    tracking_number = Column(String(100), unique=True, nullable=True, index=True)
    carrier = Column(String(100))
    shipping_method = Column(String(50))  # Express, Regular, Economy
    
    # Dates
    shipment_date = Column(Date)
    estimated_delivery_date = Column(Date)
    actual_delivery_date = Column(Date)
    
    # Status tracking
    status = Column(String(50), default='PREPARING', nullable=False)
    # PREPARING, READY_TO_SHIP, SHIPPED, IN_TRANSIT, DELIVERED, CANCELLED, RETURNED
    
    # Address information
    delivery_address = Column(Text)
    pickup_address = Column(Text)
    contact_person = Column(String(100))
    contact_phone = Column(String(20))
    contact_email = Column(String(100))
    
    # Package information
    total_weight = Column(Float)  # Total weight in kg
    total_volume = Column(Float)  # Total volume in m3
    total_boxes = Column(Integer, default=0)
    
    # Cost information
    shipping_cost = Column(Numeric(12, 2))
    insurance_cost = Column(Numeric(12, 2))
    total_value = Column(Numeric(15, 2))  # Total value of goods
    
    # Tracking
    created_by = Column(String(50))  # User yang create shipment
    created_date = Column(DateTime, default=func.current_timestamp())
    shipped_by = Column(String(50))  # User yang confirm shipping
    shipped_date = Column(DateTime)
    
    # Special instructions
    delivery_instructions = Column(Text)
    handling_instructions = Column(Text)
    notes = Column(Text)
    
    # External references
    courier_booking_id = Column(String(100))  # ID booking di sistem courier
    pod_document_url = Column(String(255))  # Proof of Delivery document
    
    # Relationships
    shipping_plan = relationship('ShippingPlan', back_populates='shipment')
    customer = relationship('Customer')
    picking_orders = relationship('PickingOrder', back_populates='shipment')
    documents = relationship('ShipmentDocument', back_populates='shipment', cascade='all, delete-orphan')
    tracking_events = relationship('ShipmentTracking', back_populates='shipment', cascade='all, delete-orphan')
    consignments = relationship('Consignment', back_populates='shipment')

    # ENHANCED: PS reference (main reference untuk shipment)
    packing_slip_id = Column(Integer, ForeignKey('packing_slips.id'), nullable=False)
    packing_slip = relationship('PackingSlip', back_populates='shipments')
    
    # ENHANCED: Flexible delivery address
    # Option 1: Use customer address
    delivery_address_id = Column(Integer, ForeignKey('customer_addresses.id'), nullable=True)
    delivery_address = relationship('CustomerAddress', back_populates='shipments')
    
    # Option 2: Custom delivery address (override customer address)
    custom_delivery_address = Column(Text, nullable=True)
    custom_contact_person = Column(String(100))
    custom_contact_phone = Column(String(20))
    custom_delivery_instructions = Column(Text)
    
    # Flag to determine which address to use
    use_custom_address = Column(Boolean, default=False)
    
    # Properties untuk final delivery info
    @property
    def final_delivery_address(self):
        if self.use_custom_address:
            return self.custom_delivery_address
        elif self.delivery_address:
            return f"{self.delivery_address.address_line1}, {self.delivery_address.city}"
        else:
            return self.customer.default_address.address_line1 if self.customer.default_address else None
    
    @property
    def final_contact_person(self):
        if self.use_custom_address:
            return self.custom_contact_person
        elif self.delivery_address:
            return self.delivery_address.contact_person
        else:
            return self.customer.default_address.contact_person if self.customer.default_address else None
    
    @property
    def final_contact_phone(self):
        if self.use_custom_address:
            return self.custom_contact_phone
        elif self.delivery_address:
            return self.delivery_address.contact_phone
        else:
            return self.customer.default_address.contact_phone if self.customer.default_address else None
    
    # Computed properties
    @property
    def sales_order(self):
        """Get sales order melalui shipping plan"""
        return self.shipping_plan.sales_order if self.shipping_plan else None
    
    @property
    def so_number(self):
        """Get SO number untuk kemudahan"""
        return self.sales_order.so_number if self.sales_order else None
    
    @property
    def total_items(self):
        """Total items dalam shipment"""
        total = 0
        for picking_order in self.picking_orders:
            total += len(picking_order.items)
        return total
    
    @property
    def is_delivered(self):
        """Apakah shipment sudah delivered"""
        return self.status == 'DELIVERED' and self.actual_delivery_date is not None
    
    @property
    def days_in_transit(self):
        """Berapa hari dalam transit"""
        if self.shipped_date and self.actual_delivery_date:
            return (self.actual_delivery_date.date() - self.shipped_date.date()).days
        return None
    
    def __repr__(self):
        return f'<Shipment {self.shipment_number}>'
    
    def to_dict(self):
        """Convert to dictionary untuk API response"""
        return {
            'id': self.id,
            'public_id': str(self.public_id),
            'shipment_number': self.shipment_number,
            'tracking_number': self.tracking_number,
            'carrier': self.carrier,
            'status': self.status,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name if self.customer else None,
            'so_number': self.so_number,
            'shipment_date': self.shipment_date.isoformat() if self.shipment_date else None,
            'estimated_delivery_date': self.estimated_delivery_date.isoformat() if self.estimated_delivery_date else None,
            'actual_delivery_date': self.actual_delivery_date.isoformat() if self.actual_delivery_date else None,
            'total_weight': float(self.total_weight) if self.total_weight else None,
            'total_boxes': self.total_boxes,
            'shipping_cost': float(self.shipping_cost) if self.shipping_cost else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ShipmentDocument(BaseModel):
    """Model untuk dokumen-dokumen yang terkait dengan shipment"""
    __tablename__ = 'shipment_documents'
    
    document_type_id = Column(Integer, ForeignKey('document_types.id'), nullable=False)
    document_type = relationship('DocumentType', back_populates='shipment_documents')

    document_number = Column(String(100))
    document_url = Column(String(255))
    file_name = Column(String(255))
    file_size = Column(Integer)  # in bytes
    
    # Reference
    shipment_id = Column(Integer, ForeignKey('shipments.id'), nullable=False)
    shipment = relationship('Shipment', back_populates='documents')
    
    # Tracking
    uploaded_by = Column(String(50))
    uploaded_date = Column(DateTime, default=func.current_timestamp())
    
    def __repr__(self):
        return f'<ShipmentDocument {self.document_type} - {self.shipment.shipment_number}>'

class ShipmentTracking(BaseModel):
    """Model untuk tracking events dalam shipment"""
    __tablename__ = 'shipment_tracking'
    
    event_type = Column(String(50), nullable=False)  # CREATED, SHIPPED, IN_TRANSIT, DELIVERED, etc
    event_description = Column(Text)
    event_location = Column(String(100))
    event_date = Column(DateTime, default=func.current_timestamp())
    
    # Reference
    shipment_id = Column(Integer, ForeignKey('shipments.id'), nullable=False)
    shipment = relationship('Shipment', back_populates='tracking_events')
    
    # External tracking (dari courier)
    external_tracking_id = Column(String(100))
    courier_status = Column(String(100))
    
    # Internal tracking
    created_by = Column(String(50))
    is_customer_visible = Column(Boolean, default=True)
    
    def __repr__(self):
        return f'<ShipmentTracking {self.event_type} - {self.shipment.shipment_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_type': self.event_type,
            'event_description': self.event_description,
            'event_location': self.event_location,
            'event_date': self.event_date.isoformat() if self.event_date else None,
            'courier_status': self.courier_status
        }

# Additional helper models for shipment management

class DeliveryMethod(BaseModel):
    """Master data untuk metode pengiriman"""
    __tablename__ = 'delivery_methods'
    
    name = Column(String(100), unique=True, nullable=False)  # Express, Regular, Economy
    description = Column(Text)
    estimated_days = Column(Integer)  # Estimasi hari pengiriman
    cost_per_kg = Column(Numeric(10, 2))
    cost_per_km = Column(Numeric(10, 2))
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f'<DeliveryMethod {self.name}>'

class Carrier(BaseModel):
    """Master data untuk kurir/carrier"""
    __tablename__ = 'carriers'
    
    name = Column(String(100), unique=True, nullable=False)  # JNE, TIKI, JNT, etc    
    code = Column(String(10), unique=True, nullable=False)
    contact_info = Column(Text)
    carrier_type_id = Column(Integer, ForeignKey('carrier_types.id'), nullable=False)
    carrier_type = relationship('CarrierType', back_populates='carriers')
    api_endpoint = Column(String(255))  # Untuk integrasi API
    api_key = Column(String(255))
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f'<Carrier {self.name}>'