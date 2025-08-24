"""
Authentication Service
======================

CRITICAL SERVICE untuk user authentication dan session management
"""

import hashlib
from typing import List
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, select


from ..base import BaseService, transactional, audit_log
from ..exceptions import AuthenticationError, AuthorizationError, ValidationError
from ...models import User, UserSession, UserActivity
from ...schemas import LoginSchema, LoginResponseSchema, UserProfileSchema

class AuthService(BaseService):
    """CRITICAL SERVICE untuk Authentication"""
    
    def __init__(self, db_session: Session, secret_key: str, 
                 audit_service=None, notification_service=None):
        super().__init__(db_session, audit_service=audit_service, 
                        notification_service=notification_service)
        self.secret_key = secret_key
        self.token_expiry_hours = 8  # 8 hours
        self.refresh_token_expiry_days = 30  # 30 days
    
    @audit_log('LOGIN', 'User')
    async def authenticate_user(self, username: str, password: str, 
                         ip_address: str = None, user_agent: str = None,
                         remember_me: bool = False) -> Dict[str, Any]:
        """Authenticate user dan create session"""
        # Find user
        result = await self.db_session.execute(select(User).filter(User.username == username))
        user = result.scalars().first()
        
        if not user:
            await self._log_failed_login(username, ip_address, 'USER_NOT_FOUND')
            raise AuthenticationError("Invalid username or password")
        
        # Check if user is locked
        if user.is_locked:
            if user.locked_until and user.locked_until > datetime.utcnow():
                remaining_minutes = int((user.locked_until - datetime.utcnow()).total_seconds() / 60)
                raise AuthenticationError(f"Account locked. Try again in {remaining_minutes} minutes")
            else:
                # Auto-unlock if lock period expired
                user.is_locked = False
                user.locked_until = None
                user.failed_login_attempts = 0
        
        # Verify password
        if not self._verify_password(password, user.password_hash):
            await self._handle_failed_login(user, ip_address)
            raise AuthenticationError("Invalid username or password")
        
        # Check if user can login
        if not user.is_active:
            raise AuthenticationError("Account is deactivated")
        
        # Check password expiry
        if user.password_expires_at and user.password_expires_at <= datetime.utcnow():
            raise AuthenticationError("Password has expired. Please reset your password")
        
        # Successful login - reset failed attempts
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()
        user.last_login_ip = ip_address
        self._set_audit_fields(user, is_update=True)
        
        # Create session
        session_data = await self._create_user_session(user, ip_address, user_agent, remember_me)
        
        # Generate tokens
        access_token = self._generate_access_token(user, session_data['session_id'])
        refresh_token = self._generate_refresh_token(user, session_data['session_id'])
        
        # Log activity
        await self._log_user_activity(user.id, 'LOGIN', ip_address, user_agent)
        
        # Prepare response
        response_data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': self.token_expiry_hours * 3600,  # seconds
            'user': UserProfileSchema().dump(user)
        }
        
        return LoginResponseSchema().load(response_data)
    
    @transactional
    @audit_log('LOGOUT', 'User')
    async def logout_user(self, session_id: str, user_id: int = None,
                   ip_address: str = None, user_agent: str = None) -> bool:
        """Logout user dan invalidate session"""
        # Find session
        session = self.db_session.query(UserSession).filter(
            UserSession.session_id == session_id
        ).first()
        
        if session:
            # Deactivate session
            session.is_active = False
            session.logout_reason = 'MANUAL'
            
            # Log activity
            if session.user_id:
                await self._log_user_activity(session.user_id, 'LOGOUT', ip_address, user_agent)
        
        return True
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token"""
        try:
            # Decode refresh token
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=['HS256'])
            
            user_id = payload.get('user_id')
            session_id = payload.get('session_id')
            token_type = payload.get('type')
            
            if token_type != 'refresh':
                raise AuthenticationError("Invalid token type")
            
            # Validate session
            session = self.db_session.query(UserSession).filter(
                and_(
                    UserSession.session_id == session_id,
                    UserSession.user_id == user_id,
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.utcnow()
                )
            ).first()
            
            if not session:
                raise AuthenticationError("Invalid or expired session")
            
            # Get user
            user = self.db_session.query(User).filter(
                and_(User.id == user_id, User.is_active == True)
            ).first()
            
            if not user:
                raise AuthenticationError("User not found or inactive")
            
            # Generate new access token
            new_access_token = self._generate_access_token(user, session_id)
            
            return {
                'access_token': new_access_token,
                'token_type': 'Bearer',
                'expires_in': self.token_expiry_hours * 3600
            }
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Refresh token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid refresh token")
    
    def verify_access_token(self, access_token: str) -> Dict[str, Any]:
        """Verify access token dan return user info"""
        try:
            # Decode token
            payload = jwt.decode(access_token, self.secret_key, algorithms=['HS256'])
            
            user_id = payload.get('user_id')
            session_id = payload.get('session_id')
            token_type = payload.get('type')
            
            if token_type != 'access':
                raise AuthenticationError("Invalid token type")
            
            # Validate session
            session = self.db_session.query(UserSession).filter(
                and_(
                    UserSession.session_id == session_id,
                    UserSession.user_id == user_id,
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.utcnow()
                )
            ).first()
            
            if not session:
                raise AuthenticationError("Invalid or expired session")
            
            # Get user
            user = self.db_session.query(User).filter(
                and_(User.id == user_id, User.is_active == True)
            ).first()
            
            if not user:
                raise AuthenticationError("User not found or inactive")
            
            # Update session last activity
            session.last_activity = datetime.utcnow()
            
            return {
                'user_id': user.id,
                'username': user.username,
                'role': user.role,
                'session_id': session_id
            }
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Access token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid access token")
    
    def check_permission(self, user_id: int, required_role: str = None,
                        required_permissions: List[str] = None) -> bool:
        """Check user permissions"""
        user = self.db_session.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            return False
        
        # Check role
        if required_role:
            role_hierarchy = {
                'superadmin': 3,
                'admin': 2,
                'user': 1
            }
            
            user_role_level = role_hierarchy.get(user.role, 0)
            required_role_level = role_hierarchy.get(required_role, 99)
            
            if user_role_level < required_role_level:
                return False
        
        # Additional permission checks could be implemented here
        
        return True
    
    def require_permission(self, user_id: int, required_role: str = None) -> bool:
        """Require permission atau raise exception"""
        if not self.check_permission(user_id, required_role):
            raise AuthorizationError(f"Insufficient permissions. Required role: {required_role}")
        return True
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        # Simple password verification - in production use proper hashing like bcrypt
        return hashlib.sha256(password.encode()).hexdigest() == password_hash
    
    def _hash_password(self, password: str) -> str:
        """Hash password"""
        # Simple hashing - in production use proper hashing like bcrypt
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generate_access_token(self, user: User, session_id: str) -> str:
        """Generate JWT access token"""
        payload = {
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'session_id': session_id,
            'type': 'access',
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=self.token_expiry_hours)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def _generate_refresh_token(self, user: User, session_id: str) -> str:
        """Generate JWT refresh token"""
        payload = {
            'user_id': user.id,
            'session_id': session_id,
            'type': 'refresh',
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(days=self.refresh_token_expiry_days)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def _create_user_session(self, user: User, ip_address: str = None,
                           user_agent: str = None, remember_me: bool = False) -> Dict[str, Any]:
        """Create user session"""
        session_id = secrets.token_urlsafe(32)
        
        # Session expiry
        if remember_me:
            expires_at = datetime.utcnow() + timedelta(days=self.refresh_token_expiry_days)
        else:
            expires_at = datetime.utcnow() + timedelta(hours=self.token_expiry_hours)
        
        session = UserSession(
            session_id=session_id,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            expires_at=expires_at,
            is_active=True
        )
        
        self.db_session.add(session)
        self.db_session.flush()
        
        # Update user current session
        user.current_session_id = session_id
        user.session_expires_at = expires_at
        
        return {
            'session_id': session_id,
            'expires_at': expires_at
        }
    
    def _handle_failed_login(self, user: User, ip_address: str = None):
        """Handle failed login attempt"""
        user.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.utcnow() + timedelta(minutes=30)  # Lock for 30 minutes
        
        self._set_audit_fields(user, is_update=True)
        
        # Log failed attempt
        self._log_failed_login(user.username, ip_address, 'INVALID_PASSWORD')
    
    def _log_failed_login(self, username: str, ip_address: str = None, reason: str = None):
        """Log failed login attempt"""
        if self.audit_service:
            self.audit_service.log_security_event(
                event_type='FAILED_LOGIN',
                username=username,
                ip_address=ip_address,
                details={'reason': reason}
            )
    
    def _log_user_activity(self, user_id: int, activity_type: str,
                          ip_address: str = None, user_agent: str = None):
        """Log user activity"""
        activity = UserActivity(
            user_id=user_id,
            activity_type=activity_type,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow()
        )
        
        self.db_session.add(activity)