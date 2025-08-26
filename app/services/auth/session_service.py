"""
User Session Service
====================

Service untuk User Session management
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, select

from ..base import CRUDService, transactional, audit_log
from ..exceptions import ValidationError, NotFoundError
from ...models import UserSession, User
from ...schemas import UserSessionSchema, UserSessionCreateSchema, UserSessionUpdateSchema

class UserSessionService(CRUDService):
    """Service untuk User Session management"""
    
    model_class = UserSession
    create_schema = UserSessionCreateSchema
    update_schema = UserSessionUpdateSchema
    response_schema = UserSessionSchema
    
    async def get_active_sessions(self, user_id: int = None) -> List[Dict[str, Any]]:
        """Get active sessions"""
        stmt = select(UserSession).where(
            and_(
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        )
        
        if user_id:
            stmt = stmt.where(UserSession.user_id == user_id)
        
        stmt = stmt.order_by(UserSession.last_activity.desc())
        result = await self.db_session.execute(stmt)
        sessions = result.scalars().all()
        return self.response_schema(many=True).dump(sessions)
    
    @transactional
    @audit_log('TERMINATE_SESSION', 'UserSession')
    async def terminate_session(self, session_id: str, reason: str = 'ADMIN') -> bool:
        """Terminate specific session"""
        stmt = select(UserSession).where(
            UserSession.session_id == session_id
        )
        result = await self.db_session.execute(stmt)
        session = result.scalars().first()
        
        if not session:
            raise NotFoundError('UserSession', session_id)
        
        session.is_active = False
        session.logout_reason = reason
        
        return True
    
    @transactional
    @audit_log('CLEANUP_SESSIONS', 'UserSession')
    async def cleanup_expired_sessions(self) -> int:
        """Cleanup expired sessions"""
        stmt = select(UserSession).where(
            and_(
                UserSession.is_active == True,
                UserSession.expires_at <= datetime.utcnow()
            )
        )
        result = await self.db_session.execute(stmt)
        expired_sessions = result.scalars().all()
        
        count = 0
        for session in expired_sessions:
            session.is_active = False
            session.logout_reason = 'EXPIRED'
            count += 1
        
        return count
    
    async def get_session_statistics(self) -> Dict[str, Any]:
        """Get session statistics"""
        # Active sessions
        active_stmt = select(func.count(UserSession.id)).where(
            and_(
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        )
        active_sessions_result = await self.db_session.execute(active_stmt)
        active_sessions = active_sessions_result.scalar_one()
        
        # Sessions today
        today = datetime.utcnow().date()
        today_stmt = select(func.count(UserSession.id)).where(
            func.date(UserSession.created_at) == today
        )
        sessions_today_result = await self.db_session.execute(today_stmt)
        sessions_today = sessions_today_result.scalar_one()
        
        # Unique users today
        unique_users_stmt = select(func.count(func.distinct(UserSession.user_id))).where(
            func.date(UserSession.created_at) == today
        )
        unique_users_today_result = await self.db_session.execute(unique_users_stmt)
        unique_users_today = unique_users_today_result.scalar_one()
        
        return {
            'active_sessions': active_sessions,
            'sessions_today': sessions_today,
            'unique_users_today': unique_users_today
        }