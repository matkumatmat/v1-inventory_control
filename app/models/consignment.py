import uuid
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Text, DateTime, Date, Numeric, Boolean,
    func
)
from sqlalchemy.orm import relationship
from .base import BaseModel

class ConsignmentAgreement(BaseModel):
    """Model untuk Perjanjian Konsinyasi dengan Customer"""
    __tablename__ = 'consignment_agreements'
    
    public_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)
    agreement_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Customer information
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    customer = relationship('Customer', back_populates='consignment_agreements')
    
    # Agreement details
    agreement_date = Column(Date, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    
    # Terms and conditions
    commission_rate = Column(Numeric(5, 2))  # Percentage commission
    payment_terms_days = Column(Integer, default=30)
    return_policy_days = Column(Integer, default=90)  # Max days untuk return
    
    # Status
    status = Column(String(20), default='ACTIVE')  # ACTIVE, SUSPENDED, TERMINATED, EXPIRED
    
    # Document references
    contract_document_url = Column(String(255))
    terms_document_url = Column(String(255))
    
    # Tracking
    created_by = Column(String(50))
    created_date = Column(DateTime, default=func.current_timestamp())
    approved_by = Column(String(50))
    approved_date = Column(DateTime)
    
    # Relationships
    consignments = relationship('Consignment', back_populates='agreement')
    
    def __repr__(self):
        return f'<ConsignmentAgreement {self.agreement_number}>'

class Consignment(BaseModel):
    """
    Model untuk Consignment - Alokasi khusus untuk titip jual
    Stock keluar dari warehouse tapi masih milik perusahaan sampai terjual
    """
    __tablename__ = 'consignments'
    
    public_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)
    consignment_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Agreement reference
    agreement_id = Column(Integer, ForeignKey('consignment_agreements.id'), nullable=False)
    agreement = relationship('ConsignmentAgreement', back_populates='consignments')
    
    # Allocation reference (Consignment adalah tipe allocation khusus)
    allocation_id = Column(Integer, ForeignKey('allocations.id'), nullable=False)
    allocation = relationship('Allocation', back_populates='consignments')
    
    # Shipment reference (ketika consignment dikirim)
    shipment_id = Column(Integer, ForeignKey('shipments.id'), nullable=True)
    shipment = relationship('Shipment', back_populates='consignments')
    
    # Consignment details
    consignment_date = Column(Date, nullable=False)
    expected_return_date = Column(Date)
    actual_return_date = Column(Date)
    
    # Financial tracking
    total_value = Column(Numeric(15, 2))  # Total value produk yang dikonsinyasi
    commission_rate = Column(Numeric(5, 2))  # Rate komisi untuk consignment ini
    
    # Status tracking
    status = Column(String(20), default='PENDING', nullable=False)
    # PENDING, SHIPPED, RECEIVED_BY_CUSTOMER, PARTIALLY_SOLD, FULLY_SOLD, RETURNED, CANCELLED
    
    # Notes
    notes = Column(Text)
    terms_conditions = Column(Text)
    
    # Tracking
    created_by = Column(String(50))
    created_date = Column(DateTime, default=func.current_timestamp())
    shipped_by = Column(String(50))
    shipped_date = Column(DateTime)
    
    # Relationships
    items = relationship('ConsignmentItem', back_populates='consignment', cascade='all, delete-orphan')
    sales = relationship('ConsignmentSale', back_populates='consignment', cascade='all, delete-orphan')
    returns = relationship('ConsignmentReturn', back_populates='consignment', cascade='all, delete-orphan')
    
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
    
    # References
    consignment_id = Column(Integer, ForeignKey('consignments.id'), nullable=False)
    consignment = relationship('Consignment', back_populates='items')
    
    # Product & batch info (dari allocation)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    product = relationship('Product')
    
    batch_id = Column(Integer, ForeignKey('batches.id'), nullable=False)
    batch = relationship('Batch')
    
    # Quantities
    quantity_shipped = Column(Integer, nullable=False)
    quantity_sold = Column(Integer, default=0)
    quantity_returned = Column(Integer, default=0)
    
    # Pricing
    unit_value = Column(Numeric(12, 2))  # Nilai per unit
    total_value = Column(Numeric(15, 2))  # Total nilai item ini
    selling_price = Column(Numeric(12, 2))  # Harga jual yang disepakati
    
    # Status per item
    status = Column(String(20), default='SHIPPED')  # SHIPPED, PARTIALLY_SOLD, SOLD, RETURNED
    
    # Tracking
    expiry_date = Column(Date)  # Copy dari batch untuk tracking
    lot_number = Column(String(50))  # Copy dari batch
    
    # Notes
    notes = Column(Text)
    
    @property
    def quantity_remaining(self):
        return self.quantity_shipped - self.quantity_sold - self.quantity_returned
    
    def __repr__(self):
        return f'<ConsignmentItem {self.consignment.consignment_number} - {self.product.name}>'

