"""
Audit Service
=============

CRITICAL SERVICE untuk audit logging dan compliance tracking
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, select

from ..base import BaseService, transactional
from ...models import AuditLog, UserActivity

class AuditService(BaseService):
    """CRITICAL SERVICE untuk Audit dan Compliance"""
    
    def __init__(self, db_session: Session, current_user: str = None):
        super().__init__(db_session, current_user)
    
    @transactional
    async def log_action(self, entity_type: str, entity_id: Optional[int],
                         action: str, request_id: str = None,
                         old_values: Dict[str, Any] = None,
                         new_values: Dict[str, Any] = None,
                         user_id: int = None, username: str = None,
                         ip_address: str = None, user_agent: str = None,
                         notes: str = None, severity: str = "INFO") -> int:
        """Log audit action"""

        # If user_id is not provided, try to find it by username
        if user_id is None and username:
            from ...models import User  # Avoid circular import
            result = await self.db_session.execute(select(User).filter(User.username == username))
            user = result.scalars().first()
            if user:
                user_id = user.id

        audit_log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id if entity_id is not None else -1,
            action=action,
            user_id=user_id,
            username=username or self.current_user,
            timestamp=datetime.utcnow(),
            request_id=request_id,
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None,
            ip_address=ip_address,
            user_agent=user_agent,
            notes=notes,
            severity=severity
        )
        
        self.db_session.add(audit_log)
        await self.db_session.flush()
        
        return audit_log.id
    
    @transactional
    async def log_error(self, entity_type: str, action: str, error: str,
                 request_id: str = None) -> int:
        """Log error/failure in audit"""
        
        return await self.log_action(
            entity_type=entity_type,
            entity_id=None,
            action=f"{action}_FAILED",
            request_id=request_id,
            new_values={'error': error},
        )
    
    @transactional
    async def log_security_event(self, event_type: str, user_id: int = None,
                                 username: str = None, ip_address: str = None,
                                 user_agent: str = None, details: Dict[str, Any] = None,
                                 severity: str = "WARNING") -> int:
        """Log security-related events"""

        # Consolidate details for the notes field
        notes_details = {
            'reason': details.get('reason') if details else 'N/A',
            'username_provided': username,
        }

        return await self.log_action(
            entity_type='SECURITY',
            entity_id=user_id,
            action=event_type,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            notes=json.dumps(notes_details),
            severity=severity
        )
    
    async def get_audit_trail(self, entity_type: str = None, entity_id: int = None,
                       user_id: int = None, start_date: datetime = None,
                       end_date: datetime = None, page: int = 1,
                       per_page: int = 50) -> Dict[str, Any]:
        """Get audit trail with filters"""
        
        query = select(AuditLog)
        
        # Apply filters
        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)
        if entity_id:
            query = query.where(AuditLog.entity_id == entity_id)
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if start_date:
            query = query.where(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.where(AuditLog.timestamp <= end_date)
        
        # Order by timestamp descending
        query = query.order_by(AuditLog.timestamp.desc())
        
        # Paginate
        result = await self._paginate_query(query, page, per_page)
        
        # Convert to serializable format
        audit_logs = []
        for log in result['items']:
            audit_logs.append({
                'id': log.id,
                'entity_type': log.entity_type,
                'entity_id': log.entity_id,
                'action': log.action,
                'user_id': log.user_id,
                'username': log.username,
                'timestamp': log.timestamp.isoformat(),
                'request_id': log.request_id,
                'old_values': json.loads(log.old_values) if log.old_values else None,
                'new_values': json.loads(log.new_values) if log.new_values else None,
            })
        
        return {
            'audit_logs': audit_logs,
            'pagination': result['pagination']
        }
    
    async def generate_compliance_report(self, start_date: date, end_date: date,
                                 report_type: str = 'FULL') -> Dict[str, Any]:
        """Generate compliance report"""
        
        # Get audit logs for period
        result = await self.db_session.execute(
            select(AuditLog).where(
                and_(
                    AuditLog.timestamp >= start_date,
                    AuditLog.timestamp <= end_date
                )
            )
        )
        audit_logs = result.scalars().all()
        
        # Get user activities for period
        result = await self.db_session.execute(
            select(UserActivity).where(
                and_(
                    UserActivity.timestamp >= start_date,
                    UserActivity.timestamp <= end_date
                )
            )
        )
        user_activities = result.scalars().all()
        
        # Analysis
        total_actions = len(audit_logs)
        unique_users = len(set(log.user_id for log in audit_logs if log.user_id))
        
        # Actions by type
        actions_by_type = {}
        for log in audit_logs:
            action_type = log.action
            actions_by_type[action_type] = actions_by_type.get(action_type, 0) + 1
        
        # Actions by user
        actions_by_user = {}
        for log in audit_logs:
            username = log.username or 'SYSTEM'
            actions_by_user[username] = actions_by_user.get(username, 0) + 1
        
        # Failed actions
        failed_actions = [log for log in audit_logs if 'FAILED' in log.action or 'ERROR' in log.action]
        
        # Security events
        security_events = [log for log in audit_logs if log.entity_type == 'SECURITY']
        
        # Daily activity summary
        daily_activity = {}
        for log in audit_logs:
            day = log.timestamp.date()
            daily_activity[day] = daily_activity.get(day, 0) + 1
        
        # High-risk actions (configurable)
        high_risk_actions = ['DELETE', 'TERMINATE', 'CANCEL', 'DEACTIVATE']
        critical_actions = [
            log for log in audit_logs 
            if any(risk_action in log.action for risk_action in high_risk_actions)
        ]
        
        return {
            'report_title': 'Compliance Audit Report',
            'report_type': report_type,
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'generated_at': datetime.utcnow().isoformat(),
            'generated_by': self.current_user,
            
            'summary': {
                'total_actions': total_actions,
                'unique_users': unique_users,
                'failed_actions': len(failed_actions),
                'security_events': len(security_events),
                'critical_actions': len(critical_actions)
            },
            
            'analysis': {
                'actions_by_type': dict(sorted(actions_by_type.items(), key=lambda x: x[1], reverse=True)),
                'actions_by_user': dict(sorted(actions_by_user.items(), key=lambda x: x[1], reverse=True)),
                'daily_activity': {day.isoformat(): count for day, count in sorted(daily_activity.items())}
            },
            
            'alerts': {
                'failed_actions': [
                    {
                        'timestamp': log.timestamp.isoformat(),
                        'action': log.action,
                        'username': log.username,
                        'entity_type': log.entity_type,
                        'error': json.loads(log.new_values).get('error') if log.new_values else None
                    }
                    for log in failed_actions[-10:]  # Last 10 failures
                ],
                
                'critical_actions': [
                    {
                        'timestamp': log.timestamp.isoformat(),
                        'action': log.action,
                        'username': log.username,
                        'entity_type': log.entity_type,
                        'entity_id': log.entity_id
                    }
                    for log in critical_actions[-10:]  # Last 10 critical actions
                ],
                
                'security_events': [
                    {
                        'timestamp': log.timestamp.isoformat(),
                        'action': log.action,
                        'username': log.username,
                        'details': json.loads(log.new_values) if log.new_values else None
                    }
                    for log in security_events[-10:]  # Last 10 security events
                ]
            }
        }
    
    async def get_user_activity_summary(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get user activity summary"""
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get audit logs for user
        result = await self.db_session.execute(
            select(AuditLog).where(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.timestamp >= start_date
                )
            )
        )
        user_logs = result.scalars().all()
        
        # Get user activities
        result = await self.db_session.execute(
            select(UserActivity).where(
                and_(
                    UserActivity.user_id == user_id,
                    UserActivity.timestamp >= start_date
                )
            )
        )
        activities = result.scalars().all()
        
        # Analysis
        total_actions = len(user_logs)
        login_count = len([a for a in activities if a.activity_type == 'LOGIN'])
        unique_days_active = len(set(log.timestamp.date() for log in user_logs))
        
        # Actions by day
        actions_by_day = {}
        for log in user_logs:
            day = log.timestamp.date()
            actions_by_day[day] = actions_by_day.get(day, 0) + 1
        
        # Most common actions
        actions_by_type = {}
        for log in user_logs:
            action_type = log.action
            actions_by_type[action_type] = actions_by_type.get(action_type, 0) + 1
        
        return {
            'user_id': user_id,
            'analysis_period_days': days,
            'summary': {
                'total_actions': total_actions,
                'login_count': login_count,
                'unique_days_active': unique_days_active,
                'average_actions_per_day': round(total_actions / days, 2) if days > 0 else 0
            },
            'activity_pattern': {
                'actions_by_day': {day.isoformat(): count for day, count in sorted(actions_by_day.items())},
                'most_common_actions': dict(sorted(actions_by_type.items(), key=lambda x: x[1], reverse=True)[:10])
            }
        }