"""
Consignment Statement Service
=============================

Service untuk Consignment Statement management
"""

from typing import Dict, Any, List
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ..base import CRUDService, transactional, audit_log
from ..exceptions import ValidationError, BusinessRuleError, ConsignmentError
from ...models import (
    ConsignmentStatement, ConsignmentAgreement, Consignment, 
    ConsignmentSale, ConsignmentReturn
)
from ...schemas import ConsignmentStatementSchema, ConsignmentStatementCreateSchema, ConsignmentStatementUpdateSchema

class ConsignmentStatementService(CRUDService):
    """Service untuk Consignment Statement management"""
    
    model_class = ConsignmentStatement
    create_schema = ConsignmentStatementCreateSchema
    update_schema = ConsignmentStatementUpdateSchema
    response_schema = ConsignmentStatementSchema
    search_fields = ['statement_number']
    
    @transactional
    @audit_log('CREATE', 'ConsignmentStatement')
    def generate_statement(self, agreement_id: int, period_start: date, 
                          period_end: date) -> Dict[str, Any]:
        """Generate consignment statement"""
        # Validate agreement
        agreement = self._get_or_404(ConsignmentAgreement, agreement_id)
        
        # Validate period
        if period_start >= period_end:
            raise ValidationError("Period start must be before period end")
        
        # Check if statement already exists for period
        existing_statement = self.db_session.query(ConsignmentStatement).filter(
            and_(
                ConsignmentStatement.agreement_id == agreement_id,
                ConsignmentStatement.period_start == period_start,
                ConsignmentStatement.period_end == period_end
            )
        ).first()
        
        if existing_statement:
            raise BusinessRuleError("Statement already exists for this period")
        
        # Calculate statement totals
        statement_data = self._calculate_statement_totals(
            agreement_id, period_start, period_end
        )
        
        # Generate statement number
        statement_data.update({
            'statement_number': self._generate_statement_number(),
            'agreement_id': agreement_id,
            'customer_id': agreement.customer_id,
            'period_start': period_start,
            'period_end': period_end,
            'generated_by': self.current_user
        })
        
        # Calculate payment due date
        payment_terms_days = agreement.payment_terms_days or 30
        statement_data['payment_due_date'] = period_end + timedelta(days=payment_terms_days)
        
        # Create statement
        statement_result = super().create(statement_data)
        
        # Send notification
        self._send_notification('CONSIGNMENT_STATEMENT_GENERATED', ['customer', 'finance_team'], {
            'statement_id': statement_result['id'],
            'statement_number': statement_data['statement_number'],
            'agreement_number': agreement.agreement_number,
            'customer_name': agreement.customer.name,
            'net_amount_due': statement_data['net_amount_due']
        })
        
        return statement_result
    
    @transactional
    @audit_log('SEND', 'ConsignmentStatement')
    def send_statement(self, statement_id: int) -> Dict[str, Any]:
        """Send statement to customer"""
        statement = self._get_or_404(ConsignmentStatement, statement_id)
        
        if statement.status != 'DRAFT':
            raise ConsignmentError(f"Can only send draft statements. Current status: {statement.status}")
        
        # Send statement
        statement.status = 'SENT'
        statement.sent_date = datetime.utcnow()
        self._set_audit_fields(statement, is_update=True)
        
        return self.response_schema().dump(statement)
    
    @transactional
    @audit_log('CONFIRM', 'ConsignmentStatement')
    def confirm_statement(self, statement_id: int) -> Dict[str, Any]:
        """Confirm statement by customer"""
        statement = self._get_or_404(ConsignmentStatement, statement_id)
        
        if statement.status != 'SENT':
            raise ConsignmentError(f"Can only confirm sent statements. Current status: {statement.status}")
        
        # Confirm statement
        statement.status = 'CONFIRMED'
        self._set_audit_fields(statement, is_update=True)
        
        return self.response_schema().dump(statement)
    
    @transactional
    @audit_log('PAYMENT', 'ConsignmentStatement')
    def record_payment(self, statement_id: int, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record payment for statement"""
        statement = self._get_or_404(ConsignmentStatement, statement_id)
        
        if statement.status != 'CONFIRMED':
            raise ConsignmentError(f"Can only record payment for confirmed statements. Current status: {statement.status}")
        
        # Record payment
        payment_amount = payment_data['payment_amount']
        statement.payment_amount = (statement.payment_amount or 0) + payment_amount
        statement.payment_received_date = payment_data.get('payment_date', date.today())
        
        # Update payment status
        if statement.payment_amount >= statement.net_amount_due:
            statement.payment_status = 'PAID'
            statement.status = 'PAID'
        else:
            statement.payment_status = 'PARTIAL'
        
        self._set_audit_fields(statement, is_update=True)
        
        return self.response_schema().dump(statement)
    
    def get_statements_by_agreement(self, agreement_id: int) -> List[Dict[str, Any]]:
        """Get all statements untuk agreement"""
        statements = self.db_session.query(ConsignmentStatement).filter(
            ConsignmentStatement.agreement_id == agreement_id
        ).order_by(ConsignmentStatement.period_end.desc()).all()
        
        return self.response_schema(many=True).dump(statements)
    
    def get_overdue_statements(self, days_overdue: int = 0) -> List[Dict[str, Any]]:
        """Get overdue statements"""
        cutoff_date = date.today() - timedelta(days=days_overdue)
        
        statements = self.db_session.query(ConsignmentStatement).filter(
            and_(
                ConsignmentStatement.payment_status.in_(['PENDING', 'PARTIAL']),
                ConsignmentStatement.payment_due_date <= cutoff_date
            )
        ).order_by(ConsignmentStatement.payment_due_date.asc()).all()
        
        result = []
        for statement in statements:
            statement_data = self.response_schema().dump(statement)
            days_overdue = (date.today() - statement.payment_due_date).days
            statement_data['days_overdue'] = days_overdue
            result.append(statement_data)
        
        return result
    
    def _calculate_statement_totals(self, agreement_id: int, 
                                  period_start: date, period_end: date) -> Dict[str, Any]:
        """Calculate statement totals untuk period"""
        # Get all consignments dalam period
        consignments = self.db_session.query(Consignment).filter(
            and_(
                Consignment.agreement_id == agreement_id,
                Consignment.consignment_date >= period_start,
                Consignment.consignment_date <= period_end
            )
        ).all()
        
        # Calculate totals
        total_shipped_value = sum(c.total_value or 0 for c in consignments)
        
        # Get sales dalam period
        consignment_ids = [c.id for c in consignments]
        sales = self.db_session.query(ConsignmentSale).filter(
            and_(
                ConsignmentSale.consignment_id.in_(consignment_ids),
                ConsignmentSale.sale_date >= period_start,
                ConsignmentSale.sale_date <= period_end,
                ConsignmentSale.status.in_(['CONFIRMED', 'PAID'])
            )
        ).all()
        
        total_sold_value = sum(sale.total_value for sale in sales)
        total_commission = sum(sale.commission_amount for sale in sales)
        
        # Get returns dalam period
        returns = self.db_session.query(ConsignmentReturn).filter(
            and_(
                ConsignmentReturn.consignment_id.in_(consignment_ids),
                ConsignmentReturn.return_date >= period_start,
                ConsignmentReturn.return_date <= period_end,
                ConsignmentReturn.status == 'PROCESSED'
            )
        ).all()
        
        total_returned_value = sum(
            (return_rec.restocked_quantity * (return_rec.consignment_item.unit_value or 0))
            for return_rec in returns
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
    
    def _generate_statement_number(self) -> str:
        """Generate unique statement number"""
        today = date.today()
        prefix = f"CST{today.strftime('%y%m%d')}"
        
        last_statement = self.db_session.query(ConsignmentStatement).filter(
            ConsignmentStatement.statement_number.like(f"{prefix}%")
        ).order_by(ConsignmentStatement.id.desc()).first()
        
        if last_statement:
            last_seq = int(last_statement.statement_number[-4:])
            next_seq = last_seq + 1
        else:
            next_seq = 1
        
        return f"{prefix}{next_seq:04d}"