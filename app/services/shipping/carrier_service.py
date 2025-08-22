"""
Carrier Service
===============

Service untuk Carrier management
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc


from ..base import CRUDService, transactional, audit_log
from ..exceptions import ValidationError, ConflictError
from ...models import Carrier, CarrierType
from ...schemas import CarrierSchema, CarrierCreateSchema, CarrierUpdateSchema

class CarrierService(CRUDService):
    """Service untuk Carrier management"""
    
    model_class = Carrier
    create_schema = CarrierCreateSchema
    update_schema = CarrierUpdateSchema
    response_schema = CarrierSchema
    search_fields = ['name', 'carrier_code', 'contact_person']
    
    @transactional
    @audit_log('CREATE', 'Carrier')
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create carrier dengan validation"""
        # Validate carrier code uniqueness
        carrier_code = data.get('carrier_code')
        if carrier_code:
            self._validate_unique_field(Carrier, 'carrier_code', carrier_code,
                                      error_message=f"Carrier code '{carrier_code}' already exists")
        
        # Validate carrier type exists
        carrier_type_id = data.get('carrier_type_id')
        if carrier_type_id:
            carrier_type = self.db.query(CarrierType).filter(
                CarrierType.id == carrier_type_id
            ).first()
            if not carrier_type:
                raise ValidationError(f"Carrier type with ID {carrier_type_id} not found")
        
        return super().create(data)
    
    def get_active_carriers(self) -> List[Dict[str, Any]]:
        """Get all active carriers"""
        carriers = self.db.query(Carrier).filter(
            Carrier.is_active == True
        ).order_by(Carrier.name.asc()).all()
        
        return self.response_schema(many=True).dump(carriers)
    
    def get_carriers_by_type(self, carrier_type_id: int) -> List[Dict[str, Any]]:
        """Get carriers by type"""
        carriers = self.db.query(Carrier).filter(
            and_(
                Carrier.carrier_type_id == carrier_type_id,
                Carrier.is_active == True
            )
        ).order_by(Carrier.name.asc()).all()
        
        return self.response_schema(many=True).dump(carriers)

