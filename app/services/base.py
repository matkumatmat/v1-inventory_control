"""
Base Service Classes
====================

Base classes dan utilities untuk semua services
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from functools import wraps
import logging
import uuid

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from .exceptions import WMSException, ValidationError, NotFoundError, ConflictError
from ..schemas import PaginationSchema

logger = logging.getLogger(__name__)

def transactional(func):
    """Decorator untuk automatic transaction management"""
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        try:
            result = await func(self, *args, **kwargs)
            if hasattr(self, 'db_session') and self.db_session:
                await self.db_session.commit()
            return result
        except Exception as e:
            if hasattr(self, 'db_session') and self.db_session:
                await self.db_session.rollback()
            logger.error(f"Transaction failed in {func.__name__}: {str(e)}")
            raise
    return wrapper

def audit_log(action: str, entity_type: str):
    """Decorator untuk audit logging"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            start_time = datetime.utcnow()
            request_id = str(uuid.uuid4())
            
            try:
                result = await func(self, *args, **kwargs)
                
                # Log successful operation
                if hasattr(self, 'audit_service') and self.audit_service:
                    entity_id = None
                    if hasattr(result, 'id'):
                        entity_id = result.id
                    elif isinstance(result, dict) and 'id' in result:
                        entity_id = result['id']
                    
                    await self.audit_service.log_action(
                        entity_type=entity_type,
                        entity_id=entity_id,
                        action=action,
                        request_id=request_id
                    )
                
                return result
                
            except Exception as e:
                # Log failed operation
                if hasattr(self, 'audit_service') and self.audit_service:
                    await self.audit_service.log_error(
                        entity_type=entity_type,
                        action=action,
                        error=str(e),
                        request_id=request_id
                    )
                raise
        return wrapper
    return decorator

class BaseService(ABC):
    """Base service class dengan common functionality"""
    
    def __init__(self, db_session: Session, current_user: str = None, 
                 audit_service=None, notification_service=None):
        self.db_session = db_session
        self.current_user = current_user
        self.audit_service = audit_service
        self.notification_service = notification_service
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def _get_or_404(self, model_class, entity_id: int, error_message: str = None):
        """Get entity by ID or raise 404 error"""
        result = await self.db_session.execute(select(model_class).filter(model_class.id == entity_id))
        entity = result.scalars().first()
        if not entity:
            resource_type = model_class.__name__
            raise NotFoundError(resource_type, entity_id)
        return entity
    
    async def _get_by_public_id_or_404(self, model_class, public_id: str):
        """Get entity by public_id or raise 404 error"""
        result = await self.db_session.execute(select(model_class).filter(model_class.public_id == public_id))
        entity = result.scalars().first()
        if not entity:
            resource_type = model_class.__name__
            raise NotFoundError(resource_type, public_id)
        return entity
    
    async def _validate_unique_field(self, model_class, field_name: str, field_value: Any, 
                              exclude_id: int = None, error_message: str = None):
        """Validate that field value is unique"""
        query = select(model_class).filter(getattr(model_class, field_name) == field_value)
        if exclude_id:
            query = query.filter(model_class.id != exclude_id)
        
        result = await self.db_session.execute(query)
        existing = result.scalars().first()
        if existing:
            message = error_message or f"{field_name} '{field_value}' already exists"
            raise ConflictError(message, model_class.__name__)
    
    async def _paginate_query(self, query, page: int = 1, per_page: int = 20, 
                       max_per_page: int = 100):
        """Paginate query results"""
        per_page = min(per_page, max_per_page)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db_session.execute(count_query)
        total = total_result.scalar()
        
        # Calculate pagination info
        pages = (total + per_page - 1) // per_page if total > 0 else 1
        has_prev = page > 1
        has_next = page < pages
        
        # Get paginated results
        offset = (page - 1) * per_page
        paginated_query = query.offset(offset).limit(per_page)
        items_result = await self.db_session.execute(paginated_query)
        items = items_result.scalars().all()
        
        return {
            'items': items,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': pages,
                'has_prev': has_prev,
                'has_next': has_next
            }
        }
    
    async def _apply_filters(self, query, model_class, filters: Dict[str, Any]):
        """Apply filters to query"""
        for field, value in filters.items():
            if value is not None:
                if hasattr(model_class, field):
                    query = query.filter(getattr(model_class, field) == value)
        return query
    
    async def _apply_search(self, query, model_class, search_term: str, search_fields: List[str]):
        """Apply text search to query"""
        if not search_term or not search_fields:
            return query
        
        search_conditions = []
        for field in search_fields:
            if hasattr(model_class, field):
                field_attr = getattr(model_class, field)
                search_conditions.append(field_attr.ilike(f'%{search_term}%'))
        
        if search_conditions:
            from sqlalchemy import or_
            query = query.filter(or_(*search_conditions))
        
        return query
    
    async def _apply_sorting(self, query, model_class, sort_by: str = None, 
                      sort_order: str = 'asc', default_sort: str = 'id'):
        """Apply sorting to query"""
        sort_field = sort_by or default_sort
        
        if hasattr(model_class, sort_field):
            field_attr = getattr(model_class, sort_field)
            if sort_order.lower() == 'desc':
                query = query.order_by(field_attr.desc())
            else:
                query = query.order_by(field_attr.asc())
        
        return query
    
    def _set_audit_fields(self, entity, is_update: bool = False):
        """Set audit fields pada entity"""
        if is_update:
            entity.last_modified_by = self.current_user
            entity.last_modified_date = datetime.utcnow()
        else:
            entity.created_by = self.current_user
            entity.created_date = datetime.utcnow()
    
    async def _send_notification(self, notification_type: str, recipients: List[str], 
                          context: Dict[str, Any]):
        """Send notification through notification service"""
        if self.notification_service:
            try:
                await self.notification_service.send_notification(
                    notification_type=notification_type,
                    recipients=recipients,
                    context=context
                )
            except Exception as e:
                self.logger.warning(f"Failed to send notification: {str(e)}")

