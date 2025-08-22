from app.models.base import BaseModel, db
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from sqlalchemy import Numeric

class ConsignmentAgreement(BaseModel):
    """Model untuk Perjanjian Konsinyasi dengan Customer"""
    __tablename__ = 'consignment_agreements'
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    agreement_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Customer information
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    customer = db.relationship('Customer', back_populates='consignment_agreements')
    
    # Agreement details
    agreement_date = db.Column(db.Date, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    
    # Terms and conditions
    commission_rate = db.Column(db.Numeric(5, 2))  # Percentage commission
    payment_terms_days = db.Column(db.Integer, default=30)
    return_policy_days = db.Column(db.Integer, default=90)  # Max days untuk return
    
    # Status
    status = db.Column(db.String(20), default='ACTIVE')  # ACTIVE, SUSPENDED, TERMINATED, EXPIRED
    
    # Document references
    contract_document_url = db.Column(db.String(255))
    terms_document_url = db.Column(db.String(255))
    
    # Tracking
    created_by = db.Column(db.String(50))
    created_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    approved_by = db.Column(db.String(50))
    approved_date = db.Column(db.DateTime)
    
    # Relationships
    consignments = db.relationship('Consignment', back_populates='agreement')
    
    def __repr__(self):
        return f'<ConsignmentAgreement {self.agreement_number}>'

class Consignment(BaseModel):
    """
    Model untuk Consignment - Alokasi khusus untuk titip jual
    Stock keluar dari warehouse tapi masih milik perusahaan sampai terjual
    """
    __tablename__ = 'consignments'
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    consignment_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Agreement reference
    agreement_id = db.Column(db.Integer, db.ForeignKey('consignment_agreements.id'), nullable=False)
    agreement = db.relationship('ConsignmentAgreement', back_populates='consignments')
    
    # Allocation reference (Consignment adalah tipe allocation khusus)
    allocation_id = db.Column(db.Integer, db.ForeignKey('allocations.id'), nullable=False)
    allocation = db.relationship('Allocation', back_populates='consignments')
    
    # Shipment reference (ketika consignment dikirim)
    shipment_id = db.Column(db.Integer, db.ForeignKey('shipments.id'), nullable=True)
    shipment = db.relationship('Shipment', back_populates='consignments')
    
    # Consignment details
    consignment_date = db.Column(db.Date, nullable=False)
    expected_return_date = db.Column(db.Date)
    actual_return_date = db.Column(db.Date)
    
    # Financial tracking
    total_value = db.Column(db.Numeric(15, 2))  # Total value produk yang dikonsinyasi
    commission_rate = db.Column(db.Numeric(5, 2))  # Rate komisi untuk consignment ini
    
    # Status tracking
    status = db.Column(db.String(20), default='PENDING', nullable=False)
    # PENDING, SHIPPED, RECEIVED_BY_CUSTOMER, PARTIALLY_SOLD, FULLY_SOLD, RETURNED, CANCELLED
    
    # Notes
    notes = db.Column(db.Text)
    terms_conditions = db.Column(db.Text)
    
    # Tracking
    created_by = db.Column(db.String(50))
    created_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    shipped_by = db.Column(db.String(50))
    shipped_date = db.Column(db.DateTime)
    
    # Relationships
    items = db.relationship('ConsignmentItem', back_populates='consignment', cascade='all, delete-orphan')
    sales = db.relationship('ConsignmentSale', back_populates='consignment', cascade='all, delete-orphan')
    returns = db.relationship('ConsignmentReturn', back_populates='consignment', cascade='all, delete-orphan')
    
    # Properties untuk kemudahan akses
    @property
    def customer(self):
        return self.agreement.customer if self.agreement else None
    
    @property
    def total_quantity_shipped(self):
        return sum(item.quantity_shipped for item in self.items)
    
    @property
    def total_quantity_sold(self):
        return sum(sale.quantity_sold for sale in self.sales)
    
    @property
    def total_quantity_returned(self):
        return sum(ret.quantity_returned for ret in self.returns)
    
    @property
    def total_quantity_remaining(self):
        return self.total_quantity_shipped - self.total_quantity_sold - self.total_quantity_returned
    
    @property
    def total_sales_value(self):
        return sum(sale.total_value for sale in self.sales)
    
    @property
    def total_commission_earned(self):
        return sum(sale.commission_amount for sale in self.sales)
    
    def __repr__(self):
        return f'<Consignment {self.consignment_number}>'

class ConsignmentItem(BaseModel):
    """Detail item dalam consignment"""
    __tablename__ = 'consignment_items'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # References
    consignment_id = db.Column(db.Integer, db.ForeignKey('consignments.id'), nullable=False)
    consignment = db.relationship('Consignment', back_populates='items')
    
    # Product & batch info (dari allocation)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product = db.relationship('Product')
    
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=False)
    batch = db.relationship('Batch')
    
    # Quantities
    quantity_shipped = db.Column(db.Integer, nullable=False)
    quantity_sold = db.Column(db.Integer, default=0)
    quantity_returned = db.Column(db.Integer, default=0)
    
    # Pricing
    unit_value = db.Column(db.Numeric(12, 2))  # Nilai per unit
    total_value = db.Column(db.Numeric(15, 2))  # Total nilai item ini
    selling_price = db.Column(db.Numeric(12, 2))  # Harga jual yang disepakati
    
    # Status per item
    status = db.Column(db.String(20), default='SHIPPED')  # SHIPPED, PARTIALLY_SOLD, SOLD, RETURNED
    
    # Tracking
    expiry_date = db.Column(db.Date)  # Copy dari batch untuk tracking
    lot_number = db.Column(db.String(50))  # Copy dari batch
    
    # Notes
    notes = db.Column(db.Text)
    
    @property
    def quantity_remaining(self):
        return self.quantity_shipped - self.quantity_sold - self.quantity_returned
    
    def __repr__(self):
        return f'<ConsignmentItem {self.consignment.consignment_number} - {self.product.name}>'

