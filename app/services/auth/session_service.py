"""
User Session Service
====================

Service untuk User Session management
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

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
    
    def get_active_sessions(self, user_id: int = None) -> List[Dict[str, Any]]:
        """Get active sessions"""
        query = self.db.query(UserSession).filter(
            and_(
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        )
        
        if user_id:
            query = query.filter(UserSession.user_id == user_id)
        
        sessions = query.order_by(UserSession.last_activity.desc()).all()
        return self.response_schema(many=True).dump(sessions)
    
    @transactional
    @audit_log('TERMINATE_SESSION', 'UserSession')
    def terminate_session(self, session_id: str, reason: str = 'ADMIN') -> bool:
        """Terminate specific session"""
        session = self.db.query(UserSession).filter(
            UserSession.session_id == session_id
        ).first()
        
        if not session:
            raise NotFoundError('UserSession', session_id)
        
        session.is_active = False
        session.logout_reason = reason
        
        return True
    
    @transactional
    @audit_log('CLEANUP_SESSIONS', 'UserSession')
    def cleanup_expired_sessions(self) -> int:
        """Cleanup expired sessions"""
        expired_sessions = self.db.query(UserSession).filter(
            and_(
                UserSession.is_active == True,
                UserSession.expires_at <= datetime.utcnow()
            )
        ).all()
        
        count = 0
        for session in expired_sessions:
            session.is_active = False
            session.logout_reason = 'EXPIRED'
            count += 1
        
        return count
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get session statistics"""
        # Active sessions
        active_sessions = self.db.query(UserSession).filter(
            and_(
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        ).count()
        
        # Sessions today
        today = datetime.utcnow().date()
        sessions_today = self.db.query(UserSession).filter(
            func.date(UserSession.created_at) == today
        ).count()
        
        # Unique users today
        unique_users_today = self.db.query(UserSession.user_id).filter(
            func.date(UserSession.created_at) == today
        ).distinct().count()
        
        return {
            'active_sessions': active_sessions,
            'sessions_today': sessions_today,
            'unique_users_today': unique_users_today
        }