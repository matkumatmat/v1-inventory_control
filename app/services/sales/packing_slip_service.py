"""
Packing Slip Service
====================

Service untuk Packing Slip management
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ..base import CRUDService, transactional, audit_log
from ..exceptions import ValidationError, BusinessRuleError, NotFoundError
from ...models import PackingSlip, SalesOrder, Customer
from ...schemas import PackingSlipSchema, PackingSlipCreateSchema, PackingSlipUpdateSchema

class PackingSlipService(CRUDService):
    """Service untuk Packing Slip management"""
    
    model_class = PackingSlip
    create_schema = PackingSlipCreateSchema
    update_schema = PackingSlipUpdateSchema
    response_schema = PackingSlipSchema
    search_fields = ['ps_number', 'delivery_address', 'notes']
    
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)
    
    @transactional
    @audit_log('CREATE', 'PackingSlip')
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create packing slip dengan validation"""
        # Validate PS number uniqueness
        ps_number = data.get('ps_number')
        if ps_number:
            self._validate_unique_field(PackingSlip, 'ps_number', ps_number,
                                      error_message=f"PS number '{ps_number}' already exists")
        
        # Validate SO exists
        so = self._get_or_404(SalesOrder, data['sales_order_id'])
        
        if so.status not in ['CONFIRMED', 'PROCESSING', 'ALLOCATED']:
            raise BusinessRuleError(f"Cannot create packing slip for SO with status {so.status}")
        
        # Auto-populate customer dari SO
        data['customer_id'] = so.customer_id
        
        # Set default delivery address dari customer
        if not data.get('delivery_address'):
            customer = so.customer
            if customer.default_delivery_address:
                data['delivery_address'] = customer.default_delivery_address
        
        # Create packing slip
        ps_data = super().create(data)
        
        # Send notification
        self._send_notification('PACKING_SLIP_CREATED', ['warehouse_team', 'logistics_team'], {
            'ps_id': ps_data['id'],
            'ps_number': ps_number,
            'so_number': so.so_number,
            'customer_name': so.customer.name
        })
        
        return ps_data
    
    @transactional
    @audit_log('FINALIZE', 'PackingSlip')
    def finalize_packing_slip(self, ps_id: int) -> Dict[str, Any]:
        """Finalize packing slip untuk shipment"""
        ps = self._get_or_404(PackingSlip, ps_id)
        
        if ps.status != 'DRAFT':
            raise BusinessRuleError(f"Only draft packing slips can be finalized. Current status: {ps.status}")
        
        # Validate required fields
        if not ps.delivery_address:
            raise ValidationError("Delivery address is required before finalizing")
        
        # Finalize
        ps.status = 'FINALIZED'
        ps.finalized_by = self.current_user
        ps.finalized_date = datetime.utcnow()
        self._set_audit_fields(ps, is_update=True)
        
        # Send notification
        self._send_notification('PACKING_SLIP_FINALIZED', ['logistics_team', 'shipping_team'], {
            'ps_id': ps_id,
            'ps_number': ps.ps_number
        })
        
        return self.response_schema().dump(ps)
    
    def get_by_ps_number(self, ps_number: str) -> Dict[str, Any]:
        """Get packing slip by PS number"""
        ps = self.db.query(PackingSlip).filter(
            PackingSlip.ps_number == ps_number
        ).first()
        
        if not ps:
            raise NotFoundError('PackingSlip', ps_number)
        
        return self.response_schema().dump(ps)
    
    def get_ready_for_shipment(self) -> List[Dict[str, Any]]:
        """Get packing slips yang ready untuk shipment"""
        query = self.db.query(PackingSlip).filter(
            PackingSlip.status == 'FINALIZED'
        ).order_by(PackingSlip.finalized_date.asc())
        
        packing_slips = query.all()
        return self.response_schema(many=True).dump(packing_slips)
    
    def get_ps_by_customer(self, customer_id: int, 
                          include_shipped: bool = False) -> List[Dict[str, Any]]:
        """Get packing slips untuk customer"""
        query = self.db.query(PackingSlip).filter(
            PackingSlip.customer_id == customer_id
        )
        
        if not include_shipped:
            query = query.filter(PackingSlip.status != 'SHIPPED')
        
        query = query.order_by(PackingSlip.ps_date.desc())
        
        packing_slips = query.all()
        return self.response_schema(many=True).dump(packing_slips)