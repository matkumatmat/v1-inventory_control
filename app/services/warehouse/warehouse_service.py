"""
Warehouse Service
=================

Service untuk Warehouse management
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from ..base import CRUDService, transactional, audit_log
from ..exceptions import ValidationError, ConflictError, NotFoundError
from ...models import Warehouse, Rack
from ...schemas import WarehouseSchema, WarehouseCreateSchema, WarehouseUpdateSchema

class WarehouseService(CRUDService):
    """Service untuk Warehouse management"""
    
    model_class = Warehouse
    create_schema = WarehouseCreateSchema
    update_schema = WarehouseUpdateSchema
    response_schema = WarehouseSchema
    search_fields = ['name', 'warehouse_code', 'address_line1', 'city']
    
    @transactional
    @audit_log('CREATE', 'Warehouse')
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create warehouse dengan validation"""
        # Validate warehouse code uniqueness
        warehouse_code = data.get('warehouse_code')
        if warehouse_code:
            self._validate_unique_field(Warehouse, 'warehouse_code', warehouse_code,
                                      error_message=f"Warehouse code '{warehouse_code}' already exists")
        
        return super().create(data)
    
    @transactional
    @audit_log('UPDATE', 'Warehouse')
    def update(self, entity_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update warehouse dengan validation"""
        # Validate warehouse code uniqueness if changed
        warehouse_code = data.get('warehouse_code')
        if warehouse_code:
            self._validate_unique_field(Warehouse, 'warehouse_code', warehouse_code,
                                      exclude_id=entity_id,
                                      error_message=f"Warehouse code '{warehouse_code}' already exists")
        
        return super().update(entity_id, data)
    
    def get_by_code(self, warehouse_code: str) -> Dict[str, Any]:
        """Get warehouse by code"""
        warehouse = self.db_session.query(Warehouse).filter(
            Warehouse.warehouse_code == warehouse_code
        ).first()
        
        if not warehouse:
            raise NotFoundError('Warehouse', warehouse_code)
        
        return self.response_schema().dump(warehouse)
    
    def get_warehouse_summary(self, warehouse_id: int) -> Dict[str, Any]:
        """Get warehouse summary dengan rack dan capacity info"""
        warehouse = self._get_or_404(Warehouse, warehouse_id)
        
        # Get racks summary
        racks_query = self.db_session.query(Rack).filter(
            Rack.warehouse_id == warehouse_id
        )
        
        total_racks = racks_query.count()
        active_racks = racks_query.filter(Rack.is_active == True).count()
        
        # Calculate capacity utilization
        total_capacity = sum(rack.max_capacity or 0 for rack in racks_query.all())
        current_usage = sum(rack.current_quantity or 0 for rack in racks_query.all())
        
        utilization_percentage = (current_usage / total_capacity * 100) if total_capacity > 0 else 0
        
        return {
            'warehouse': self.response_schema().dump(warehouse),
            'summary': {
                'total_racks': total_racks,
                'active_racks': active_racks,
                'total_capacity': total_capacity,
                'current_usage': current_usage,
                'available_capacity': total_capacity - current_usage,
                'utilization_percentage': round(utilization_percentage, 2)
            }
        }
    
    def get_active_warehouses(self) -> List[Dict[str, Any]]:
        """Get all active warehouses"""
        query = self.db_session.query(Warehouse).filter(
            Warehouse.is_active == True
        ).order_by(Warehouse.name.asc())
        
        warehouses = query.all()
        return self.response_schema(many=True).dump(warehouses)