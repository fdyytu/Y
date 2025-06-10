from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID
from models.audit.audit_base import AuditEntry
from models.common.enums import Status

class AuditLog(AuditEntry):
    """Enhanced audit log implementation."""
    
    def __init__(self,
                 action: str,
                 user_id: str,
                 resource_type: str,
                 resource_id: str,
                 details: str = '',
                 status: Status = Status.ACTIVE,
                 id: UUID = None):
        super().__init__(action, user_id, resource_type, resource_id, status, id)
        self.details = details
        self.ip_address: Optional[str] = None
        self.user_agent: Optional[str] = None
        self.session_id: Optional[str] = None
        self.request_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit log to dictionary."""
        base_dict = super().to_dict()
        return {
            **base_dict,
            'details': self.details,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'session_id': self.session_id,
            'request_id': self.request_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditLog':
        """Create audit log from dictionary."""
        log = cls(
            action=data['action'],
            user_id=data['user_id'],
            resource_type=data['resource_type'],
            resource_id=data['resource_id'],
            details=data.get('details', ''),
            status=Status(data['status']),
            id=UUID(data['id']) if data.get('id') else None
        )
        
        # Set audit information
        if data.get('created_by'):
            log.set_created_by(data['created_by'])
        if data.get('updated_by'):
            log.set_updated_by(data['updated_by'])
        if data.get('deleted_by'):
            log.set_deleted_by(data['deleted_by'])
            
        # Set timestamps if provided
        if data.get('created_at'):
            log._created_at = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            log._updated_at = datetime.fromisoformat(data['updated_at'])
        if data.get('deleted_at'):
            log._deleted_at = datetime.fromisoformat(data['deleted_at'])
            
        log.metadata = data.get('metadata', {})
        log.ip_address = data.get('ip_address')
        log.user_agent = data.get('user_agent')
        log.session_id = data.get('session_id')
        log.request_id = data.get('request_id')
        return log
    
    def set_request_context(self, ip_address: str = None, user_agent: str = None, 
                          session_id: str = None, request_id: str = None):
        """Set request context information."""
        if ip_address:
            self.ip_address = ip_address
        if user_agent:
            self.user_agent = user_agent
        if session_id:
            self.session_id = session_id
        if request_id:
            self.request_id = request_id
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata to the audit log."""
        self.metadata[key] = value
        
    def get_summary(self) -> str:
        """Get a human-readable summary of the audit log."""
        return f"User {self.user_id} performed '{self.action}' on {self.resource_type}:{self.resource_id}"
