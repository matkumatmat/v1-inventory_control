"""
ERP Integration Service
=======================

CRITICAL SERVICE untuk ERP integration dan data synchronization
"""

import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..base import BaseService, transactional, audit_log
from ..exceptions import ERPIntegrationError, ValidationError
from ...models import ERPSyncLog, Product, Customer, SalesOrder

class ERPService(BaseService):
    """CRITICAL SERVICE untuk ERP Integration"""
    
    def __init__(self, db_session: AsyncSession, erp_base_url: str, api_key: str,
                 current_user: str = None, audit_service=None, notification_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)
        self.erp_base_url = erp_base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = 30  # 30 seconds timeout
    
    @transactional
    @audit_log('SYNC_PRODUCTS', 'ERPSync')
    async def sync_products_from_erp(self) -> Dict[str, Any]:
        """Sync products dari ERP system"""
        try:
            # Call ERP API
            response = self._make_erp_request('GET', '/api/products')
            erp_products = response.get('data', [])
            
            synced_count = 0
            error_count = 0
            errors = []
            
            for erp_product in erp_products:
                try:
                    await self._sync_single_product(erp_product)
                    synced_count += 1
                except Exception as e:
                    error_count += 1
                    errors.append({
                        'product_code': erp_product.get('code'),
                        'error': str(e)
                    })
            
            # Log sync result
            await self._log_sync_operation('PRODUCT_SYNC', 'SUCCESS', {
                'synced_count': synced_count,
                'error_count': error_count,
                'total_products': len(erp_products)
            })
            
            return {
                'success': True,
                'synced_count': synced_count,
                'error_count': error_count,
                'errors': errors
            }
            
        except Exception as e:
            await self._log_sync_operation('PRODUCT_SYNC', 'ERROR', {'error': str(e)})
            raise ERPIntegrationError(f"Failed to sync products: {str(e)}")
    
    @transactional
    @audit_log('SYNC_CUSTOMERS', 'ERPSync')
    async def sync_customers_from_erp(self) -> Dict[str, Any]:
        """Sync customers dari ERP system"""
        try:
            response = self._make_erp_request('GET', '/api/customers')
            erp_customers = response.get('data', [])
            
            synced_count = 0
            error_count = 0
            errors = []
            
            for erp_customer in erp_customers:
                try:
                    await self._sync_single_customer(erp_customer)
                    synced_count += 1
                except Exception as e:
                    error_count += 1
                    errors.append({
                        'customer_code': erp_customer.get('code'),
                        'error': str(e)
                    })
            
            await self._log_sync_operation('CUSTOMER_SYNC', 'SUCCESS', {
                'synced_count': synced_count,
                'error_count': error_count,
                'total_customers': len(erp_customers)
            })
            
            return {
                'success': True,
                'synced_count': synced_count,
                'error_count': error_count,
                'errors': errors
            }
            
        except Exception as e:
            await self._log_sync_operation('CUSTOMER_SYNC', 'ERROR', {'error': str(e)})
            raise ERPIntegrationError(f"Failed to sync customers: {str(e)}")
    
    @transactional
    @audit_log('SYNC_SALES_ORDERS', 'ERPSync')
    async def sync_sales_orders_from_erp(self, start_date: date = None) -> Dict[str, Any]:
        """Sync sales orders dari ERP system"""
        try:
            params = {}
            if start_date:
                params['start_date'] = start_date.isoformat()
            
            response = self._make_erp_request('GET', '/api/sales-orders', params=params)
            erp_orders = response.get('data', [])
            
            synced_count = 0
            error_count = 0
            errors = []
            
            for erp_order in erp_orders:
                try:
                    await self._sync_single_sales_order(erp_order)
                    synced_count += 1
                except Exception as e:
                    error_count += 1
                    errors.append({
                        'so_number': erp_order.get('so_number'),
                        'error': str(e)
                    })
            
            await self._log_sync_operation('SALES_ORDER_SYNC', 'SUCCESS', {
                'synced_count': synced_count,
                'error_count': error_count,
                'total_orders': len(erp_orders)
            })
            
            return {
                'success': True,
                'synced_count': synced_count,
                'error_count': error_count,
                'errors': errors
            }
            
        except Exception as e:
            await self._log_sync_operation('SALES_ORDER_SYNC', 'ERROR', {'error': str(e)})
            raise ERPIntegrationError(f"Failed to sync sales orders: {str(e)}")
    
    async def send_shipment_confirmation_to_erp(self, shipment_id: int) -> bool:
        """Send shipment confirmation ke ERP"""
        try:
            from ...models import Shipment
            shipment = await self._get_or_404(Shipment, shipment_id)
            
            payload = {
                'shipment_number': shipment.shipment_number,
                'tracking_number': shipment.tracking_number,
                'shipped_date': shipment.shipped_date.isoformat() if shipment.shipped_date else None,
                'carrier': shipment.carrier.name if shipment.carrier else None,
                'packing_slip_number': shipment.packing_slip.ps_number if shipment.packing_slip else None
            }
            
            response = self._make_erp_request('POST', '/api/shipment-confirmations', data=payload)
            
            await self._log_sync_operation('SHIPMENT_CONFIRMATION', 'SUCCESS', {
                'shipment_id': shipment_id,
                'erp_response': response
            })
            
            return True
            
        except Exception as e:
            await self._log_sync_operation('SHIPMENT_CONFIRMATION', 'ERROR', {
                'shipment_id': shipment_id,
                'error': str(e)
            })
            return False
    
    async def send_inventory_update_to_erp(self, product_id: int, new_quantity: int) -> bool:
        """Send inventory update ke ERP"""
        try:
            product = await self._get_or_404(Product, product_id)
            
            payload = {
                'product_code': product.product_code,
                'quantity': new_quantity,
                'update_date': datetime.utcnow().isoformat()
            }
            
            response = self._make_erp_request('POST', '/api/inventory-updates', data=payload)
            
            await self._log_sync_operation('INVENTORY_UPDATE', 'SUCCESS', {
                'product_id': product_id,
                'quantity': new_quantity,
                'erp_response': response
            })
            
            return True
            
        except Exception as e:
            await self._log_sync_operation('INVENTORY_UPDATE', 'ERROR', {
                'product_id': product_id,
                'error': str(e)
            })
            return False
    
    def get_erp_order_status(self, so_number: str) -> Dict[str, Any]:
        """Get order status dari ERP"""
        try:
            response = self._make_erp_request('GET', f'/api/sales-orders/{so_number}/status')
            return response.get('data', {})
            
        except Exception as e:
            raise ERPIntegrationError(f"Failed to get order status: {str(e)}")
    
    def _make_erp_request(self, method: str, endpoint: str, 
                         data: Dict[str, Any] = None, 
                         params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make HTTP request ke ERP system.
        NOTE: This method uses the synchronous `requests` library. For a fully
        asynchronous service, this should be replaced with an async HTTP client
        like `httpx` or `aiohttp`.
        """
        url = f"{self.erp_base_url}{endpoint}"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'WMS-Integration/1.0'
        }
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=self.timeout)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=self.timeout)
            else:
                raise ERPIntegrationError(f"Unsupported HTTP method: {method}")
            
            # Check response status
            if response.status_code >= 400:
                raise ERPIntegrationError(
                    f"ERP API error: {response.status_code} - {response.text}",
                    erp_response=response.text
                )
            
            return response.json()
            
        except requests.exceptions.Timeout:
            raise ERPIntegrationError("ERP API request timeout")
        except requests.exceptions.ConnectionError:
            raise ERPIntegrationError("Failed to connect to ERP system")
        except requests.exceptions.RequestException as e:
            raise ERPIntegrationError(f"ERP API request failed: {str(e)}")
    
    async def _sync_single_product(self, erp_product: Dict[str, Any]):
        """Sync single product dari ERP"""
        product_code = erp_product.get('code')
        if not product_code:
            raise ValidationError("Product code is required")
        
        # Check if product exists
        result = await self.db_session.execute(
            select(Product).filter(Product.product_code == product_code)
        )
        existing_product = result.scalars().first()
        
        # Map ERP data to WMS format
        product_data = {
            'product_code': product_code,
            'name': erp_product.get('name'),
            'generic_name': erp_product.get('generic_name'),
            'manufacturer': erp_product.get('manufacturer'),
            'strength': erp_product.get('strength'),
            'unit_of_measure': erp_product.get('unit_of_measure'),
            'product_type_id': self._map_product_type(erp_product.get('type')),
            'is_active': erp_product.get('is_active', True)
        }
        
        if existing_product:
            # Update existing product
            for key, value in product_data.items():
                if value is not None:
                    setattr(existing_product, key, value)
            self._set_audit_fields(existing_product, is_update=True)
        else:
            # Create new product
            new_product = Product(**product_data)
            self._set_audit_fields(new_product)
            self.db_session.add(new_product)
        
        await self.db_session.flush()
    
    async def _sync_single_customer(self, erp_customer: Dict[str, Any]):
        """Sync single customer dari ERP"""
        customer_code = erp_customer.get('code')
        if not customer_code:
            raise ValidationError("Customer code is required")
        
        # Check if customer exists
        result = await self.db_session.execute(
            select(Customer).filter(Customer.customer_code == customer_code)
        )
        existing_customer = result.scalars().first()
        
        # Map ERP data to WMS format
        customer_data = {
            'customer_code': customer_code,
            'name': erp_customer.get('name'),
            'legal_name': erp_customer.get('legal_name'),
            'email': erp_customer.get('email'),
            'phone': erp_customer.get('phone'),
            'customer_type_id': self._map_customer_type(erp_customer.get('type')),
            'is_active': erp_customer.get('is_active', True)
        }
        
        if existing_customer:
            # Update existing customer
            for key, value in customer_data.items():
                if value is not None:
                    setattr(existing_customer, key, value)
            self._set_audit_fields(existing_customer, is_update=True)
        else:
            # Create new customer
            new_customer = Customer(**customer_data)
            self._set_audit_fields(new_customer)
            self.db_session.add(new_customer)
        
        await self.db_session.flush()
    
    async def _sync_single_sales_order(self, erp_order: Dict[str, Any]):
        """Sync single sales order dari ERP"""
        so_number = erp_order.get('so_number')
        if not so_number:
            raise ValidationError("SO number is required")
        
        # Check if SO exists
        result = await self.db_session.execute(
            select(SalesOrder).filter(SalesOrder.so_number == so_number)
        )
        existing_so = result.scalars().first()
        
        if existing_so:
            # Update existing SO status if needed
            erp_status = erp_order.get('status')
            if erp_status and erp_status != existing_so.status:
                existing_so.status = erp_status
                self._set_audit_fields(existing_so, is_update=True)
        else:
            # Create new SO would require SalesOrderService
            # This is a simplified implementation
            pass
    
    def _map_product_type(self, erp_type: str) -> Optional[int]:
        """Map ERP product type ke WMS product type ID"""
        # This would be configured based on your ERP mapping
        type_mapping = {
            'PHARMA': 1,
            'MEDICAL_DEVICE': 2,
            'SUPPLEMENT': 3
        }
        return type_mapping.get(erp_type)
    
    def _map_customer_type(self, erp_type: str) -> Optional[int]:
        """Map ERP customer type ke WMS customer type ID"""
        type_mapping = {
            'HOSPITAL': 1,
            'PHARMACY': 2,
            'CLINIC': 3,
            'DISTRIBUTOR': 4
        }
        return type_mapping.get(erp_type)
    
    async def _log_sync_operation(self, operation_type: str, status: str, details: Dict[str, Any]):
        """Log sync operation"""
        sync_log = ERPSyncLog(
            operation_type=operation_type,
            status=status,
            details=json.dumps(details),
            executed_by=self.current_user,
            executed_at=datetime.utcnow()
        )
        
        self.db_session.add(sync_log)
        await self.db_session.flush()