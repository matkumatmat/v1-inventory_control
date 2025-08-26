"""
Consignment Service
===================

Services for Consignment and ConsignmentAgreement management
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, func, desc, select

from ..base import CRUDService, transactional, audit_log
from ..exceptions import ValidationError, BusinessRuleError, ConsignmentError, NotFoundError
from ...models import (
    ConsignmentAgreement, Consignment, ConsignmentItem, Customer,
    Allocation, Product, Batch
)
from ...schemas import (
    ConsignmentAgreementSchema, ConsignmentAgreementCreateSchema, ConsignmentAgreementUpdateSchema,
    ConsignmentSchema, ConsignmentCreateSchema, ConsignmentUpdateSchema,
    ConsignmentItemSchema, ConsignmentItemCreateSchema
)

class ConsignmentAgreementService(CRUDService):
    """Service for Consignment Agreement management"""
    
    model_class = ConsignmentAgreement
    create_schema = ConsignmentAgreementCreateSchema
    update_schema = ConsignmentAgreementUpdateSchema
    response_schema = ConsignmentAgreementSchema
    search_fields = ['agreement_number']
    
    def __init__(self, db_session: AsyncSession, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)
    
    @transactional
    @audit_log('CREATE', 'ConsignmentAgreement')
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create consignment agreement with validation"""
        agreement_number = data.get('agreement_number')
        if agreement_number:
            await self._validate_unique_field(ConsignmentAgreement, 'agreement_number', agreement_number,
                                              error_message=f"Agreement number '{agreement_number}' already exists")
        
        customer = await self._validate_customer_for_consignment(data['customer_id'])
        self._validate_agreement_dates(data)
        
        agreement_data = await super().create(data)
        
        await self._send_notification('CONSIGNMENT_AGREEMENT_CREATED', ['admin', 'sales_team'], {
            'agreement_id': agreement_data['id'],
            'agreement_number': agreement_number,
            'customer_name': customer.name,
            'commission_rate': data.get('commission_rate')
        })
        
        return agreement_data
    
    @transactional
    @audit_log('APPROVE', 'ConsignmentAgreement')
    async def approve_agreement(self, agreement_id: int) -> Dict[str, Any]:
        """Approve consignment agreement"""
        agreement = await self._get_or_404(ConsignmentAgreement, agreement_id)
        
        if agreement.status == 'TERMINATED':
            raise ConsignmentError("Cannot approve terminated agreement")
        
        agreement.status = 'ACTIVE'
        agreement.approved_by = self.current_user
        agreement.approved_date = datetime.utcnow()
        self._set_audit_fields(agreement, is_update=True)
        
        await self._send_notification('CONSIGNMENT_AGREEMENT_APPROVED', ['sales_team', 'customer'], {
            'agreement_id': agreement_id,
            'agreement_number': agreement.agreement_number,
            'customer_name': agreement.customer.name
        })
        
        return self.response_schema().dump(agreement)
    
    @transactional
    @audit_log('TERMINATE', 'ConsignmentAgreement')
    async def terminate_agreement(self, agreement_id: int, reason: str) -> Dict[str, Any]:
        """Terminate consignment agreement"""
        agreement = await self._get_or_404(ConsignmentAgreement, agreement_id)
        
        query = select(func.count(Consignment.id)).filter(
            and_(
                Consignment.agreement_id == agreement_id,
                Consignment.status.in_(['PENDING', 'SHIPPED', 'RECEIVED_BY_CUSTOMER', 'PARTIALLY_SOLD'])
            )
        )
        active_consignments_result = await self.db_session.execute(query)
        active_consignments = active_consignments_result.scalar()
        
        if active_consignments > 0:
            raise ConsignmentError(f"Cannot terminate agreement with {active_consignments} active consignments")
        
        agreement.status = 'TERMINATED'
        agreement.notes = f"Terminated: {reason}. {agreement.notes or ''}"
        self._set_audit_fields(agreement, is_update=True)
        
        await self._send_notification('CONSIGNMENT_AGREEMENT_TERMINATED', ['sales_team', 'customer'], {
            'agreement_id': agreement_id,
            'agreement_number': agreement.agreement_number,
            'reason': reason
        })
        
        return self.response_schema().dump(agreement)
    
    async def get_active_agreements(self, customer_id: int = None) -> List[Dict[str, Any]]:
        """Get active consignment agreements"""
        query = select(ConsignmentAgreement).filter(
            ConsignmentAgreement.status == 'ACTIVE'
        )
        
        if customer_id:
            query = query.filter(ConsignmentAgreement.customer_id == customer_id)
        
        query = query.order_by(ConsignmentAgreement.start_date.desc())
        
        result = await self.db_session.execute(query)
        agreements = result.scalars().all()
        return self.response_schema(many=True).dump(agreements)
    
    async def get_expiring_agreements(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Get agreements that are about to expire"""
        cutoff_date = date.today() + timedelta(days=days_ahead)
        
        query = select(ConsignmentAgreement).filter(
            and_(
                ConsignmentAgreement.status == 'ACTIVE',
                ConsignmentAgreement.end_date <= cutoff_date,
                ConsignmentAgreement.end_date >= date.today()
            )
        ).order_by(ConsignmentAgreement.end_date.asc())
        
        result = await self.db_session.execute(query)
        agreements = result.scalars().all()
        
        response_data = []
        for agreement in agreements:
            agreement_data = self.response_schema().dump(agreement)
            agreement_data['days_remaining'] = (agreement.end_date - date.today()).days
            response_data.append(agreement_data)
        
        return response_data
    
    async def _validate_customer_for_consignment(self, customer_id: int) -> Customer:
        """Validate customer for consignment"""
        customer = await self._get_or_404(Customer, customer_id)
        
        if not customer.is_active:
            raise ValidationError(f"Customer {customer.name} is not active")
        
        return customer
    
    def _validate_agreement_dates(self, data: Dict[str, Any]):
        """Validate agreement date relationships"""
        agreement_date = data.get('agreement_date')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if agreement_date and start_date and agreement_date > start_date:
            raise ValidationError("Agreement date cannot be after start date")
        
        if start_date and end_date and start_date >= end_date:
            raise ValidationError("Start date must be before end date")


class ConsignmentService(CRUDService):
    """Service for Consignment management"""
    
    model_class = Consignment
    create_schema = ConsignmentCreateSchema
    update_schema = ConsignmentUpdateSchema
    response_schema = ConsignmentSchema
    search_fields = ['consignment_number']
    
    def __init__(self, db_session: AsyncSession, current_user: str = None,
                 audit_service=None, notification_service=None, 
                 allocation_service=None, shipment_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)
        self.allocation_service = allocation_service
        self.shipment_service = shipment_service
    
    @transactional
    @audit_log('CREATE', 'Consignment')
    async def create_consignment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create consignment with validation"""
        agreement = await self._validate_agreement(data['agreement_id'])
        await self._get_or_404(Allocation, data['allocation_id'])
        
        data['consignment_number'] = await self._generate_consignment_number()
        
        if not data.get('commission_rate') and agreement.commission_rate:
            data['commission_rate'] = agreement.commission_rate
        
        consignment_data = await super().create(data)
        
        await self._send_notification('CONSIGNMENT_CREATED', ['sales_team', 'warehouse_team'], {
            'consignment_id': consignment_data['id'],
            'consignment_number': data['consignment_number'],
            'agreement_number': agreement.agreement_number,
            'customer_name': agreement.customer.name
        })
        
        return consignment_data
    
    @transactional
    @audit_log('ADD_ITEM', 'Consignment')
    async def add_consignment_item(self, consignment_id: int, 
                                 item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add item to consignment"""
        consignment = await self._get_or_404(Consignment, consignment_id)
        
        if consignment.status not in ['PENDING', 'SHIPPED']:
            raise ConsignmentError(f"Cannot add items to consignment with status {consignment.status}")
        
        product = await self._get_or_404(Product, item_data['product_id'])
        batch = await self._get_or_404(Batch, item_data['batch_id'])
        
        if batch.product_id != product.id:
            raise ValidationError("Batch does not belong to specified product")
        
        item_data['consignment_id'] = consignment_id
        
        validated_data = ConsignmentItemCreateSchema().load(item_data)
        item = ConsignmentItem(**validated_data)
        self._set_audit_fields(item)
        
        self.db_session.add(item)
        await self.db_session.flush()
        
        await self._update_consignment_totals(consignment_id)
        
        return ConsignmentItemSchema().dump(item)
    
    @transactional
    @audit_log('SHIP', 'Consignment')
    async def ship_consignment(self, consignment_id: int, 
                             shipment_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ship consignment"""
        consignment = await self._get_or_404(Consignment, consignment_id)
        
        if consignment.status != 'PENDING':
            raise ConsignmentError(f"Can only ship pending consignments. Current status: {consignment.status}")
        
        items_count_query = select(func.count(ConsignmentItem.id)).filter(
            ConsignmentItem.consignment_id == consignment_id
        )
        items_count_result = await self.db_session.execute(items_count_query)
        items_count = items_count_result.scalar()
        
        if items_count == 0:
            raise ConsignmentError("Cannot ship consignment without items")
        
        shipment_id = None
        if self.shipment_service and shipment_data:
            pass  # Placeholder for shipment creation logic
        
        consignment.status = 'SHIPPED'
        consignment.shipped_by = self.current_user
        consignment.shipped_date = datetime.utcnow()
        consignment.shipment_id = shipment_id
        self._set_audit_fields(consignment, is_update=True)
        
        await self._send_notification('CONSIGNMENT_SHIPPED', ['customer', 'sales_team'], {
            'consignment_id': consignment_id,
            'consignment_number': consignment.consignment_number,
            'total_items': items_count
        })
        
        return self.response_schema().dump(consignment)
    
    @transactional
    @audit_log('RECEIVE', 'Consignment')
    async def confirm_receipt(self, consignment_id: int, 
                            receipt_confirmation: Dict[str, Any]) -> Dict[str, Any]:
        """Confirm consignment receipt by customer"""
        consignment = await self._get_or_404(Consignment, consignment_id)
        
        if consignment.status != 'SHIPPED':
            raise ConsignmentError(f"Can only confirm receipt for shipped consignments. Current status: {consignment.status}")
        
        consignment.status = 'RECEIVED_BY_CUSTOMER'
        
        if receipt_confirmation:
            consignment.notes = f"Received by: {receipt_confirmation.get('received_by')}. {consignment.notes or ''}"
        
        self._set_audit_fields(consignment, is_update=True)
        
        await self._send_notification('CONSIGNMENT_RECEIVED', ['sales_team'], {
            'consignment_id': consignment_id,
            'consignment_number': consignment.consignment_number,
            'received_by': receipt_confirmation.get('received_by')
        })
        
        return self.response_schema().dump(consignment)
    
    async def get_consignment_with_items(self, consignment_id: int) -> Dict[str, Any]:
        """Get consignment with all items"""
        consignment = await self._get_or_404(Consignment, consignment_id)
        
        items_query = select(ConsignmentItem).filter(
            ConsignmentItem.consignment_id == consignment_id
        )
        items_result = await self.db_session.execute(items_query)
        items = items_result.scalars().all()
        
        consignment_data = self.response_schema().dump(consignment)
        consignment_data['items'] = ConsignmentItemSchema(many=True).dump(items)
        
        return consignment_data
    
    async def get_active_consignments(self, customer_id: int = None) -> List[Dict[str, Any]]:
        """Get active consignments"""
        query = select(Consignment).filter(
            Consignment.status.in_(['PENDING', 'SHIPPED', 'RECEIVED_BY_CUSTOMER', 'PARTIALLY_SOLD'])
        )
        
        if customer_id:
            query = query.join(ConsignmentAgreement).filter(
                ConsignmentAgreement.customer_id == customer_id
            )
        
        query = query.order_by(Consignment.consignment_date.desc())
        
        result = await self.db_session.execute(query)
        consignments = result.scalars().all()
        return self.response_schema(many=True).dump(consignments)
    
    async def get_consignment_performance_summary(self, agreement_id: int = None,
                                                start_date: date = None, 
                                                end_date: date = None) -> Dict[str, Any]:
        """Get consignment performance summary"""
        query = select(Consignment)
        
        if agreement_id:
            query = query.filter(Consignment.agreement_id == agreement_id)
        if start_date:
            query = query.filter(Consignment.consignment_date >= start_date)
        if end_date:
            query = query.filter(Consignment.consignment_date <= end_date)
        
        result = await self.db_session.execute(query)
        consignments = result.scalars().all()
        
        total_consignments = len(consignments)
        total_value_shipped = sum(c.total_value or 0 for c in consignments)
        
        by_status = {}
        for c in consignments:
            status = c.status
            if status not in by_status:
                by_status[status] = {'count': 0, 'total_value': 0}
            by_status[status]['count'] += 1
            by_status[status]['total_value'] += c.total_value or 0
        
        return {
            'summary': {
                'total_consignments': total_consignments,
                'total_value_shipped': total_value_shipped
            },
            'by_status': by_status
        }
    
    async def _validate_agreement(self, agreement_id: int) -> ConsignmentAgreement:
        """Validate agreement for consignment"""
        agreement = await self._get_or_404(ConsignmentAgreement, agreement_id)
        
        if agreement.status != 'ACTIVE':
            raise ConsignmentError(f"Agreement {agreement.agreement_number} is not active")
        
        if agreement.end_date and agreement.end_date <= date.today():
            raise ConsignmentError(f"Agreement {agreement.agreement_number} has expired")
        
        return agreement
    
    async def _generate_consignment_number(self) -> str:
        """Generate unique consignment number"""
        today = date.today()
        prefix = f"CS{today.strftime('%y%m%d')}"
        
        query = select(Consignment).filter(
            Consignment.consignment_number.like(f"{prefix}%")
        ).order_by(Consignment.id.desc())
        
        result = await self.db_session.execute(query)
        last_consignment = result.scalars().first()
        
        if last_consignment:
            last_seq = int(last_consignment.consignment_number[-4:])
            next_seq = last_seq + 1
        else:
            next_seq = 1
        
        return f"{prefix}{next_seq:04d}"
    
    async def _update_consignment_totals(self, consignment_id: int):
        """Update consignment totals"""
        consignment = await self._get_or_404(Consignment, consignment_id)
        
        items_query = select(ConsignmentItem).filter(
            ConsignmentItem.consignment_id == consignment_id
        )
        items_result = await self.db_session.execute(items_query)
        items = items_result.scalars().all()
        
        total_quantity_shipped = sum(item.quantity_shipped for item in items)
        total_value = sum(item.total_value or 0 for item in items)
        
        consignment.total_quantity_shipped = total_quantity_shipped
        consignment.total_value = total_value
        self._set_audit_fields(consignment, is_update=True)