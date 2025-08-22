from app.models.base import BaseModel, db
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy import Numeric


class TenderContract(BaseModel):
    """Model untuk Contract Tender dari ERP"""
    __tablename__ = 'tender_contracts'
    
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    
    # Contract details dari ERP
    contract_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    contract_date = db.Column(db.Date, nullable=False)
    contract_value = db.Column(db.Numeric(15, 2))
    
    # Contract period
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    
    # Tender information
    tender_reference = db.Column(db.String(100))
    tender_winner = db.Column(db.String(100))
    
    # Status
    status = db.Column(db.String(20), default='ACTIVE')
    
    # ERP Integration
    erp_contract_id = db.Column(db.String(50))
    erp_sync_date = db.Column(db.DateTime)
    
    # Document references
    contract_document_url = db.Column(db.String(255))
    
    # Tracking
    created_by = db.Column(db.String(50))
    created_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationships
    allocations = db.relationship('Allocation', back_populates='tender_contract')
    sales_orders = db.relationship('SalesOrder', back_populates='tender_contract')
    contract_reservations = db.relationship('ContractReservation', back_populates='contract')
    
    def __repr__(self):
        return f'<TenderContract {self.contract_number}>'

class ContractReservation(BaseModel):
    """Model untuk tracking reserved stock per contract"""
    __tablename__ = 'contract_reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Contract reference
    contract_id = db.Column(db.Integer, db.ForeignKey('tender_contracts.id'), nullable=False)
    contract = db.relationship('TenderContract', back_populates='contract_reservations')
    
    # Product & batch reference
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product = db.relationship('Product')
    
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=False)
    batch = db.relationship('Batch')
    
    # Allocation reference (TENDER allocation)
    allocation_id = db.Column(db.Integer, db.ForeignKey('allocations.id'), nullable=False)
    allocation = db.relationship('Allocation')
    
    # Reserved quantities
    reserved_quantity = db.Column(db.Integer, nullable=False)
    allocated_quantity = db.Column(db.Integer, default=0)
    remaining_quantity = db.Column(db.Integer, nullable=False)
    
    # Tracking
    created_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    @property
    def available_for_allocation(self):
        return self.remaining_quantity
    
    def __repr__(self):
        return f'<ContractReservation {self.contract.contract_number} - {self.product.name}>'