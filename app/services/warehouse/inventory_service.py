"""
Inventory Service
=================

Service untuk inventory management dan stock summaries
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from ..base import BaseService, transactional
from ..exceptions import NotFoundError
from ...models import Product, Batch, Allocation, RackAllocation, Rack, Warehouse

class InventoryService(BaseService):
    """Service untuk Inventory management dan reporting"""
    
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)
    
    def get_stock_summary_by_product(self, product_id: int) -> Dict[str, Any]:
        """Get comprehensive stock summary untuk product"""
        product = self._get_or_404(Product, product_id)
        
        # Get all batches
        batches = self.db_session.query(Batch).filter(
            and_(Batch.product_id == product_id, Batch.status == 'ACTIVE')
        ).all()
        
        # Calculate totals
        total_received = sum(batch.received_quantity for batch in batches)
        
        # Get allocation summary
        allocations_query = self.db_session.query(Allocation).join(Batch).filter(
            and_(Batch.product_id == product_id, Allocation.status == 'active')
        )
        
        allocations = allocations_query.all()
        total_allocated = sum(alloc.allocated_quantity for alloc in allocations)
        total_shipped = sum(alloc.shipped_quantity for alloc in allocations)
        total_reserved = sum(alloc.reserved_quantity for alloc in allocations)
        
        # Calculate availability
        total_available = total_allocated - total_shipped
        total_unreserved = total_available - total_reserved
        
        # Group by allocation type
        allocation_by_type = {}
        for allocation in allocations:
            type_code = allocation.allocation_type.code
            if type_code not in allocation_by_type:
                allocation_by_type[type_code] = {
                    'allocated': 0, 'shipped': 0, 'available': 0, 'reserved': 0
                }
            
            allocation_by_type[type_code]['allocated'] += allocation.allocated_quantity
            allocation_by_type[type_code]['shipped'] += allocation.shipped_quantity
            allocation_by_type[type_code]['available'] += (allocation.allocated_quantity - allocation.shipped_quantity)
            allocation_by_type[type_code]['reserved'] += allocation.reserved_quantity
        
        # Get expiring batches
        expiring_soon = self._get_expiring_batches_for_product(product_id, days_ahead=30)
        
        return {
            'product_id': product_id,
            'product_name': product.name,
            'product_code': product.product_code,
            'stock_summary': {
                'total_received': total_received,
                'total_allocated': total_allocated,
                'total_shipped': total_shipped,
                'total_available': total_available,
                'total_reserved': total_reserved,
                'total_unreserved': total_unreserved,
                'unallocated_stock': total_received - total_allocated
            },
            'by_allocation_type': allocation_by_type,
            'batch_summary': {
                'total_batches': len(batches),
                'active_batches': len([b for b in batches if b.qc_status == 'PASSED']),
                'expiring_soon': len(expiring_soon)
            },
            'expiring_batches': expiring_soon
        }
    
    def get_warehouse_inventory(self, warehouse_id: int) -> Dict[str, Any]:
        """Get inventory summary untuk warehouse"""
        warehouse = self._get_or_404(Warehouse, warehouse_id)
        
        # Get all rack allocations in this warehouse
        rack_allocations_query = self.db_session.query(RackAllocation).join(Rack).filter(
            Rack.warehouse_id == warehouse_id
        )
        
        rack_allocations = rack_allocations_query.all()
        
        # Group by product
        product_summary = {}
        for rack_alloc in rack_allocations:
            allocation = rack_alloc.allocation
            batch = allocation.batch
            product = batch.product
            
            if product.id not in product_summary:
                product_summary[product.id] = {
                    'product': {
                        'id': product.id,
                        'name': product.name,
                        'code': product.product_code
                    },
                    'total_quantity': 0,
                    'available_quantity': 0,
                    'reserved_quantity': 0,
                    'batch_count': set(),
                    'rack_count': set()
                }
            
            product_summary[product.id]['total_quantity'] += rack_alloc.quantity
            product_summary[product.id]['available_quantity'] += (allocation.allocated_quantity - allocation.shipped_quantity)
            product_summary[product.id]['reserved_quantity'] += allocation.reserved_quantity
            product_summary[product.id]['batch_count'].add(batch.id)
            product_summary[product.id]['rack_count'].add(rack_alloc.rack_id)
        
        # Convert sets to counts
        for product_id in product_summary:
            product_summary[product_id]['batch_count'] = len(product_summary[product_id]['batch_count'])
            product_summary[product_id]['rack_count'] = len(product_summary[product_id]['rack_count'])
        
        return {
            'warehouse': {
                'id': warehouse.id,
                'name': warehouse.name,
                'code': warehouse.warehouse_code
            },
            'summary': {
                'unique_products': len(product_summary),
                'total_rack_allocations': len(rack_allocations),
                'total_quantity': sum(p['total_quantity'] for p in product_summary.values())
            },
            'products': list(product_summary.values())
        }
    
    def get_stock_aging_report(self, warehouse_id: int = None) -> Dict[str, Any]:
        """Get stock aging report berdasarkan received date"""
        query = self.db_session.query(Batch).filter(
            and_(Batch.status == 'ACTIVE', Batch.qc_status == 'PASSED')
        )
        
        if warehouse_id:
            # Filter by warehouse through rack allocations
            query = query.join(Allocation).join(RackAllocation).join(Rack).filter(
                Rack.warehouse_id == warehouse_id
            )
        
        batches = query.all()
        
        today = date.today()
        aging_categories = {
            '0-30_days': [],
            '31-60_days': [],
            '61-90_days': [],
            '91-180_days': [],
            '180+_days': []
        }
        
        for batch in batches:
            days_old = (today - batch.received_date).days
            
            if days_old <= 30:
                category = '0-30_days'
            elif days_old <= 60:
                category = '31-60_days'
            elif days_old <= 90:
                category = '61-90_days'
            elif days_old <= 180:
                category = '91-180_days'
            else:
                category = '180+_days'
            
            aging_categories[category].append({
                'batch_id': batch.id,
                'batch_number': batch.batch_number,
                'product_name': batch.product.name,
                'received_date': batch.received_date.isoformat(),
                'days_old': days_old,
                'received_quantity': batch.received_quantity
            })
        
        # Calculate summary
        summary = {}
        for category, batches_list in aging_categories.items():
            summary[category] = {
                'batch_count': len(batches_list),
                'total_quantity': sum(b['received_quantity'] for b in batches_list)
            }
        
        return {
            'aging_categories': aging_categories,
            'summary': summary,
            'total_batches': len(batches),
            'total_quantity': sum(batch.received_quantity for batch in batches)
        }
    
    def get_expiry_alert_report(self, days_ahead: int = 30) -> Dict[str, Any]:
        """Get expiry alert report"""
        cutoff_date = date.today() + timedelta(days=days_ahead)
        
        query = self.db_session.query(Batch).filter(
            and_(
                Batch.expiry_date <= cutoff_date,
                Batch.expiry_date >= date.today(),
                Batch.status == 'ACTIVE',
                Batch.qc_status == 'PASSED'
            )
        ).order_by(Batch.expiry_date.asc())
        
        expiring_batches = query.all()
        
        # Categorize by urgency
        today = date.today()
        urgency_categories = {
            'critical': [],  # 0-7 days
            'high': [],      # 8-14 days
            'medium': [],    # 15-21 days
            'low': []        # 22+ days
        }
        
        for batch in expiring_batches:
            days_to_expiry = (batch.expiry_date - today).days
            
            # Get available stock for this batch
            available_stock = self._get_available_stock_for_batch(batch.id)
            
            batch_info = {
                'batch_id': batch.id,
                'batch_number': batch.batch_number,
                'product_name': batch.product.name,
                'product_code': batch.product.product_code,
                'expiry_date': batch.expiry_date.isoformat(),
                'days_to_expiry': days_to_expiry,
                'received_quantity': batch.received_quantity,
                'available_quantity': available_stock
            }
            
            if days_to_expiry <= 7:
                urgency_categories['critical'].append(batch_info)
            elif days_to_expiry <= 14:
                urgency_categories['high'].append(batch_info)
            elif days_to_expiry <= 21:
                urgency_categories['medium'].append(batch_info)
            else:
                urgency_categories['low'].append(batch_info)
        
        return {
            'urgency_categories': urgency_categories,
            'summary': {
                'total_expiring_batches': len(expiring_batches),
                'critical_count': len(urgency_categories['critical']),
                'high_count': len(urgency_categories['high']),
                'medium_count': len(urgency_categories['medium']),
                'low_count': len(urgency_categories['low'])
            }
        }
    
    def get_low_stock_alert(self, minimum_threshold: int = 10) -> List[Dict[str, Any]]:
        """Get low stock alert untuk products"""
        # This is a simplified version - you might want to implement 
        # per-product thresholds in the future
        
        products = self.db_session.query(Product).filter(Product.is_active == True).all()
        low_stock_products = []
        
        for product in products:
            stock_summary = self.get_stock_summary_by_product(product.id)
            available_stock = stock_summary['stock_summary']['total_unreserved']
            
            if available_stock <= minimum_threshold:
                low_stock_products.append({
                    'product': {
                        'id': product.id,
                        'name': product.name,
                        'code': product.product_code
                    },
                    'available_stock': available_stock,
                    'threshold': minimum_threshold,
                    'status': 'critical' if available_stock == 0 else 'low'
                })
        
        return sorted(low_stock_products, key=lambda x: x['available_stock'])
    
    def _get_expiring_batches_for_product(self, product_id: int, days_ahead: int) -> List[Dict[str, Any]]:
        """Get expiring batches untuk specific product"""
        cutoff_date = date.today() + timedelta(days=days_ahead)
        
        query = self.db_session.query(Batch).filter(
            and_(
                Batch.product_id == product_id,
                Batch.expiry_date <= cutoff_date,
                Batch.expiry_date >= date.today(),
                Batch.status == 'ACTIVE'
            )
        ).order_by(Batch.expiry_date.asc())
        
        batches = query.all()
        
        result = []
        for batch in batches:
            days_to_expiry = (batch.expiry_date - date.today()).days
            available_stock = self._get_available_stock_for_batch(batch.id)
            
            result.append({
                'batch_id': batch.id,
                'batch_number': batch.batch_number,
                'expiry_date': batch.expiry_date.isoformat(),
                'days_to_expiry': days_to_expiry,
                'available_quantity': available_stock
            })
        
        return result
    
    def _get_available_stock_for_batch(self, batch_id: int) -> int:
        """Get available stock untuk specific batch"""
        batch = self.db_session.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            return 0
        
        # Calculate total allocated
        total_allocated = self.db_session.query(
            func.sum(Allocation.allocated_quantity - Allocation.shipped_quantity)
        ).filter(
            and_(Allocation.batch_id == batch_id, Allocation.status == 'active')
        ).scalar() or 0
        
        return batch.received_quantity - total_allocated