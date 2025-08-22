"""
User Service
============

Service untuk User management dan profile operations
"""

import hashlib
import secrets
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc


from ..base import CRUDService, transactional, audit_log
from ..exceptions import ValidationError, ConflictError, AuthenticationError
from ...models import User, UserSession, UserActivity
from ...schemas import UserSchema, UserCreateSchema, UserUpdateSchema, PasswordChangeSchema

class UserService(CRUDService):
    """Service untuk User management"""
    
    model_class = User
    create_schema = UserCreateSchema
    update_schema = UserUpdateSchema
    response_schema = UserSchema
    search_fields = ['username', 'email', 'full_name']
    
    def __init__(self, db_session: Session, current_user: str = None,
                 audit_service=None, notification_service=None):
        super().__init__(db_session, current_user, audit_service, notification_service)
    
    @transactional
    @audit_log('CREATE', 'User')
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create user dengan validation"""
        # Validate username uniqueness
        username = data.get('username')
        if username:
            self._validate_unique_field(User, 'username', username,
                                      error_message=f"Username '{username}' already exists")
        
        # Validate email uniqueness
        email = data.get('email')
        if email:
            self._validate_unique_field(User, 'email', email,
                                      error_message=f"Email '{email}' already exists")
        
        # Hash password
        if 'password' in data:
            data['password_hash'] = self._hash_password(data['password'])
            del data['password']  # Remove plain password
        
        # Set password expiry (90 days from creation)
        data['password_expires_at'] = datetime.utcnow() + timedelta(days=90)
        
        # Create user
        user_data = super().create(data)
        
        # Send welcome notification
        if self.notification_service and email:
            self.notification_service.send_welcome_email(
                email=email,
                username=username,
                full_name=data.get('full_name')
            )
        
        return user_data
    
    @transactional
    @audit_log('UPDATE', 'User')
    def update(self, entity_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user dengan validation"""
        user = self._get_or_404(User, entity_id)
        
        # Validate username uniqueness if changed
        username = data.get('username')
        if username and username != user.username:
            self._validate_unique_field(User, 'username', username,
                                      exclude_id=entity_id,
                                      error_message=f"Username '{username}' already exists")
        
        # Validate email uniqueness if changed
        email = data.get('email')
        if email and email != user.email:
            self._validate_unique_field(User, 'email', email,
                                      exclude_id=entity_id,
                                      error_message=f"Email '{email}' already exists")
        
        # Don't allow password update through this method
        if 'password' in data:
            del data['password']
        
        return super().update(entity_id, data)
    
    @transactional
    @audit_log('CHANGE_PASSWORD', 'User')
    def change_password(self, user_id: int, current_password: str, 
                       new_password: str) -> Dict[str, Any]:
        """Change user password"""
        user = self._get_or_404(User, user_id)
        
        # Verify current password
        if not self._verify_password(current_password, user.password_hash):
            raise AuthenticationError("Current password is incorrect")
        
        # Validate new password
        self._validate_password_strength(new_password)
        
        # Check password history (prevent reuse of last 5 passwords)
        if self._is_password_reused(user_id, new_password):
            raise ValidationError("Cannot reuse recent passwords")
        
        # Update password
        user.password_hash = self._hash_password(new_password)
        user.password_changed_at = datetime.utcnow()
        user.password_expires_at = datetime.utcnow() + timedelta(days=90)
        user.failed_login_attempts = 0
        user.is_locked = False
        user.locked_until = None
        
        # Invalidate all sessions (force re-login)
        self._invalidate_user_sessions(user_id)
        
        self._set_audit_fields(user, is_update=True)
        
        # Send notification
        if self.notification_service and user.email:
            self.notification_service.send_password_changed_notification(
                email=user.email,
                username=user.username
            )
        
        return self.response_schema().dump(user)
    
    @transactional
    @audit_log('RESET_PASSWORD', 'User')
    def reset_password(self, username_or_email: str) -> bool:
        """Initiate password reset"""
        # Find user by username or email
        user = self.db.query(User).filter(
            or_(User.username == username_or_email, User.email == username_or_email)
        ).first()
        
        if not user:
            # Don't reveal if user exists or not
            return True
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        reset_expires = datetime.utcnow() + timedelta(hours=24)  # 24 hours
        
        user.password_reset_token = reset_token
        user.password_reset_expires = reset_expires
        self._set_audit_fields(user, is_update=True)
        
        # Send reset email
        if self.notification_service and user.email:
            self.notification_service.send_password_reset_email(
                email=user.email,
                username=user.username,
                reset_token=reset_token
            )
        
        return True
    
    @transactional
    @audit_log('CONFIRM_RESET', 'User')
    def confirm_password_reset(self, reset_token: str, new_password: str) -> Dict[str, Any]:
        """Confirm password reset dengan token"""
        # Find user by reset token
        user = self.db.query(User).filter(
            and_(
                User.password_reset_token == reset_token,
                User.password_reset_expires > datetime.utcnow()
            )
        ).first()
        
        if not user:
            raise ValidationError("Invalid or expired reset token")
        
        # Validate new password
        self._validate_password_strength(new_password)
        
        # Update password
        user.password_hash = self._hash_password(new_password)
        user.password_changed_at = datetime.utcnow()
        user.password_expires_at = datetime.utcnow() + timedelta(days=90)
        user.password_reset_token = None
        user.password_reset_expires = None
        user.failed_login_attempts = 0
        user.is_locked = False
        user.locked_until = None
        
        # Invalidate all sessions
        self._invalidate_user_sessions(user.id)
        
        self._set_audit_fields(user, is_update=True)
        
        return self.response_schema().dump(user)
    
    @transactional
    @audit_log('ACTIVATE', 'User')
    def activate_user(self, user_id: int) -> Dict[str, Any]:
        """Activate user account"""
        user = self._get_or_404(User, user_id)
        
        user.is_active = True
        user.activated_at = datetime.utcnow()
        user.activated_by = self.current_user
        self._set_audit_fields(user, is_update=True)
        
        return self.response_schema().dump(user)
    
    @transactional
    @audit_log('DEACTIVATE', 'User')
    def deactivate_user(self, user_id: int, reason: str = None) -> Dict[str, Any]:
        """Deactivate user account"""
        user = self._get_or_404(User, user_id)
        
        user.is_active = False
        user.deactivated_at = datetime.utcnow()
        user.deactivated_by = self.current_user
        
        if reason:
            user.notes = f"Deactivated: {reason}. {user.notes or ''}"
        
        # Invalidate all sessions
        self._invalidate_user_sessions(user_id)
        
        self._set_audit_fields(user, is_update=True)
        
        return self.response_schema().dump(user)
    
    @transactional
    @audit_log('UNLOCK', 'User')
    def unlock_user(self, user_id: int) -> Dict[str, Any]:
        """Unlock user account"""
        user = self._get_or_404(User, user_id)
        
        user.is_locked = False
        user.locked_until = None
        user.failed_login_attempts = 0
        self._set_audit_fields(user, is_update=True)
        
        return self.response_schema().dump(user)
    
    def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Get user profile with additional info"""
        user = self._get_or_404(User, user_id)
        
        # Get recent activities
        recent_activities = self.db.query(UserActivity).filter(
            UserActivity.user_id == user_id
        ).order_by(UserActivity.timestamp.desc()).limit(10).all()
        
        # Get active sessions
        active_sessions = self.db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        ).count()
        
        user_data = self.response_schema().dump(user)
        user_data.update({
            'recent_activities': [
                {
                    'activity_type': activity.activity_type,
                    'timestamp': activity.timestamp.isoformat(),
                    'ip_address': activity.ip_address
                }
                for activity in recent_activities
            ],
            'active_sessions_count': active_sessions,
            'password_expires_in_days': (
                (user.password_expires_at - datetime.utcnow()).days
                if user.password_expires_at else None
            )
        })
        
        return user_data
    
    def get_users_by_role(self, role: str) -> List[Dict[str, Any]]:
        """Get users by role"""
        users = self.db.query(User).filter(
            and_(User.role == role, User.is_active == True)
        ).order_by(User.full_name.asc()).all()
        
        return self.response_schema(many=True).dump(users)
    
    def get_user_activity_report(self, user_id: int = None, 
                               start_date: datetime = None,
                               end_date: datetime = None) -> Dict[str, Any]:
        """Get user activity report"""
        query = self.db.query(UserActivity)
        
        if user_id:
            query = query.filter(UserActivity.user_id == user_id)
        
        if start_date:
            query = query.filter(UserActivity.timestamp >= start_date)
        if end_date:
            query = query.filter(UserActivity.timestamp <= end_date)
        
        activities = query.all()
        
        # Group by activity type
        by_activity_type = {}
        for activity in activities:
            activity_type = activity.activity_type
            if activity_type not in by_activity_type:
                by_activity_type[activity_type] = 0
            by_activity_type[activity_type] += 1
        
        # Group by user
        by_user = {}
        for activity in activities:
            user_id = activity.user_id
            if user_id not in by_user:
                by_user[user_id] = {
                    'user_id': user_id,
                    'username': activity.user.username,
                    'full_name': activity.user.full_name,
                    'total_activities': 0
                }
            by_user[user_id]['total_activities'] += 1
        
        return {
            'summary': {
                'total_activities': len(activities),
                'unique_users': len(by_user)
            },
            'by_activity_type': by_activity_type,
            'by_user': list(by_user.values())
        }
    
    def _hash_password(self, password: str) -> str:
        """Hash password - simple implementation"""
        # In production, use proper password hashing like bcrypt
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return hashlib.sha256(password.encode()).hexdigest() == password_hash
    
    def _validate_password_strength(self, password: str):
        """Validate password strength"""
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in password):
            raise ValidationError("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            raise ValidationError("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            raise ValidationError("Password must contain at least one number")
    
    def _is_password_reused(self, user_id: int, new_password: str) -> bool:
        """Check if password was recently used"""
        # Simple implementation - in production, store password history
        user = self._get_or_404(User, user_id)
        return self._verify_password(new_password, user.password_hash)
    
    def _invalidate_user_sessions(self, user_id: int):
        """Invalidate all user sessions"""
        sessions = self.db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            )
        ).all()
        
        for session in sessions:
            session.is_active = False
            session.logout_reason = 'PASSWORD_CHANGED'