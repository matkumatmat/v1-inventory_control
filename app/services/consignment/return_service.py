"""
Consignment Return Service
==========================

Service for Consignment Returns management
"""

from typing import Dict, Any, List
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..base import CRUDService, transactional, audit_log
from ..exceptions import ValidationError, BusinessRuleError, ConsignmentError
from ...models import ConsignmentReturn, Consignment, ConsignmentItem
from ...schemas import ConsignmentReturnSchema, ConsignmentReturnCreateSchema, ConsignmentReturnUpdateSchema

class ConsignmentReturnService(CRUDService):
    """Service for Consignment Returns management"""
    
    model_class = ConsignmentReturn
    create_schema = ConsignmentReturnCreateSchema
    update_schema = ConsignmentReturnUpdateSchema
    response_schema = ConsignmentReturnSchema
    search_fields = ['return_number']

    def __init__(self, db_session: AsyncSession, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)

    @transactional
    @audit_log('CREATE', 'ConsignmentReturn')
    async def initiate_return(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate consignment return"""
        consignment_item = await self._get_or_404(ConsignmentItem, data['consignment_item_id'])
        
        quantity_returned = data['quantity_returned']
        available_for_return = consignment_item.quantity_shipped - consignment_item.quantity_sold - consignment_item.quantity_returned
        
        if quantity_returned > available_for_return:
            raise ConsignmentError(f"Cannot return {quantity_returned}. Available: {available_for_return}")
        
        data['return_number'] = await self._generate_return_number()
        data['consignment_id'] = consignment_item.consignment_id
        data['initiated_by'] = self.current_user
        
        return_data = await super().create(data)
        
        consignment_item.quantity_returned += quantity_returned
        self._set_audit_fields(consignment_item, is_update=True)
        
        await self._send_notification('CONSIGNMENT_RETURN_INITIATED', ['warehouse_team'], {
            'return_id': return_data['id'],
            'return_number': data['return_number'],
            'quantity_returned': quantity_returned,
            'return_reason': data.get('return_reason')
        })
        
        return return_data
    
    @transactional
    @audit_log('RECEIVE', 'ConsignmentReturn')
    async def receive_return(self, return_id: int, reception_data: Dict[str, Any]) -> Dict[str, Any]:
        """Receive returned items"""
        return_record = await self._get_or_404(ConsignmentReturn, return_id)
        
        if return_record.status != 'PENDING':
            raise ConsignmentError(f"Can only receive pending returns. Current status: {return_record.status}")
        
        return_record.status = 'RECEIVED'
        return_record.received_by = self.current_user
        return_record.received_date = datetime.utcnow()
        
        if reception_data:
            return_record.condition = reception_data.get('condition', return_record.condition)
            return_record.notes = f"Received: {reception_data.get('notes', '')}. {return_record.notes or ''}"
        
        self._set_audit_fields(return_record, is_update=True)
        
        return self.response_schema().dump(return_record)
    
    @transactional
    @audit_log('QC', 'ConsignmentReturn')
    async def conduct_qc(self, return_id: int, qc_results: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct QC on returned items"""
        return_record = await self._get_or_404(ConsignmentReturn, return_id)
        
        if return_record.status != 'RECEIVED':
            raise ConsignmentError(f"Can only conduct QC on received returns. Current status: {return_record.status}")
        
        return_record.qc_status = qc_results.get('qc_status', 'PENDING')
        return_record.qc_notes = qc_results.get('qc_notes')
        return_record.qc_by = self.current_user
        return_record.qc_date = datetime.utcnow()
        
        if return_record.qc_status in ['PASSED', 'FAILED']:
            return_record.status = 'QC_DONE'
        
        self._set_audit_fields(return_record, is_update=True)
        
        return self.response_schema().dump(return_record)
    
    @transactional
    @audit_log('PROCESS', 'ConsignmentReturn')
    async def process_return(self, return_id: int, processing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process returned items (restock/dispose)"""
        return_record = await self._get_or_404(ConsignmentReturn, return_id)
        
        if return_record.status != 'QC_DONE':
            raise ConsignmentError(f"Can only process QC-completed returns. Current status: {return_record.status}")
        
        restocked_qty = processing_data.get('restocked_quantity', 0)
        disposed_qty = processing_data.get('disposed_quantity', 0)
        
        if restocked_qty + disposed_qty != return_record.quantity_returned:
            raise ValidationError("Restocked + Disposed must equal returned quantity")
        
        return_record.disposition = processing_data.get('disposition', 'RESTOCK')
        return_record.restocked_quantity = restocked_qty
        return_record.disposed_quantity = disposed_qty
        return_record.status = 'PROCESSED'
        
        self._set_audit_fields(return_record, is_update=True)
        
        # TODO: Update inventory if restocking
        
        return self.response_schema().dump(return_record)
    
    async def get_returns_by_consignment(self, consignment_id: int) -> List[Dict[str, Any]]:
        """Get all returns for a consignment"""
        query = select(ConsignmentReturn).filter(
            ConsignmentReturn.consignment_id == consignment_id
        ).order_by(ConsignmentReturn.return_date.desc())
        
        result = await self.db_session.execute(query)
        returns = result.scalars().all()
        
        return self.response_schema(many=True).dump(returns)
    
    async def _generate_return_number(self) -> str:
        """Generate unique return number"""
        today = date.today()
        prefix = f"CRT{today.strftime('%y%m%d')}"
        
        query = select(ConsignmentReturn).filter(
            ConsignmentReturn.return_number.like(f"{prefix}%")
        ).order_by(ConsignmentReturn.id.desc())
        
        result = await self.db_session.execute(query)
        last_return = result.scalars().first()
        
        if last_return:
            last_seq = int(last_return.return_number[-4:])
            next_seq = last_seq + 1
        else:
            next_seq = 1
        
        return f"{prefix}{next_seq:04d}"