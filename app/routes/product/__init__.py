"""
Product Domain Routes
=====================

Routes untuk product management (inbound operations)
"""

from .product_routes import router as product_router
from .batch_routes import router as batch_router  
from .allocation_routes import router as allocation_router
from .product_type_routes import router as product_type_router
from .package_type_routes import router as package_type_router      
from .temperature_type_routes import router as temperature_type_router      

__all__ = ['product_router', 'batch_router', 'allocation_router', 'product_type_router', 'package_type_router','temperature_type_router']