from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from models.audit.audit_log import AuditLog
from models.audit.audit_repository import AuditRepositoryInterface
from models.common.enums import Status

class AuditService:
    """Service for managing audit logs."""
    
    def __init__(self, audit_repository: AuditRepositoryInterface):
        self._repository = audit_repository
    
    async def log_action(self, 
                        action: str,
                        user_id: str,
                        resource_type: str,
                        resource_id: str,
                        details: str = '',
                        ip_address: str = None,
                        user_agent: str = None,
                        session_id: str = None,
                        request_id: str = None,
                        metadata: Dict[str, Any] = None,
                        performed_by: str = None) -> AuditLog:
        """Log an audit action."""
        audit_log = AuditLog(
            action=action,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details
        )
        
        # Set request context
        audit_log.set_request_context(
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            request_id=request_id
        )
        
        # Add metadata if provided
        if metadata:
            for key, value in metadata.items():
                audit_log.add_metadata(key, value)
        
        # Log who performed the action
        if performed_by:
            audit_log.log_action(performed_by)
        
        return await self._repository.save(audit_log)
    
    async def log_create_action(self,
                               user_id: str,
                               resource_type: str,
                               resource_id: str,
                               details: str = '',
                               **context) -> AuditLog:
        """Log a create action."""
        return await self.log_action(
            action='CREATE',
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or f"Created {resource_type} {resource_id}",
            **context
        )
    
    async def log_update_action(self,
                               user_id: str,
                               resource_type: str,
                               resource_id: str,
                               details: str = '',
                               **context) -> AuditLog:
        """Log an update action."""
        return await self.log_action(
            action='UPDATE',
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or f"Updated {resource_type} {resource_id}",
            **context
        )
    
    async def log_delete_action(self,
                               user_id: str,
                               resource_type: str,
                               resource_id: str,
                               details: str = '',
                               **context) -> AuditLog:
        """Log a delete action."""
        return await self.log_action(
            action='DELETE',
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or f"Deleted {resource_type} {resource_id}",
            **context
        )
    
    async def log_access_action(self,
                               user_id: str,
                               resource_type: str,
                               resource_id: str,
                               details: str = '',
                               **context) -> AuditLog:
        """Log an access action."""
        return await self.log_action(
            action='ACCESS',
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or f"Accessed {resource_type} {resource_id}",
            **context
        )
    
    async def get_audit_log(self, audit_id: UUID) -> Optional[AuditLog]:
        """Get a specific audit log by ID."""
        return await self._repository.find_by_id(audit_id)
    
    async def get_user_audit_logs(self, user_id: str, limit: int = 100) -> List[AuditLog]:
        """Get audit logs for a specific user."""
        return await self._repository.find_by_user(user_id, limit)
    
    async def get_resource_audit_logs(self, resource_type: str, resource_id: str, limit: int = 100) -> List[AuditLog]:
        """Get audit logs for a specific resource."""
        return await self._repository.find_by_resource(resource_type, resource_id, limit)
    
    async def get_audit_logs_by_date_range(self, start_date: datetime, end_date: datetime, limit: int = 100) -> List[AuditLog]:
        """Get audit logs within a date range."""
        return await self._repository.find_by_date_range(start_date, end_date, limit)
    
    async def search_audit_logs(self,
                               user_id: Optional[str] = None,
                               resource_type: Optional[str] = None,
                               resource_id: Optional[str] = None,
                               action: Optional[str] = None,
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None,
                               status: Optional[Status] = None,
                               limit: int = 100,
                               offset: int = 0) -> List[AuditLog]:
        """Search audit logs with multiple filters."""
        return await self._repository.find_with_filters(
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            start_date=start_date,
            end_date=end_date,
            status=status,
            limit=limit,
            offset=offset
        )
    
    async def count_audit_logs(self,
                              user_id: Optional[str] = None,
                              resource_type: Optional[str] = None,
                              resource_id: Optional[str] = None,
                              action: Optional[str] = None,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None,
                              status: Optional[Status] = None) -> int:
        """Count audit logs with filters."""
        return await self._repository.count_by_filters(
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            start_date=start_date,
            end_date=end_date,
            status=status
        )
    
    async def cleanup_old_logs(self, days_to_keep: int = 365) -> int:
        """Clean up old audit logs."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        return await self._repository.delete_old_logs(cutoff_date)
    
    async def get_audit_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get audit summary for a user."""
        start_date = datetime.utcnow() - timedelta(days=days)
        logs = await self._repository.find_with_filters(
            user_id=user_id,
            start_date=start_date,
            limit=1000
        )
        
        # Aggregate statistics
        action_counts = {}
        resource_counts = {}
        daily_counts = {}
        
        for log in logs:
            # Count by action
            action_counts[log.action] = action_counts.get(log.action, 0) + 1
            
            # Count by resource type
            resource_counts[log.resource_type] = resource_counts.get(log.resource_type, 0) + 1
            
            # Count by day
            day_key = log.created_at.date().isoformat()
            daily_counts[day_key] = daily_counts.get(day_key, 0) + 1
        
        return {
            'total_actions': len(logs),
            'action_breakdown': action_counts,
            'resource_breakdown': resource_counts,
            'daily_activity': daily_counts,
            'period_days': days,
            'most_active_day': max(daily_counts.items(), key=lambda x: x[1]) if daily_counts else None,
            'most_common_action': max(action_counts.items(), key=lambda x: x[1]) if action_counts else None
        }
