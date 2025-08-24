"""
Shipment Service
================

CRITICAL SERVICE untuk Shipment management dan logistics
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ..base import CRUDService, transactional, audit_log
from ..exceptions import ValidationError, BusinessRuleError, ShipmentError, NotFoundError
from ...models import (
    Shipment, PackingSlip, PackingOrder, Customer, Carrier, 
    DeliveryMethod, ShipmentDocument, ShipmentTracking
)
from ...schemas import (
    ShipmentSchema, ShipmentCreateSchema, ShipmentUpdateSchema,
    ShipmentDocumentSchema, ShipmentTrackingSchema
)

class ShipmentService(CRUDService):
    """CRITICAL SERVICE untuk Shipment management"""
    
    model_class = Shipment
    create_schema = ShipmentCreateSchema
    update_schema = ShipmentUpdateSchema
    response_schema = ShipmentSchema
    search_fields = ['shipment_number', 'tracking_number', 'delivery_address']
    
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None, 
                 tracking_service=None, document_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)
        self.tracking_service = tracking_service
        self.document_service = document_service
    
    @transactional
    @audit_log('CREATE', 'Shipment')
    def create_from_packing_slip(self, packing_slip_id: int, 
                                carrier_id: int, delivery_method_id: int,
                                additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create shipment dari packing slip"""
        packing_slip = self._get_or_404(PackingSlip, packing_slip_id)
        
        if packing_slip.status != 'FINALIZED':
            raise BusinessRuleError(f"Packing slip must be finalized. Current status: {packing_slip.status}")
        
        # Validate carrier dan delivery method
        carrier = self._get_or_404(Carrier, carrier_id)
        delivery_method = self._get_or_404(DeliveryMethod, delivery_method_id)
        
        if not carrier.is_active:
            raise ValidationError(f"Carrier {carrier.name} is not active")
        
        # Generate shipment number
        shipment_number = self._generate_shipment_number()
        
        # Create shipment data
        shipment_data = {
            'shipment_number': shipment_number,
            'packing_slip_id': packing_slip_id,
            'customer_id': packing_slip.customer_id,
            'carrier_id': carrier_id,
            'delivery_method_id': delivery_method_id,
            'shipment_date': date.today(),
            'delivery_address': packing_slip.delivery_address,
            'contact_person': packing_slip.contact_person,
            'contact_phone': packing_slip.contact_phone,
            'status': 'PENDING',
            'priority_level': packing_slip.priority_level or 'NORMAL'
        }
        
        # Merge additional data
        if additional_data:
            shipment_data.update(additional_data)
        
        # Create shipment
        shipment_data_result = super().create(shipment_data)
        
        # Update packing slip status
        packing_slip.status = 'SHIPPED'
        self._set_audit_fields(packing_slip, is_update=True)
        
        # Create initial tracking record
        if self.tracking_service:
            self.tracking_service.create_tracking_record(
                shipment_id=shipment_data_result['id'],
                status='SHIPMENT_CREATED',
                description='Shipment created and ready for pickup'
            )
        
        # Send notification
        self._send_notification('SHIPMENT_CREATED', ['logistics_team', 'customer'], {
            'shipment_id': shipment_data_result['id'],
            'shipment_number': shipment_number,
            'customer_name': packing_slip.customer.name,
            'carrier_name': carrier.name,
            'delivery_address': packing_slip.delivery_address
        })
        
        return shipment_data_result
    
    @transactional
    @audit_log('DISPATCH', 'Shipment')
    def dispatch_shipment(self, shipment_id: int, tracking_number: str = None,
                         estimated_delivery_date: date = None,
                         driver_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Dispatch shipment"""
        shipment = self._get_or_404(Shipment, shipment_id)
        
        if shipment.status != 'PENDING':
            raise ShipmentError(f"Can only dispatch pending shipments. Current status: {shipment.status}")
        
        # Update shipment
        shipment.status = 'DISPATCHED'
        shipment.shipped_by = self.current_user
        shipment.shipped_date = datetime.utcnow()
        
        if tracking_number:
            shipment.tracking_number = tracking_number
        
        if estimated_delivery_date:
            shipment.estimated_delivery_date = estimated_delivery_date
        
        if driver_info:
            shipment.driver_name = driver_info.get('driver_name')
            shipment.driver_phone = driver_info.get('driver_phone')
            shipment.vehicle_number = driver_info.get('vehicle_number')
        
        self._set_audit_fields(shipment, is_update=True)
        
        # Create tracking record
        if self.tracking_service:
            self.tracking_service.create_tracking_record(
                shipment_id=shipment_id,
                status='DISPATCHED',
                description=f'Shipment dispatched via {shipment.carrier.name}',
                tracking_number=tracking_number
            )
        
        # Send notifications
        self._send_notification('SHIPMENT_DISPATCHED', ['customer', 'logistics_team'], {
            'shipment_id': shipment_id,
            'shipment_number': shipment.shipment_number,
            'tracking_number': tracking_number,
            'estimated_delivery': estimated_delivery_date.isoformat() if estimated_delivery_date else None
        })
        
        return self.response_schema().dump(shipment)
    
    @transactional
    @audit_log('DELIVER', 'Shipment')
    def confirm_delivery(self, shipment_id: int, 
                        delivery_confirmation: Dict[str, Any]) -> Dict[str, Any]:
        """Confirm shipment delivery"""
        shipment = self._get_or_404(Shipment, shipment_id)
        
        if shipment.status not in ['DISPATCHED', 'IN_TRANSIT']:
            raise ShipmentError(f"Can only confirm delivery for dispatched shipments. Current status: {shipment.status}")
        
        # Update shipment
        shipment.status = 'DELIVERED'
        shipment.delivered_date = datetime.utcnow()
        shipment.delivered_confirmed_by = delivery_confirmation.get('confirmed_by')
        shipment.delivered_confirmed_date = datetime.utcnow()
        
        # Update final delivery details
        shipment.final_delivery_address = delivery_confirmation.get('delivery_address', shipment.delivery_address)
        shipment.final_contact_person = delivery_confirmation.get('contact_person')
        shipment.final_contact_phone = delivery_confirmation.get('contact_phone')
        
        # Calculate days in transit
        if shipment.shipped_date:
            days_in_transit = (shipment.delivered_date.date() - shipment.shipped_date.date()).days
            shipment.days_in_transit = days_in_transit
        
        self._set_audit_fields(shipment, is_update=True)
        
        # Create tracking record
        if self.tracking_service:
            self.tracking_service.create_tracking_record(
                shipment_id=shipment_id,
                status='DELIVERED',
                description=f'Package delivered to {delivery_confirmation.get("confirmed_by", "recipient")}',
                location=delivery_confirmation.get('delivery_location')
            )
        
        # Send notifications
        self._send_notification('SHIPMENT_DELIVERED', ['customer', 'sales_team'], {
            'shipment_id': shipment_id,
            'shipment_number': shipment.shipment_number,
            'delivered_to': delivery_confirmation.get('confirmed_by'),
            'delivery_date': shipment.delivered_date.isoformat()
        })
        
        return self.response_schema().dump(shipment)
    
    @transactional
    @audit_log('CANCEL', 'Shipment')
    def cancel_shipment(self, shipment_id: int, reason: str) -> Dict[str, Any]:
        """Cancel shipment"""
        shipment = self._get_or_404(Shipment, shipment_id)
        
        if shipment.status in ['DELIVERED', 'CANCELLED']:
            raise ShipmentError(f"Cannot cancel shipment with status {shipment.status}")
        
        # Cancel shipment
        shipment.status = 'CANCELLED'
        shipment.cancelled_by = self.current_user
        shipment.cancelled_date = datetime.utcnow()
        shipment.cancellation_reason = reason
        
        self._set_audit_fields(shipment, is_update=True)
        
        # Create tracking record
        if self.tracking_service:
            self.tracking_service.create_tracking_record(
                shipment_id=shipment_id,
                status='CANCELLED',
                description=f'Shipment cancelled: {reason}'
            )
        
        # Revert packing slip status
        if shipment.packing_slip:
            shipment.packing_slip.status = 'FINALIZED'
            self._set_audit_fields(shipment.packing_slip, is_update=True)
        
        # Send notification
        self._send_notification('SHIPMENT_CANCELLED', ['logistics_team', 'customer'], {
            'shipment_id': shipment_id,
            'shipment_number': shipment.shipment_number,
            'reason': reason
        })
        
        return self.response_schema().dump(shipment)
    
    def get_by_shipment_number(self, shipment_number: str) -> Dict[str, Any]:
        """Get shipment by shipment number"""
        shipment = self.db_session.query(Shipment).filter(
            Shipment.shipment_number == shipment_number
        ).first()
        
        if not shipment:
            raise NotFoundError('Shipment', shipment_number)
        
        return self.response_schema().dump(shipment)
    
    def get_by_tracking_number(self, tracking_number: str) -> Dict[str, Any]:
        """Get shipment by tracking number"""
        shipment = self.db_session.query(Shipment).filter(
            Shipment.tracking_number == tracking_number
        ).first()
        
        if not shipment:
            raise NotFoundError('Shipment', f'tracking: {tracking_number}')
        
        return self.response_schema().dump(shipment)
    
    def get_pending_shipments(self, carrier_id: int = None) -> List[Dict[str, Any]]:
        """Get pending shipments"""
        query = self.db_session.query(Shipment).filter(
            Shipment.status == 'PENDING'
        )
        
        if carrier_id:
            query = query.filter(Shipment.carrier_id == carrier_id)
        
        query = query.order_by(Shipment.priority_level.desc(), Shipment.shipment_date.asc())
        
        shipments = query.all()
        return self.response_schema(many=True).dump(shipments)
    
    def get_overdue_shipments(self, days_overdue: int = 1) -> List[Dict[str, Any]]:
        """Get overdue shipments"""
        cutoff_date = date.today() - timedelta(days=days_overdue)
        
        query = self.db_session.query(Shipment).filter(
            and_(
                Shipment.status.in_(['DISPATCHED', 'IN_TRANSIT']),
                Shipment.estimated_delivery_date <= cutoff_date
            )
        ).order_by(Shipment.estimated_delivery_date.asc())
        
        shipments = query.all()
        
        result = []
        for shipment in shipments:
            shipment_data = self.response_schema().dump(shipment)
            if shipment.estimated_delivery_date:
                days_overdue = (date.today() - shipment.estimated_delivery_date).days
                shipment_data['days_overdue'] = days_overdue
            result.append(shipment_data)
        
        return result
    
    def get_shipment_performance_report(self, start_date: date = None, 
                                      end_date: date = None) -> Dict[str, Any]:
        """Get shipment performance report"""
        query = self.db_session.query(Shipment)
        
        if start_date:
            query = query.filter(Shipment.shipment_date >= start_date)
        if end_date:
            query = query.filter(Shipment.shipment_date <= end_date)
        
        shipments = query.all()
        
        # Calculate metrics
        total_shipments = len(shipments)
        delivered_shipments = len([s for s in shipments if s.status == 'DELIVERED'])
        cancelled_shipments = len([s for s in shipments if s.status == 'CANCELLED'])
        
        # Delivery performance
        on_time_deliveries = 0
        total_transit_days = 0
        delivered_count = 0
        
        for shipment in shipments:
            if shipment.status == 'DELIVERED':
                delivered_count += 1
                
                if shipment.days_in_transit:
                    total_transit_days += shipment.days_in_transit
                
                # Check if delivered on time
                if shipment.estimated_delivery_date and shipment.delivered_date:
                    if shipment.delivered_date.date() <= shipment.estimated_delivery_date:
                        on_time_deliveries += 1
        
        # Calculate averages
        avg_transit_days = total_transit_days / delivered_count if delivered_count > 0 else 0
        on_time_percentage = on_time_deliveries / delivered_count * 100 if delivered_count > 0 else 0
        delivery_rate = delivered_shipments / total_shipments * 100 if total_shipments > 0 else 0
        
        # Group by carrier
        by_carrier = {}
        for shipment in shipments:
            carrier_name = shipment.carrier.name
            if carrier_name not in by_carrier:
                by_carrier[carrier_name] = {
                    'total': 0, 'delivered': 0, 'cancelled': 0, 'in_progress': 0
                }
            
            by_carrier[carrier_name]['total'] += 1
            if shipment.status == 'DELIVERED':
                by_carrier[carrier_name]['delivered'] += 1
            elif shipment.status == 'CANCELLED':
                by_carrier[carrier_name]['cancelled'] += 1
            else:
                by_carrier[carrier_name]['in_progress'] += 1
        
        return {
            'summary': {
                'total_shipments': total_shipments,
                'delivered_shipments': delivered_shipments,
                'cancelled_shipments': cancelled_shipments,
                'delivery_rate_percentage': round(delivery_rate, 2),
                'on_time_delivery_percentage': round(on_time_percentage, 2),
                'average_transit_days': round(avg_transit_days, 1)
            },
            'by_carrier': by_carrier
        }
    
    def _generate_shipment_number(self) -> str:
        """Generate unique shipment number"""
        today = date.today()
        prefix = f"SH{today.strftime('%y%m%d')}"
        
        last_shipment = self.db_session.query(Shipment).filter(
            Shipment.shipment_number.like(f"{prefix}%")
        ).order_by(Shipment.id.desc()).first()
        
        if last_shipment:
            last_seq = int(last_shipment.shipment_number[-4:])
            next_seq = last_seq + 1
        else:
            next_seq = 1
        
        return f"{prefix}{next_seq:04d}"