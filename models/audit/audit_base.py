from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID
from models.core.base_model import BaseModel
from models.core.mixins.audit_mixin import AuditMixin
from models.common.enums import Status

class AuditEntry(BaseModel, AuditMixin):
    """Base class for audit entries."""
    
    def __init__(self, 
                 action: str,
                 user_id: str,
                 resource_type: str,
                 resource_id: str,
                 status: Status = Status.ACTIVE,
                 id: UUID = None):
        super().__init__(id)
        self.action = action
        self.user_id = user_id
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.status = status
        self.metadata: Dict[str, Any] = {}
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit entry to dictionary."""
        base_dict = {
            'id': str(self.id),
            'action': self.action,
            'user_id': self.user_id,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'status': self.status.value,
            'metadata': self.metadata
        }
        
        # Include audit information from mixin
        audit_info = self.get_audit_info()
        base_dict.update(audit_info)
        
        return base_dict
    
    def log_action(self, performed_by: str):
        """Log who performed this audit action."""
        if not self.created_by:
            self.set_created_by(performed_by)
        else:
            self.set_updated_by(performed_by)