class CRUDService(BaseService):
    """Service class dengan CRUD operations standard"""
    
    @property
    @abstractmethod
    def model_class(self):
        """Model class yang digunakan service ini"""
        pass
    
    @property
    @abstractmethod
    def create_schema(self):
        """Schema untuk create operations"""
        pass
    
    @property
    @abstractmethod
    def update_schema(self):
        """Schema untuk update operations"""
        pass
    
    @property
    @abstractmethod
    def response_schema(self):
        """Schema untuk response"""
        pass
    
    @transactional
    @audit_log('CREATE', 'Entity')
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new entity"""
        # Validate input data
        validated_data = self.create_schema().load(data)
        
        # Create entity
        entity = self.model_class(**validated_data)
        self._set_audit_fields(entity)
        
        self.db_session.add(entity)
        await self.db_session.flush()  # Get ID
        
        # Return serialized entity
        return self.response_schema().dump(entity)
    
    async def get_by_id(self, entity_id: int) -> Dict[str, Any]:
        """Get entity by ID"""
        entity = await self._get_or_404(self.model_class, entity_id)
        return self.response_schema().dump(entity)
    
    async def get_by_public_id(self, public_id: str) -> Dict[str, Any]:
        """Get entity by public_id"""
        entity = await self._get_by_public_id_or_404(self.model_class, public_id)
        return self.response_schema().dump(entity)
    
    async def list(self, page: int = 1, per_page: int = 20, search: str = None,
             filters: Dict[str, Any] = None, sort_by: str = None, 
             sort_order: str = 'asc') -> Dict[str, Any]:
        """List entities with pagination, search, and filters"""
        query = select(self.model_class)
        
        # Apply filters
        if filters:
            query = await self._apply_filters(query, self.model_class, filters)
        
        # Apply search
        if search and hasattr(self, 'search_fields'):
            query = await self._apply_search(query, self.model_class, search, self.search_fields)
        
        # Apply sorting
        query = await self._apply_sorting(query, self.model_class, sort_by, sort_order)
        
        # Paginate
        result = await self._paginate_query(query, page, per_page)
        
        return {
            'items': self.response_schema(many=True).dump(result['items']),
            'pagination': result['pagination']
        }
    
    @transactional
    @audit_log('UPDATE', 'Entity')
    async def update(self, entity_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update entity"""
        # Get existing entity
        entity = await self._get_or_404(self.model_class, entity_id)
        
        # Validate input data
        validated_data = self.update_schema().load(data)
        
        # Update entity
        for key, value in validated_data.items():
            setattr(entity, key, value)
        
        self._set_audit_fields(entity, is_update=True)
        
        # Return serialized entity
        return self.response_schema().dump(entity)
    
    @transactional
    @audit_log('DELETE', 'Entity')
    async def delete(self, entity_id: int) -> bool:
        """Delete entity"""
        entity = await self._get_or_404(self.model_class, entity_id)
        
        # Soft delete if supported
        if hasattr(entity, 'is_active'):
            entity.is_active = False
            self._set_audit_fields(entity, is_update=True)
        else:
            self.db_session.delete(entity)
        
        return True
    
    @transactional
    @audit_log('ACTIVATE', 'Entity')
    async def activate(self, entity_id: int) -> Dict[str, Any]:
        """Activate entity (for soft delete support)"""
        entity = await self._get_or_404(self.model_class, entity_id)
        
        if hasattr(entity, 'is_active'):
            entity.is_active = True
            self._set_audit_fields(entity, is_update=True)
            return self.response_schema().dump(entity)
        else:
            raise ValidationError("Entity does not support activation")