class ConsignmentSale(BaseModel):
    """Model untuk tracking penjualan dari consignment"""
    __tablename__ = 'consignment_sales'
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    sale_number = db.Column(db.String(50), unique=True, nullable=False)
    
    # References
    consignment_id = db.Column(db.Integer, db.ForeignKey('consignments.id'), nullable=False)
    consignment = db.relationship('Consignment', back_populates='sales')
    
    consignment_item_id = db.Column(db.Integer, db.ForeignKey('consignment_items.id'), nullable=False)
    consignment_item = db.relationship('ConsignmentItem')
    
    # Sale details
    sale_date = db.Column(db.Date, nullable=False)
    quantity_sold = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    total_value = db.Column(db.Numeric(15, 2), nullable=False)
    
    # Commission calculation
    commission_rate = db.Column(db.Numeric(5, 2))
    commission_amount = db.Column(db.Numeric(12, 2))
    net_amount = db.Column(db.Numeric(12, 2))  # Amount after commission
    
    # Customer info (end customer yang beli)
    end_customer_name = db.Column(db.String(100))
    end_customer_info = db.Column(db.Text)
    
    # Document references
    invoice_number = db.Column(db.String(50))
    receipt_document_url = db.Column(db.String(255))
    
    # Status
    status = db.Column(db.String(20), default='CONFIRMED')  # PENDING, CONFIRMED, PAID, CANCELLED
    
    # Tracking
    reported_by = db.Column(db.String(50))  # Customer yang report penjualan
    reported_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    verified_by = db.Column(db.String(50))
    verified_date = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<ConsignmentSale {self.sale_number}>'

class ConsignmentReturn(BaseModel):
    """Model untuk tracking return dari consignment"""
    __tablename__ = 'consignment_returns'
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    return_number = db.Column(db.String(50), unique=True, nullable=False)
    
    # References
    consignment_id = db.Column(db.Integer, db.ForeignKey('consignments.id'), nullable=False)
    consignment = db.relationship('Consignment', back_populates='returns')
    
    consignment_item_id = db.Column(db.Integer, db.ForeignKey('consignment_items.id'), nullable=False)
    consignment_item = db.relationship('ConsignmentItem')
    
    # Return details
    return_date = db.Column(db.Date, nullable=False)
    quantity_returned = db.Column(db.Integer, nullable=False)
    
    # Return reason and condition
    return_reason = db.Column(db.String(100))  # EXPIRED, DAMAGED, UNSOLD, RECALL, etc.
    condition = db.Column(db.String(50))  # GOOD, DAMAGED, EXPIRED
    
    # Quality check results
    qc_status = db.Column(db.String(20))  # PENDING, PASSED, FAILED
    qc_notes = db.Column(db.Text)
    qc_by = db.Column(db.String(50))
    qc_date = db.Column(db.DateTime)
    
    # Disposition
    disposition = db.Column(db.String(50))  # RESTOCK, QUARANTINE, DISPOSE, REWORK
    restocked_quantity = db.Column(db.Integer, default=0)
    disposed_quantity = db.Column(db.Integer, default=0)
    
    # Document
    return_document_url = db.Column(db.String(255))
    photos_url = db.Column(db.Text)  # JSON array of photo URLs
    
    # Status
    status = db.Column(db.String(20), default='PENDING')  # PENDING, RECEIVED, QC_DONE, PROCESSED
    
    # Tracking
    initiated_by = db.Column(db.String(50))
    received_by = db.Column(db.String(50))
    received_date = db.Column(db.DateTime)
    
    # Notes
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<ConsignmentReturn {self.return_number}>'

class ConsignmentStatement(BaseModel):
    """Model untuk statement/laporan konsinyasi periodic"""
    __tablename__ = 'consignment_statements'
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    statement_number = db.Column(db.String(50), unique=True, nullable=False)
    
    # References
    agreement_id = db.Column(db.Integer, db.ForeignKey('consignment_agreements.id'), nullable=False)
    agreement = db.relationship('ConsignmentAgreement')
    
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    customer = db.relationship('Customer')
    
    # Period
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    
    # Summary totals
    total_shipped_value = db.Column(db.Numeric(15, 2))
    total_sold_value = db.Column(db.Numeric(15, 2))
    total_returned_value = db.Column(db.Numeric(15, 2))
    total_commission = db.Column(db.Numeric(12, 2))
    net_amount_due = db.Column(db.Numeric(15, 2))
    
    # Payment tracking
    payment_status = db.Column(db.String(20), default='PENDING')  # PENDING, PARTIAL, PAID, OVERDUE
    payment_due_date = db.Column(db.Date)
    payment_received_date = db.Column(db.Date)
    payment_amount = db.Column(db.Numeric(15, 2))
    
    # Document
    statement_document_url = db.Column(db.String(255))
    
    # Status
    status = db.Column(db.String(20), default='DRAFT')  # DRAFT, SENT, CONFIRMED, PAID
    
    # Tracking
    generated_by = db.Column(db.String(50))
    generated_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    sent_date = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<ConsignmentStatement {self.statement_number}>'