"""
Product Service
===============

Service untuk mengelola Product dan related entities
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from ..base import CRUDService, transactional, audit_log
from ..exceptions import ValidationError, ConflictError, NotFoundError
from ...models import Product, ProductType, PackageType, TemperatureType
from ...schemas import (
    ProductSchema, ProductCreateSchema, ProductUpdateSchema,
    ProductTypeSchema, ProductTypeCreateSchema, ProductTypeUpdateSchema,
    PackageTypeSchema, PackageTypeCreateSchema, PackageTypeUpdateSchema,
    TemperatureTypeSchema, TemperatureTypeCreateSchema, TemperatureTypeUpdateSchema,
)

class ProductService(CRUDService):
    """Service untuk Product management"""
    
    model_class = Product
    create_schema = ProductCreateSchema
    update_schema = ProductUpdateSchema
    response_schema = ProductSchema
    search_fields = ['name', 'product_code', 'generic_name', 'manufacturer']
    
    def __init__(self, db_session: AsyncSession, current_user: str = None, 
                 audit_service=None, notification_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)
    
    @transactional
    @audit_log('CREATE', 'Product')
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new product with validation"""
        # Validate product code uniqueness
        product_code = data.get('product_code')
        if product_code:
            await self._validate_unique_field(Product, 'product_code', product_code,
                                      error_message=f"Product code '{product_code}' already exists")
        
        # Validate references exist
        await self._validate_product_type(data.get('product_type_id'))
        if data.get('package_type_id'):
            await self._validate_package_type(data.get('package_type_id'))
        if data.get('temperature_type_id'):
            await self._validate_temperature_type(data.get('temperature_type_id'))
        
        return await super().create(data)
    
    @transactional
    @audit_log('UPDATE', 'Product')
    async def update(self, entity_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update product with validation"""
        # Validate product code uniqueness if changed
        product_code = data.get('product_code')
        if product_code:
            await self._validate_unique_field(Product, 'product_code', product_code, 
                                      exclude_id=entity_id,
                                      error_message=f"Product code '{product_code}' already exists")
        
        # Validate references exist
        if data.get('product_type_id'):
            await self._validate_product_type(data.get('product_type_id'))
        if data.get('package_type_id'):
            await self._validate_package_type(data.get('package_type_id'))
        if data.get('temperature_type_id'):
            await self._validate_temperature_type(data.get('temperature_type_id'))
        
        return await super().update(entity_id, data)
    
    async def get_by_code(self, product_code: str) -> Dict[str, Any]:
        """Get product by product code"""
        result = await self.db_session.execute(
            select(Product).filter(Product.product_code == product_code)
        )
        product = result.scalars().first()
        
        if not product:
            raise NotFoundError('Product', product_code)
        
        return self.response_schema().dump(product)
    
    async def search_products(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search products by name, code, or generic name"""
        query = select(Product).filter(Product.is_active == True)
        
        if search_term:
            search_filter = or_(
                Product.name.ilike(f'%{search_term}%'),
                Product.product_code.ilike(f'%{search_term}%'),
                Product.generic_name.ilike(f'%{search_term}%')
            )
            query = query.filter(search_filter)
        
        result = await self.db_session.execute(query.limit(limit))
        products = result.scalars().all()
        return self.response_schema(many=True).dump(products)
    
    async def get_product_stock_summary(self, product_id: int) -> Dict[str, Any]:
        """Get stock summary untuk product"""
        from ...models import Batch, Allocation
        
        product = await self._get_or_404(Product, product_id)
        
        # Get all batches for this product
        batches_query = select(Batch).filter(
            Batch.product_id == product_id,
            Batch.status == 'ACTIVE'
        )
        
        batches_result = await self.db_session.execute(batches_query)
        batches = batches_result.scalars().all()
        total_received = sum(batch.received_quantity for batch in batches)
        
        # Get all allocations for this product
        allocations_query = select(Allocation).join(Batch).filter(
            Batch.product_id == product_id,
            Allocation.status == 'active'
        )
        
        allocations_result = await self.db_session.execute(allocations_query)
        allocations = allocations_result.scalars().all()
        total_allocated = sum(alloc.allocated_quantity for alloc in allocations)
        total_shipped = sum(alloc.shipped_quantity for alloc in allocations)
        total_available = total_allocated - total_shipped
        
        return {
            'product': self.response_schema().dump(product),
            'stock_summary': {
                'total_received': total_received,
                'total_allocated': total_allocated,
                'total_shipped': total_shipped,
                'total_available': total_available,
                'active_batches': len(batches),
                'active_allocations': len(allocations)
            }
        }
    
    async def _validate_product_type(self, product_type_id: int):
        """Validate product type exists"""
        result = await self.db_session.execute(
            select(ProductType).filter(ProductType.id == product_type_id)
        )
        if not result.scalars().first():
            raise ValidationError(f"Product type with ID {product_type_id} not found")
    
    async def _validate_package_type(self, package_type_id: int):
        """Validate package type exists"""
        result = await self.db_session.execute(
            select(PackageType).filter(PackageType.id == package_type_id)
        )
        if not result.scalars().first():
            raise ValidationError(f"Package type with ID {package_type_id} not found")
    
    async def _validate_temperature_type(self, temperature_type_id: int):
        """Validate temperature type exists"""
        result = await self.db_session.execute(
            select(TemperatureType).filter(TemperatureType.id == temperature_type_id)
        )
        if not result.scalars().first():
            raise ValidationError(f"Temperature type with ID {temperature_type_id} not found")

