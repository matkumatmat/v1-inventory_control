### **services/shipping/tracking_service.py**

"""
Shipment Tracking Service
=========================

Service untuk Shipment Tracking management
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ..base import CRUDService, transactional, audit_log
from ..exceptions import ValidationError, NotFoundError
from ...models import ShipmentTracking, Shipment
from ...schemas import ShipmentTrackingSchema, ShipmentTrackingCreateSchema

class ShipmentTrackingService(CRUDService):
    """Service untuk Shipment Tracking management"""
    
    model_class = ShipmentTracking
    create_schema = ShipmentTrackingCreateSchema
    response_schema = ShipmentTrackingSchema
    
    @transactional
    @audit_log('CREATE', 'ShipmentTracking')
    def create_tracking_record(self, shipment_id: int, status: str, 
                              description: str = None, location: str = None,
                              tracking_number: str = None, source: str = 'MANUAL',
                              latitude: float = None, longitude: float = None) -> Dict[str, Any]:
        """Create tracking record"""
        # Validate shipment exists
        shipment = self._get_or_404(Shipment, shipment_id)
        
        # Create tracking data
        tracking_data = {
            'shipment_id': shipment_id,
            'tracking_date': datetime.utcnow(),
            'status': status,
            'location': location,
            'description': description,
            'source': source,
            'tracking_number': tracking_number,
            'latitude': latitude,
            'longitude': longitude,
            'created_by': self.current_user
        }
        
        return super().create(tracking_data)
    
    def get_shipment_tracking_history(self, shipment_id: int) -> List[Dict[str, Any]]:
        """Get tracking history untuk shipment"""
        tracking_records = self.db.query(ShipmentTracking).filter(
            ShipmentTracking.shipment_id == shipment_id
        ).order_by(ShipmentTracking.tracking_date.desc()).all()
        
        return self.response_schema(many=True).dump(tracking_records)
    
    def get_latest_tracking_status(self, shipment_id: int) -> Optional[Dict[str, Any]]:
        """Get latest tracking status"""
        latest_tracking = self.db.query(ShipmentTracking).filter(
            ShipmentTracking.shipment_id == shipment_id
        ).order_by(ShipmentTracking.tracking_date.desc()).first()
        
        if latest_tracking:
            return self.response_schema().dump(latest_tracking)
        return None
    
    def track_by_tracking_number(self, tracking_number: str) -> List[Dict[str, Any]]:
        """Track shipment by tracking number"""
        # Find shipment by tracking number
        shipment = self.db.query(Shipment).filter(
            Shipment.tracking_number == tracking_number
        ).first()
        
        if not shipment:
            raise NotFoundError('Shipment', f'tracking: {tracking_number}')
        
        return self.get_shipment_tracking_history(shipment.id)