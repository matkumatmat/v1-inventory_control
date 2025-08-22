"""
Product Domain Routes
=====================

Routes untuk product management (inbound operations)
"""

from .product_routes import router as product_router
from .batch_routes import router as batch_router  
from .allocation_routes import router as allocation_router

__all__ = ['product_router', 'batch_router', 'allocation_router']