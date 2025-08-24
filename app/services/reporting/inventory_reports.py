"""
Inventory Report Service
========================

Service untuk Inventory reports dan analytics
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, case

from ..base import BaseService
from ...models import Product, Batch, Allocation, StockMovement, Warehouse, Rack, RackAllocation

class InventoryReportService(BaseService):
    """Service untuk Inventory Reports"""
    
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None):
        super().__init__(db_session, current_user, audit_service)
    
    def generate_stock_summary_report(self, warehouse_id: int = None,
                                    as_of_date: date = None) -> Dict[str, Any]:
        """Generate comprehensive stock summary report"""
        if not as_of_date:
            as_of_date = date.today()
        
        query = self.db_session.query(Product).filter(Product.is_active == True)
        products = query.all()
        
        report_data = []
        total_products = 0
        total_value = 0
        
        for product in products:
            # Calculate stock levels
            stock_data = self._calculate_product_stock(product.id, warehouse_id, as_of_date)
            
            if stock_data['total_stock'] > 0:  # Only include products with stock
                report_data.append({
                    'product_code': product.product_code,
                    'product_name': product.name,
                    'generic_name': product.generic_name,
                    'manufacturer': product.manufacturer,
                    'unit_of_measure': product.unit_of_measure,
                    **stock_data
                })
                
                total_products += 1
                total_value += stock_data.get('total_value', 0)
        
        # Sort by product name
        report_data.sort(key=lambda x: x['product_name'])
        
        return {
            'report_title': 'Stock Summary Report',
            'generated_at': datetime.utcnow().isoformat(),
            'as_of_date': as_of_date.isoformat(),
            'warehouse_id': warehouse_id,
            'summary': {
                'total_products_with_stock': total_products,
                'total_inventory_value': round(total_value, 2)
            },
            'data': report_data
        }
    
    def generate_expiry_report(self, days_ahead: int = 30, 
                             warehouse_id: int = None) -> Dict[str, Any]:
        """Generate expiry report"""
        cutoff_date = date.today() + timedelta(days=days_ahead)
        
        query = self.db_session.query(Batch).filter(
            and_(
                Batch.expiry_date <= cutoff_date,
                Batch.expiry_date >= date.today(),
                Batch.status == 'ACTIVE'
            )
        ).order_by(Batch.expiry_date.asc())
        
        if warehouse_id:
            # Filter by warehouse through allocations
            query = query.join(Allocation).join(RackAllocation).join(Rack).filter(
                Rack.warehouse_id == warehouse_id
            )
        
        batches = query.all()
        
        report_data = []
        total_value_at_risk = 0
        
        for batch in batches:
            available_stock = self._get_available_stock_for_batch(batch.id)
            
            if available_stock > 0:
                days_to_expiry = (batch.expiry_date - date.today()).days
                urgency = 'CRITICAL' if days_to_expiry <= 7 else 'HIGH' if days_to_expiry <= 14 else 'MEDIUM'
                
                batch_value = available_stock * (batch.unit_cost or 0)
                total_value_at_risk += batch_value
                
                report_data.append({
                    'product_code': batch.product.product_code,
                    'product_name': batch.product.name,
                    'batch_number': batch.batch_number,
                    'manufacturing_date': batch.manufacturing_date.isoformat() if batch.manufacturing_date else None,
                    'expiry_date': batch.expiry_date.isoformat(),
                    'days_to_expiry': days_to_expiry,
                    'urgency': urgency,
                    'available_stock': available_stock,
                    'unit_cost': batch.unit_cost or 0,
                    'total_value': round(batch_value, 2)
                })
        
        return {
            'report_title': 'Expiry Report',
            'generated_at': datetime.utcnow().isoformat(),
            'days_ahead': days_ahead,
            'summary': {
                'total_expiring_batches': len(report_data),
                'total_value_at_risk': round(total_value_at_risk, 2),
                'critical_batches': len([b for b in report_data if b['urgency'] == 'CRITICAL'])
            },
            'data': report_data
        }
    
    def generate_movement_report(self, start_date: date, end_date: date,
                               product_id: int = None, warehouse_id: int = None) -> Dict[str, Any]:
        """Generate stock movement report"""
        query = self.db_session.query(StockMovement).filter(
            and_(
                StockMovement.movement_date >= start_date,
                StockMovement.movement_date <= end_date
            )
        ).order_by(StockMovement.movement_date.desc())
        
        if product_id:
            query = query.join(Allocation).join(Batch).filter(
                Batch.product_id == product_id
            )
        
        movements = query.all()
        
        report_data = []
        total_in = 0
        total_out = 0
        
        for movement in movements:
            movement_data = {
                'movement_number': movement.movement_number,
                'movement_date': movement.movement_date.isoformat(),
                'movement_type': movement.movement_type.name,
                'product_code': movement.allocation.batch.product.product_code,
                'product_name': movement.allocation.batch.product.name,
                'batch_number': movement.allocation.batch.batch_number,
                'quantity': movement.quantity,
                'movement_direction': 'IN' if movement.quantity > 0 else 'OUT',
                'reference_type': movement.reference_type,
                'reference_number': movement.reference_number,
                'executed_by': movement.executed_by,
                'notes': movement.notes
            }
            
            report_data.append(movement_data)
            
            if movement.quantity > 0:
                total_in += movement.quantity
            else:
                total_out += abs(movement.quantity)
        
        return {
            'report_title': 'Stock Movement Report',
            'generated_at': datetime.utcnow().isoformat(),
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'summary': {
                'total_movements': len(report_data),
                'total_quantity_in': total_in,
                'total_quantity_out': total_out,
                'net_movement': total_in - total_out
            },
            'data': report_data
        }
    
    def generate_warehouse_utilization_report(self, warehouse_id: int = None) -> Dict[str, Any]:
        """Generate warehouse utilization report"""
        query = self.db_session.query(Warehouse).filter(Warehouse.is_active == True)
        
        if warehouse_id:
            query = query.filter(Warehouse.id == warehouse_id)
        
        warehouses = query.all()
        
        report_data = []
        
        for warehouse in warehouses:
            # Get racks in this warehouse
            racks = self.db_session.query(Rack).filter(
                and_(Rack.warehouse_id == warehouse.id, Rack.is_active == True)
            ).all()
            
            total_capacity = sum(rack.max_capacity or 0 for rack in racks)
            total_usage = sum(rack.current_quantity or 0 for rack in racks)
            utilization_pct = (total_usage / total_capacity * 100) if total_capacity > 0 else 0
            
            # Rack utilization breakdown
            rack_breakdown = []
            for rack in racks:
                rack_capacity = rack.max_capacity or 0
                rack_usage = rack.current_quantity or 0
                rack_util_pct = (rack_usage / rack_capacity * 100) if rack_capacity > 0 else 0
                
                rack_breakdown.append({
                    'rack_code': rack.rack_code,
                    'zone': rack.zone,
                    'capacity': rack_capacity,
                    'current_usage': rack_usage,
                    'available': rack_capacity - rack_usage,
                    'utilization_percentage': round(rack_util_pct, 2)
                })
            
            report_data.append({
                'warehouse_code': warehouse.warehouse_code,
                'warehouse_name': warehouse.name,
                'total_racks': len(racks),
                'total_capacity': total_capacity,
                'total_usage': total_usage,
                'available_capacity': total_capacity - total_usage,
                'utilization_percentage': round(utilization_pct, 2),
                'racks': rack_breakdown
            })
        
        return {
            'report_title': 'Warehouse Utilization Report',
            'generated_at': datetime.utcnow().isoformat(),
            'data': report_data
        }
    
    def _calculate_product_stock(self, product_id: int, warehouse_id: int = None,
                               as_of_date: date = None) -> Dict[str, Any]:
        """Calculate stock levels for a product"""
        # Get all batches for product
        batches_query = self.db_session.query(Batch).filter(
            and_(Batch.product_id == product_id, Batch.status == 'ACTIVE')
        )
        
        if as_of_date:
            batches_query = batches_query.filter(Batch.received_date <= as_of_date)
        
        batches = batches_query.all()
        
        total_received = sum(batch.received_quantity for batch in batches)
        total_allocated = 0
        total_shipped = 0
        total_value = 0
        
        # Calculate allocations
        for batch in batches:
            allocations = self.db_session.query(Allocation).filter(
                and_(Allocation.batch_id == batch.id, Allocation.status == 'active')
            )
            
            if as_of_date:
                allocations = allocations.filter(Allocation.allocation_date <= as_of_date)
            
            for allocation in allocations.all():
                total_allocated += allocation.allocated_quantity
                total_shipped += allocation.shipped_quantity
                total_value += allocation.allocated_quantity * (allocation.unit_value or 0)
        
        available_stock = total_allocated - total_shipped
        
        return {
            'total_received': total_received,
            'total_allocated': total_allocated,
            'total_shipped': total_shipped,
            'available_stock': available_stock,
            'unallocated_stock': total_received - total_allocated,
            'total_value': round(total_value, 2)
        }
    
    def _get_available_stock_for_batch(self, batch_id: int) -> int:
        """Get available stock for specific batch"""
        batch = self.db_session.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            return 0
        
        total_allocated = self.db_session.query(
            func.sum(Allocation.allocated_quantity - Allocation.shipped_quantity)
        ).filter(
            and_(Allocation.batch_id == batch_id, Allocation.status == 'active')
        ).scalar() or 0
        
        return batch.received_quantity - total_allocated