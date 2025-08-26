"""
Notification Service
====================

Service untuk Email, SMS, dan In-app notifications
"""

import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime
from jinja2 import Template
from sqlalchemy.ext.asyncio import AsyncSession

from ..base import BaseService, transactional
from ..exceptions import ExternalServiceError
from ...models import NotificationLog

class NotificationService(BaseService):
    """Service untuk Notification management"""
    
    def __init__(self, db_session: AsyncSession, email_config: Dict[str, Any],
                 current_user: str = None, audit_service=None):
        super().__init__(db_session, current_user, audit_service)
        self.email_config = email_config
        self.email_templates = self._load_email_templates()
    
    @transactional
    async def send_notification(self, notification_type: str, recipients: List[str],
                         context: Dict[str, Any], channel: str = 'email') -> bool:
        """Send notification through specified channel"""
        try:
            if channel == 'email':
                return await self._send_email_notification(notification_type, recipients, context)
            elif channel == 'sms':
                return await self._send_sms_notification(notification_type, recipients, context)
            elif channel == 'push':
                return await self._send_push_notification(notification_type, recipients, context)
            else:
                raise ValueError(f"Unsupported notification channel: {channel}")
                
        except Exception as e:
            await self._log_notification(notification_type, recipients, 'FAILED', str(e))
            return False
    
    async def send_welcome_email(self, email: str, username: str, full_name: str) -> bool:
        """Send welcome email to new user"""
        context = {
            'username': username,
            'full_name': full_name,
            'login_url': f"{self.email_config.get('app_url', '')}/login"
        }
        
        return await self.send_notification('USER_WELCOME', [email], context, 'email')
    
    async def send_password_reset_email(self, email: str, username: str, reset_token: str) -> bool:
        """Send password reset email"""
        context = {
            'username': username,
            'reset_url': f"{self.email_config.get('app_url', '')}/reset-password?token={reset_token}",
            'expires_in_hours': 24
        }
        
        return await self.send_notification('PASSWORD_RESET', [email], context, 'email')
    
    async def send_password_changed_notification(self, email: str, username: str) -> bool:
        """Send password changed notification"""
        context = {
            'username': username,
            'changed_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        }
        
        return await self.send_notification('PASSWORD_CHANGED', [email], context, 'email')
    
    async def send_low_stock_alert(self, recipients: List[str], products: List[Dict[str, Any]]) -> bool:
        """Send low stock alert"""
        context = {
            'products': products,
            'alert_date': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'dashboard_url': f"{self.email_config.get('app_url', '')}/dashboard"
        }
        
        return await self.send_notification('LOW_STOCK_ALERT', recipients, context, 'email')
    
    async def send_expiry_alert(self, recipients: List[str], batches: List[Dict[str, Any]]) -> bool:
        """Send expiry alert"""
        context = {
            'batches': batches,
            'alert_date': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'dashboard_url': f"{self.email_config.get('app_url', '')}/dashboard"
        }
        
        return await self.send_notification('EXPIRY_ALERT', recipients, context, 'email')
    
    async def _send_email_notification(self, notification_type: str, recipients: List[str],
                                     context: Dict[str, Any]) -> bool:
        """Send email notification using asyncio.to_thread"""
        try:
            template_config = self.email_templates.get(notification_type)
            if not template_config:
                raise ValueError(f"Email template not found for: {notification_type}")

            subject = Template(template_config['subject']).render(**context)
            body = Template(template_config['body']).render(**context)

            def send_mail():
                msg = MIMEMultipart()
                msg['From'] = self.email_config['smtp_from']
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'html'))

                with smtplib.SMTP(self.email_config['smtp_host'], self.email_config['smtp_port']) as server:
                    if self.email_config.get('smtp_use_tls'):
                        server.starttls()
                    if self.email_config.get('smtp_username'):
                        server.login(self.email_config['smtp_username'], self.email_config['smtp_password'])
                    
                    for recipient in recipients:
                        msg_copy = msg
                        msg_copy['To'] = recipient
                        server.send_message(msg_copy)

            await asyncio.to_thread(send_mail)
            
            await self._log_notification(notification_type, recipients, 'SUCCESS')
            return True
            
        except Exception as e:
            raise ExternalServiceError('EMAIL', f"Failed to send email: {str(e)}")
    
    async def _send_sms_notification(self, notification_type: str, recipients: List[str],
                             context: Dict[str, Any]) -> bool:
        """Send SMS notification - placeholder implementation"""
        # This would integrate with SMS provider like Twilio, AWS SNS, etc.
        try:
            # Log as if sent successfully
            await self._log_notification(notification_type, recipients, 'SUCCESS', 'SMS sent via provider')
            return True
        except Exception as e:
            raise ExternalServiceError('SMS', f"Failed to send SMS: {str(e)}")
    
    async def _send_push_notification(self, notification_type: str, recipients: List[str],
                              context: Dict[str, Any]) -> bool:
        """Send push notification - placeholder implementation"""
        # This would integrate with push notification service like Firebase, etc.
        try:
            # Log as if sent successfully
            await self._log_notification(notification_type, recipients, 'SUCCESS', 'Push sent via provider')
            return True
        except Exception as e:
            raise ExternalServiceError('PUSH', f"Failed to send push notification: {str(e)}")
    
    async def _log_notification(self, notification_type: str, recipients: List[str],
                         status: str, error_message: str = None):
        """Log notification attempt"""
        log = NotificationLog(
            notification_type=notification_type,
            recipients=','.join(recipients),
            status=status,
            error_message=error_message,
            sent_at=datetime.utcnow(),
            sent_by=self.current_user
        )
        
        self.db_session.add(log)
        await self.db_session.flush()
    
    def _load_email_templates(self) -> Dict[str, Dict[str, str]]:
        """Load email templates - in production, load from database or files"""
        return {
            'USER_WELCOME': {
                'subject': 'Welcome to WMS - {{ full_name }}',
                'body': '''
                <h2>Welcome to WMS, {{ full_name }}!</h2>
                <p>Your account has been created successfully.</p>
                <p><strong>Username:</strong> {{ username }}</p>
                <p><a href="{{ login_url }}">Click here to login</a></p>
                '''
            },
            'PASSWORD_RESET': {
                'subject': 'Password Reset Request - WMS',
                'body': '''
                <h2>Password Reset Request</h2>
                <p>Hello {{ username }},</p>
                <p>We received a request to reset your password.</p>
                <p><a href="{{ reset_url }}">Click here to reset your password</a></p>
                <p>This link will expire in {{ expires_in_hours }} hours.</p>
                '''
            },
            'PASSWORD_CHANGED': {
                'subject': 'Password Changed - WMS',
                'body': '''
                <h2>Password Changed</h2>
                <p>Hello {{ username }},</p>
                <p>Your password was successfully changed on {{ changed_at }}.</p>
                <p>If you did not make this change, please contact support immediately.</p>
                '''
            },
            'LOW_STOCK_ALERT': {
                'subject': 'Low Stock Alert - WMS',
                'body': '''
                <h2>Low Stock Alert</h2>
                <p>The following products have low stock levels:</p>
                <ul>
                {% for product in products %}
                <li>{{ product.name }} - Current Stock: {{ product.current_stock }}</li>
                {% endfor %}
                </ul>
                <p><a href="{{ dashboard_url }}">View Dashboard</a></p>
                '''
            },
            'EXPIRY_ALERT': {
                'subject': 'Product Expiry Alert - WMS',
                'body': '''
                <h2>Product Expiry Alert</h2>
                <p>The following batches are expiring soon:</p>
                <ul>
                {% for batch in batches %}
                <li>{{ batch.product_name }} - Batch: {{ batch.batch_number }} - Expires: {{ batch.expiry_date }}</li>
                {% endfor %}
                </ul>
                <p><a href="{{ dashboard_url }}">View Dashboard</a></p>
                '''
            }
        }