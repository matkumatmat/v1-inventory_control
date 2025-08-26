"""
Consignment Statement Service
=============================

Service for Consignment Statement management
"""

from typing import Dict, Any, List
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, func, select
from sqlalchemy.orm import selectinload

from ..base import CRUDService, transactional, audit_log
from ..exceptions import ValidationError, BusinessRuleError, ConsignmentError
from ...models import (
    ConsignmentStatement, ConsignmentAgreement, Consignment, 
    ConsignmentSale, ConsignmentReturn
)
from ...schemas import ConsignmentStatementSchema, ConsignmentStatementCreateSchema, ConsignmentStatementUpdateSchema

class ConsignmentStatementService(CRUDService):
    """Service for Consignment Statement management"""
    
    model_class = ConsignmentStatement
    create_schema = ConsignmentStatementCreateSchema
    update_schema = ConsignmentStatementUpdateSchema
    response_schema = ConsignmentStatementSchema
    search_fields = ['statement_number']

    def __init__(self, db_session: AsyncSession, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)

    @transactional
    @audit_log('CREATE', 'ConsignmentStatement')
    async def generate_statement(self, agreement_id: int, period_start: date, 
                               period_end: date) -> Dict[str, Any]:
        """Generate consignment statement"""
        agreement = await self._get_or_404(ConsignmentAgreement, agreement_id)
        
        if period_start >= period_end:
            raise ValidationError("Period start must be before period end")
        
        query = select(ConsignmentStatement).filter(
            and_(
                ConsignmentStatement.agreement_id == agreement_id,
                ConsignmentStatement.period_start == period_start,
                ConsignmentStatement.period_end == period_end
            )
        )
        result = await self.db_session.execute(query)
        existing_statement = result.scalars().first()
        
        if existing_statement:
            raise BusinessRuleError("Statement already exists for this period")
        
        statement_data = await self._calculate_statement_totals(
            agreement_id, period_start, period_end
        )
        
        statement_data.update({
            'statement_number': await self._generate_statement_number(),
            'agreement_id': agreement_id,
            'customer_id': agreement.customer_id,
            'period_start': period_start,
            'period_end': period_end,
            'generated_by': self.current_user
        })
        
        payment_terms_days = agreement.payment_terms_days or 30
        statement_data['payment_due_date'] = period_end + timedelta(days=payment_terms_days)
        
        statement_result = await super().create(statement_data)
        
        await self._send_notification('CONSIGNMENT_STATEMENT_GENERATED', ['customer', 'finance_team'], {
            'statement_id': statement_result['id'],
            'statement_number': statement_data['statement_number'],
            'agreement_number': agreement.agreement_number,
            'customer_name': agreement.customer.name,
            'net_amount_due': statement_data['net_amount_due']
        })
        
        return statement_result
    
    @transactional
    @audit_log('SEND', 'ConsignmentStatement')
    async def send_statement(self, statement_id: int) -> Dict[str, Any]:
        """Send statement to customer"""
        statement = await self._get_or_404(ConsignmentStatement, statement_id)
        
        if statement.status != 'DRAFT':
            raise ConsignmentError(f"Can only send draft statements. Current status: {statement.status}")
        
        statement.status = 'SENT'
        statement.sent_date = datetime.utcnow()
        self._set_audit_fields(statement, is_update=True)
        
        return self.response_schema().dump(statement)
    
    @transactional
    @audit_log('CONFIRM', 'ConsignmentStatement')
    async def confirm_statement(self, statement_id: int) -> Dict[str, Any]:
        """Confirm statement by customer"""
        statement = await self._get_or_404(ConsignmentStatement, statement_id)
        
        if statement.status != 'SENT':
            raise ConsignmentError(f"Can only confirm sent statements. Current status: {statement.status}")
        
        statement.status = 'CONFIRMED'
        self._set_audit_fields(statement, is_update=True)
        
        return self.response_schema().dump(statement)
    
    @transactional
    @audit_log('PAYMENT', 'ConsignmentStatement')
    async def record_payment(self, statement_id: int, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record payment for statement"""
        statement = await self._get_or_404(ConsignmentStatement, statement_id)
        
        if statement.status != 'CONFIRMED':
            raise ConsignmentError(f"Can only record payment for confirmed statements. Current status: {statement.status}")
        
        payment_amount = payment_data['payment_amount']
        statement.payment_amount = (statement.payment_amount or 0) + payment_amount
        statement.payment_received_date = payment_data.get('payment_date', date.today())
        
        if statement.payment_amount >= statement.net_amount_due:
            statement.payment_status = 'PAID'
            statement.status = 'PAID'
        else:
            statement.payment_status = 'PARTIAL'
        
        self._set_audit_fields(statement, is_update=True)
        
        return self.response_schema().dump(statement)
    
    async def get_statements_by_agreement(self, agreement_id: int) -> List[Dict[str, Any]]:
        """Get all statements for an agreement"""
        query = select(ConsignmentStatement).filter(
            ConsignmentStatement.agreement_id == agreement_id
        ).order_by(ConsignmentStatement.period_end.desc())
        
        result = await self.db_session.execute(query)
        statements = result.scalars().all()
        
        return self.response_schema(many=True).dump(statements)
    
    async def get_overdue_statements(self, days_overdue: int = 0) -> List[Dict[str, Any]]:
        """Get overdue statements"""
        cutoff_date = date.today() - timedelta(days=days_overdue)
        
        query = select(ConsignmentStatement).filter(
            and_(
                ConsignmentStatement.payment_status.in_(['PENDING', 'PARTIAL']),
                ConsignmentStatement.payment_due_date <= cutoff_date
            )
        ).order_by(ConsignmentStatement.payment_due_date.asc())
        
        result = await self.db_session.execute(query)
        statements = result.scalars().all()
        
        response = []
        for statement in statements:
            statement_data = self.response_schema().dump(statement)
            days_overdue_val = (date.today() - statement.payment_due_date).days
            statement_data['days_overdue'] = days_overdue_val
            response.append(statement_data)
        
        return response
    
    async def _calculate_statement_totals(self, agreement_id: int, 
                                        period_start: date, period_end: date) -> Dict[str, Any]:
        """Calculate statement totals for a period"""
        consignments_query = select(Consignment).filter(
            and_(
                Consignment.agreement_id == agreement_id,
                Consignment.consignment_date >= period_start,
                Consignment.consignment_date <= period_end
            )
        )
        consignments_result = await self.db_session.execute(consignments_query)
        consignments = consignments_result.scalars().all()
        
        total_shipped_value = sum(c.total_value or 0 for c in consignments)
        
        consignment_ids = [c.id for c in consignments]
        if not consignment_ids:
            return {
                'total_shipped_value': 0, 'total_sold_value': 0,
                'total_returned_value': 0, 'total_commission': 0,
                'net_amount_due': 0, 'payment_status': 'PENDING'
            }

        sales_query = select(ConsignmentSale).filter(
            and_(
                ConsignmentSale.consignment_id.in_(consignment_ids),
                ConsignmentSale.sale_date >= period_start,
                ConsignmentSale.sale_date <= period_end,
                ConsignmentSale.status.in_(['CONFIRMED', 'PAID'])
            )
        )
        sales_result = await self.db_session.execute(sales_query)
        sales = sales_result.scalars().all()
        
        total_sold_value = sum(sale.total_value for sale in sales)
        total_commission = sum(sale.commission_amount for sale in sales)
        
        returns_query = select(ConsignmentReturn).options(selectinload(ConsignmentReturn.consignment_item)).filter(
            and_(
                ConsignmentReturn.consignment_id.in_(consignment_ids),
                ConsignmentReturn.return_date >= period_start,
                ConsignmentReturn.return_date <= period_end,
                ConsignmentReturn.status == 'PROCESSED'
            )
        )
        returns_result = await self.db_session.execute(returns_query)
        returns = returns_result.scalars().all()
        
        total_returned_value = sum(
            (r.restocked_quantity * (r.consignment_item.unit_value or 0))
            for r in returns if r.consignment_item
        )
        
        net_amount_due = total_sold_value - total_commission
        
        return {
            'total_shipped_value': total_shipped_value,
            'total_sold_value': total_sold_value,
            'total_returned_value': total_returned_value,
            'total_commission': total_commission,
            'net_amount_due': net_amount_due,
            'payment_status': 'PENDING'
        }
    
    async def _generate_statement_number(self) -> str:
        """Generate unique statement number"""
        today = date.today()
        prefix = f"CST{today.strftime('%y%m%d')}"
        
        query = select(ConsignmentStatement).filter(
            ConsignmentStatement.statement_number.like(f"{prefix}%")
        ).order_by(ConsignmentStatement.id.desc())
        
        result = await self.db_session.execute(query)
        last_statement = result.scalars().first()
        
        if last_statement:
            last_seq = int(last_statement.statement_number[-4:])
            next_seq = last_seq + 1
        else:
            next_seq = 1
        
        return f"{prefix}{next_seq:04d}"