class ConsignmentSale(BaseModel):
    """Model untuk tracking penjualan dari consignment"""
    __tablename__ = 'consignment_sales'
    
    public_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)
    sale_number = Column(String(50), unique=True, nullable=False)
    
    # References
    consignment_id = Column(Integer, ForeignKey('consignments.id'), nullable=False)
    consignment = relationship('Consignment', back_populates='sales')
    
    consignment_item_id = Column(Integer, ForeignKey('consignment_items.id'), nullable=False)
    consignment_item = relationship('ConsignmentItem')
    
    # Sale details
    sale_date = Column(Date, nullable=False)
    quantity_sold = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    total_value = Column(Numeric(15, 2), nullable=False)
    
    # Commission calculation
    commission_rate = Column(Numeric(5, 2))
    commission_amount = Column(Numeric(12, 2))
    net_amount = Column(Numeric(12, 2))  # Amount after commission
    
    # Customer info (end customer yang beli)
    end_customer_name = Column(String(100))
    end_customer_info = Column(Text)
    
    # Document references
    invoice_number = Column(String(50))
    receipt_document_url = Column(String(255))
    
    # Status
    status = Column(String(20), default='CONFIRMED')  # PENDING, CONFIRMED, PAID, CANCELLED
    
    # Tracking
    reported_by = Column(String(50))  # Customer yang report penjualan
    reported_date = Column(DateTime, default=func.current_timestamp())
    verified_by = Column(String(50))
    verified_date = Column(DateTime)
    
    def __repr__(self):
        return f'<ConsignmentSale {self.sale_number}>'

class ConsignmentReturn(BaseModel):
    """Model untuk tracking return dari consignment"""
    __tablename__ = 'consignment_returns'
    
    public_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)
    return_number = Column(String(50), unique=True, nullable=False)
    
    # References
    consignment_id = Column(Integer, ForeignKey('consignments.id'), nullable=False)
    consignment = relationship('Consignment', back_populates='returns')
    
    consignment_item_id = Column(Integer, ForeignKey('consignment_items.id'), nullable=False)
    consignment_item = relationship('ConsignmentItem')
    
    # Return details
    return_date = Column(Date, nullable=False)
    quantity_returned = Column(Integer, nullable=False)
    
    # Return reason and condition
    return_reason = Column(String(100))  # EXPIRED, DAMAGED, UNSOLD, RECALL, etc.
    condition = Column(String(50))  # GOOD, DAMAGED, EXPIRED
    
    # Quality check results
    qc_status = Column(String(20))  # PENDING, PASSED, FAILED
    qc_notes = Column(Text)
    qc_by = Column(String(50))
    qc_date = Column(DateTime)
    
    # Disposition
    disposition = Column(String(50))  # RESTOCK, QUARANTINE, DISPOSE, REWORK
    restocked_quantity = Column(Integer, default=0)
    disposed_quantity = Column(Integer, default=0)
    
    # Document
    return_document_url = Column(String(255))
    photos_url = Column(Text)  # JSON array of photo URLs
    
    # Status
    status = Column(String(20), default='PENDING')  # PENDING, RECEIVED, QC_DONE, PROCESSED
    
    # Tracking
    initiated_by = Column(String(50))
    received_by = Column(String(50))
    received_date = Column(DateTime)
    
    # Notes
    notes = Column(Text)
    
    def __repr__(self):
        return f'<ConsignmentReturn {self.return_number}>'

class ConsignmentStatement(BaseModel):
    """Model untuk statement/laporan konsinyasi periodic"""
    __tablename__ = 'consignment_statements'
    
    public_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)
    statement_number = Column(String(50), unique=True, nullable=False)
    
    # References
    agreement_id = Column(Integer, ForeignKey('consignment_agreements.id'), nullable=False)
    agreement = relationship('ConsignmentAgreement')
    
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    customer = relationship('Customer')
    
    # Period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # Summary totals
    total_shipped_value = Column(Numeric(15, 2))
    total_sold_value = Column(Numeric(15, 2))
    total_returned_value = Column(Numeric(15, 2))
    total_commission = Column(Numeric(12, 2))
    net_amount_due = Column(Numeric(15, 2))
    
    # Payment tracking
    payment_status = Column(String(20), default='PENDING')  # PENDING, PARTIAL, PAID, OVERDUE
    payment_due_date = Column(Date)
    payment_received_date = Column(Date)
    payment_amount = Column(Numeric(15, 2))
    
    # Document
    statement_document_url = Column(String(255))
    
    # Status
    status = Column(String(20), default='DRAFT')  # DRAFT, SENT, CONFIRMED, PAID
    
    # Tracking
    generated_by = Column(String(50))
    generated_date = Column(DateTime, default=func.current_timestamp())
    sent_date = Column(DateTime)
    
    def __repr__(self):
        return f'<ConsignmentStatement {self.statement_number}>'