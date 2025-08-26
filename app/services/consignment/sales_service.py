"""
Consignment Sales Service
=========================

Service for Consignment Sales management
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..base import CRUDService, transactional, audit_log
from ..exceptions import ValidationError, BusinessRuleError, ConsignmentError, NotFoundError
from ...models import ConsignmentSale, Consignment, ConsignmentItem
from ...schemas import ConsignmentSaleSchema, ConsignmentSaleCreateSchema, ConsignmentSaleUpdateSchema

class ConsignmentSalesService(CRUDService):
    """Service for Consignment Sales management"""
    
    model_class = ConsignmentSale
    create_schema = ConsignmentSaleCreateSchema
    update_schema = ConsignmentSaleUpdateSchema
    response_schema = ConsignmentSaleSchema
    search_fields = ['sale_number', 'end_customer_name', 'invoice_number']
    
    def __init__(self, db_session: AsyncSession, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)
    
    @transactional
    @audit_log('CREATE', 'ConsignmentSale')
    async def record_sale(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Record consignment sale"""
        result = await self.db_session.execute(
            select(ConsignmentItem).options(select.joinedload(ConsignmentItem.consignment)).filter(ConsignmentItem.id == data['consignment_item_id'])
        )
        consignment_item = result.scalars().first()

        if not consignment_item:
            raise NotFoundError("ConsignmentItem", data['consignment_item_id'])

        consignment = consignment_item.consignment
        
        quantity_sold = data['quantity_sold']
        available_qty = consignment_item.quantity_shipped - consignment_item.quantity_sold
        
        if quantity_sold > available_qty:
            raise ConsignmentError(f"Cannot sell {quantity_sold}. Available: {available_qty}")
        
        unit_price = data['unit_price']
        total_value = quantity_sold * unit_price
        commission_rate = data.get('commission_rate') or consignment.commission_rate or 0
        commission_amount = total_value * (commission_rate / 100)
        net_amount = total_value - commission_amount
        
        data.update({
            'consignment_id': consignment.id,
            'sale_number': await self._generate_sale_number(),
            'total_value': total_value,
            'commission_rate': commission_rate,
            'commission_amount': commission_amount,
            'net_amount': net_amount,
            'reported_by': self.current_user,
            'reported_date': datetime.utcnow()
        })
        
        sale_data = await super().create(data)
        
        consignment_item.quantity_sold += quantity_sold
        
        if consignment_item.quantity_sold >= consignment_item.quantity_shipped:
            consignment_item.status = 'SOLD'
        elif consignment_item.quantity_sold > 0:
            consignment_item.status = 'PARTIALLY_SOLD'
        
        self._set_audit_fields(consignment_item, is_update=True)
        
        await self._update_consignment_status(consignment.id)
        
        await self._send_notification('CONSIGNMENT_SALE_RECORDED', ['sales_team'], {
            'sale_id': sale_data['id'],
            'sale_number': data['sale_number'],
            'consignment_number': consignment.consignment_number,
            'quantity_sold': quantity_sold,
            'total_value': total_value
        })
        
        return sale_data
    
    @transactional
    @audit_log('VERIFY', 'ConsignmentSale')
    async def verify_sale(self, sale_id: int, verification_notes: str = None) -> Dict[str, Any]:
        """Verify consignment sale"""
        sale = await self._get_or_404(ConsignmentSale, sale_id)
        
        if sale.status != 'PENDING':
            raise ConsignmentError(f"Can only verify pending sales. Current status: {sale.status}")
        
        sale.status = 'CONFIRMED'
        sale.verified_by = self.current_user
        sale.verified_date = datetime.utcnow()
        
        if verification_notes:
            sale.notes = f"Verified: {verification_notes}. {sale.notes or ''}"
        
        self._set_audit_fields(sale, is_update=True)
        
        return self.response_schema().dump(sale)
    
    @transactional
    @audit_log('CANCEL', 'ConsignmentSale')
    async def cancel_sale(self, sale_id: int, reason: str) -> Dict[str, Any]:
        """Cancel consignment sale"""
        sale = await self._get_or_404(ConsignmentSale, sale_id)
        
        if sale.status == 'PAID':
            raise ConsignmentError("Cannot cancel paid sales")
        
        consignment_item = await self._get_or_404(ConsignmentItem, sale.consignment_item_id)
        consignment_item.quantity_sold -= sale.quantity_sold
        
        if consignment_item.quantity_sold == 0:
            consignment_item.status = 'SHIPPED'
        elif consignment_item.quantity_sold < consignment_item.quantity_shipped:
            consignment_item.status = 'PARTIALLY_SOLD'
        
        self._set_audit_fields(consignment_item, is_update=True)
        
        sale.status = 'CANCELLED'
        sale.notes = f"Cancelled: {reason}. {sale.notes or ''}"
        self._set_audit_fields(sale, is_update=True)
        
        await self._update_consignment_status(sale.consignment_id)
        
        return self.response_schema().dump(sale)
    
    async def get_sales_by_consignment(self, consignment_id: int) -> List[Dict[str, Any]]:
        """Get all sales for a consignment"""
        query = select(ConsignmentSale).filter(
            ConsignmentSale.consignment_id == consignment_id
        ).order_by(ConsignmentSale.sale_date.desc())
        
        result = await self.db_session.execute(query)
        sales = result.scalars().all()
        
        return self.response_schema(many=True).dump(sales)
    
    async def get_sales_summary(self, consignment_id: int = None, 
                              start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """Get sales summary"""
        query = select(ConsignmentSale)
        
        if consignment_id:
            query = query.filter(ConsignmentSale.consignment_id == consignment_id)
        
        if start_date:
            query = query.filter(ConsignmentSale.sale_date >= start_date)
        if end_date:
            query = query.filter(ConsignmentSale.sale_date <= end_date)
        
        result = await self.db_session.execute(query)
        sales = result.scalars().all()
        
        total_sales = len(sales)
        if not total_sales:
            return {'summary': {}, 'by_status': {}}

        total_quantity = sum(s.quantity_sold for s in sales)
        total_value = sum(s.total_value for s in sales)
        total_commission = sum(s.commission_amount for s in sales)
        total_net = sum(s.net_amount for s in sales)
        
        by_status = {}
        for sale in sales:
            status = sale.status
            by_status.setdefault(status, {'count': 0, 'total_value': 0})
            by_status[status]['count'] += 1
            by_status[status]['total_value'] += sale.total_value
        
        return {
            'summary': {
                'total_sales': total_sales,
                'total_quantity': total_quantity,
                'total_value': total_value,
                'total_commission': total_commission,
                'total_net': total_net,
                'average_sale_value': total_value / total_sales
            },
            'by_status': by_status
        }
    
    async def _generate_sale_number(self) -> str:
        """Generate unique sale number"""
        today = date.today()
        prefix = f"CSL{today.strftime('%y%m%d')}"
        
        query = select(ConsignmentSale).filter(
            ConsignmentSale.sale_number.like(f"{prefix}%")
        ).order_by(ConsignmentSale.id.desc())
        
        result = await self.db_session.execute(query)
        last_sale = result.scalars().first()
        
        if last_sale:
            last_seq = int(last_sale.sale_number[-4:])
            next_seq = last_seq + 1
        else:
            next_seq = 1
        
        return f"{prefix}{next_seq:04d}"
    
    async def _update_consignment_status(self, consignment_id: int):
        """Update consignment status based on item sales"""
        consignment = await self._get_or_404(Consignment, consignment_id)
        
        items_query = select(ConsignmentItem).filter(
            ConsignmentItem.consignment_id == consignment_id
        )
        items_result = await self.db_session.execute(items_query)
        items = items_result.scalars().all()
        
        if not items:
            return

        total_shipped = sum(item.quantity_shipped for item in items)
        total_sold = sum(item.quantity_sold for item in items)
        
        consignment.total_quantity_sold = total_sold
        
        if total_sold == 0:
            if consignment.status == 'RECEIVED_BY_CUSTOMER':
                pass
        elif total_sold >= total_shipped:
            consignment.status = 'FULLY_SOLD'
        else:
            consignment.status = 'PARTIALLY_SOLD'
        
        self._set_audit_fields(consignment, is_update=True)