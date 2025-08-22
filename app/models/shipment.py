# app/models/shipment.py
# Model untuk Shipment yang mengikuti flow Picking → Packing → Shipment

from app.models.base import BaseModel, db
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from sqlalchemy import Numeric


class Shipment(BaseModel):
    """Model untuk Shipment final setelah proses packing selesai"""
    __tablename__ = 'shipments'
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    shipment_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Reference ke shipping plan yang jadi dasar shipment
    shipping_plan_id = db.Column(db.Integer, db.ForeignKey('shipping_plans.id'), nullable=False)
    shipping_plan = db.relationship('ShippingPlan', back_populates='shipment')
    
    # Customer info (dari shipping plan, tapi dicopy untuk kemudahan)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    customer = db.relationship('Customer')
    
    # Shipping details
    tracking_number = db.Column(db.String(100), unique=True, nullable=True, index=True)
    carrier = db.Column(db.String(100))
    shipping_method = db.Column(db.String(50))  # Express, Regular, Economy
    
    # Dates
    shipment_date = db.Column(db.Date)
    estimated_delivery_date = db.Column(db.Date)
    actual_delivery_date = db.Column(db.Date)
    
    # Status tracking
    status = db.Column(db.String(50), default='PREPARING', nullable=False)
    # PREPARING, READY_TO_SHIP, SHIPPED, IN_TRANSIT, DELIVERED, CANCELLED, RETURNED
    
    # Address information
    delivery_address = db.Column(db.Text)
    pickup_address = db.Column(db.Text)
    contact_person = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    contact_email = db.Column(db.String(100))
    
    # Package information
    total_weight = db.Column(db.Float)  # Total weight in kg
    total_volume = db.Column(db.Float)  # Total volume in m3
    total_boxes = db.Column(db.Integer, default=0)
    
    # Cost information
    shipping_cost = db.Column(db.Numeric(12, 2))
    insurance_cost = db.Column(db.Numeric(12, 2))
    total_value = db.Column(db.Numeric(15, 2))  # Total value of goods
    
    # Tracking
    created_by = db.Column(db.String(50))  # User yang create shipment
    created_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    shipped_by = db.Column(db.String(50))  # User yang confirm shipping
    shipped_date = db.Column(db.DateTime)
    
    # Special instructions
    delivery_instructions = db.Column(db.Text)
    handling_instructions = db.Column(db.Text)
    notes = db.Column(db.Text)
    
    # External references
    courier_booking_id = db.Column(db.String(100))  # ID booking di sistem courier
    pod_document_url = db.Column(db.String(255))  # Proof of Delivery document
    
    # Relationships
    picking_orders = db.relationship('PickingOrder', back_populates='shipment')
    documents = db.relationship('ShipmentDocument', back_populates='shipment', cascade='all, delete-orphan')
    tracking_events = db.relationship('ShipmentTracking', back_populates='shipment', cascade='all, delete-orphan')
    consignments = db.relationship('Consignment', back_populates='shipment')

    # ENHANCED: PS reference (main reference untuk shipment)
    packing_slip_id = db.Column(db.Integer, db.ForeignKey('packing_slips.id'), nullable=False)
    packing_slip = db.relationship('PackingSlip', back_populates='shipments')
    
    # ENHANCED: Flexible delivery address
    # Option 1: Use customer address
    delivery_address_id = db.Column(db.Integer, db.ForeignKey('customer_addresses.id'), nullable=True)
    delivery_address = db.relationship('CustomerAddress', back_populates='shipments')
    
    # Option 2: Custom delivery address (override customer address)
    custom_delivery_address = db.Column(db.Text, nullable=True)
    custom_contact_person = db.Column(db.String(100))
    custom_contact_phone = db.Column(db.String(20))
    custom_delivery_instructions = db.Column(db.Text)
    
    # Flag to determine which address to use
    use_custom_address = db.Column(db.Boolean, default=False)
    
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
    
    id = db.Column(db.Integer, primary_key=True)
    document_type_id = db.Column(db.Integer, db.ForeignKey('document_types.id'), nullable=False)
    document_type = db.relationship('DocumentType', back_populates='shipment_documents')

    document_number = db.Column(db.String(100))
    document_url = db.Column(db.String(255))
    file_name = db.Column(db.String(255))
    file_size = db.Column(db.Integer)  # in bytes
    
    # Reference
    shipment_id = db.Column(db.Integer, db.ForeignKey('shipments.id'), nullable=False)
    shipment = db.relationship('Shipment', back_populates='documents')
    
    # Tracking
    uploaded_by = db.Column(db.String(50))
    uploaded_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    def __repr__(self):
        return f'<ShipmentDocument {self.document_type} - {self.shipment.shipment_number}>'

class ShipmentTracking(BaseModel):
    """Model untuk tracking events dalam shipment"""
    __tablename__ = 'shipment_tracking'
    
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50), nullable=False)  # CREATED, SHIPPED, IN_TRANSIT, DELIVERED, etc
    event_description = db.Column(db.Text)
    event_location = db.Column(db.String(100))
    event_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Reference
    shipment_id = db.Column(db.Integer, db.ForeignKey('shipments.id'), nullable=False)
    shipment = db.relationship('Shipment', back_populates='tracking_events')
    
    # External tracking (dari courier)
    external_tracking_id = db.Column(db.String(100))
    courier_status = db.Column(db.String(100))
    
    # Internal tracking
    created_by = db.Column(db.String(50))
    is_customer_visible = db.Column(db.Boolean, default=True)
    
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
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # Express, Regular, Economy
    description = db.Column(db.Text)
    estimated_days = db.Column(db.Integer)  # Estimasi hari pengiriman
    cost_per_kg = db.Column(db.Numeric(10, 2))
    cost_per_km = db.Column(db.Numeric(10, 2))
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<DeliveryMethod {self.name}>'

class Carrier(BaseModel):
    """Master data untuk kurir/carrier"""
    __tablename__ = 'carriers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # JNE, TIKI, JNT, etc    
    code = db.Column(db.String(10), unique=True, nullable=False)
    contact_info = db.Column(db.Text)
    carrier_type_id = db.Column(db.Integer, db.ForeignKey('carrier_types.id'), nullable=False)
    carrier_type = db.relationship('CarrierType', back_populates='carriers')
    api_endpoint = db.Column(db.String(255))  # Untuk integrasi API
    api_key = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Carrier {self.name}>'