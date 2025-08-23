import uuid
from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, Date, Numeric,
    func
)
from sqlalchemy.orm import relationship
from .base import BaseModel


class TenderContract(BaseModel):
    """Model untuk Contract Tender dari ERP"""
    __tablename__ = 'tender_contracts'
    
    public_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)
    
    # Contract details dari ERP
    contract_number = Column(String(50), unique=True, nullable=False, index=True)
    contract_date = Column(Date, nullable=False)
    contract_value = Column(Numeric(15, 2))
    
    # Contract period
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Tender information
    tender_reference = Column(String(100))
    tender_winner = Column(String(100))
    
    # Status
    status = Column(String(20), default='ACTIVE')
    
    # ERP Integration
    erp_contract_id = Column(String(50))
    erp_sync_date = Column(DateTime)
    
    # Document references
    contract_document_url = Column(String(255))
    
    # Tracking
    created_by = Column(String(50))
    created_date = Column(DateTime, default=func.current_timestamp())
    
    # Relationships
    allocations = relationship('Allocation', back_populates='tender_contract')
    sales_orders = relationship('SalesOrder', back_populates='tender_contract')
    contract_reservations = relationship('ContractReservation', back_populates='contract')
    
    def __repr__(self):
        return f'<TenderContract {self.contract_number}>'

class ContractReservation(BaseModel):
    """Model untuk tracking reserved stock per contract"""
    __tablename__ = 'contract_reservations'
    
    # Contract reference
    contract_id = Column(Integer, ForeignKey('tender_contracts.id'), nullable=False)
    contract = relationship('TenderContract', back_populates='contract_reservations')
    
    # Product & batch reference
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    product = relationship('Product')
    
    batch_id = Column(Integer, ForeignKey('batches.id'), nullable=False)
    batch = relationship('Batch')
    
    # Allocation reference (TENDER allocation)
    allocation_id = Column(Integer, ForeignKey('allocations.id'), nullable=False)
    allocation = relationship('Allocation')
    
    # Reserved quantities
    reserved_quantity = Column(Integer, nullable=False)
    allocated_quantity = Column(Integer, default=0)
    remaining_quantity = Column(Integer, nullable=False)
    
    # Tracking
    created_date = Column(DateTime, default=func.current_timestamp())
    
    @property
    def available_for_allocation(self):
        return self.remaining_quantity
    
    def __repr__(self):
        return f'<ContractReservation {self.contract.contract_number} - {self.product.name}>'