from datetime import datetime
from typing import Optional
from .timestamp_mixin import TimestampMixin

class AuditMixin(TimestampMixin):
    """Mixin for audit functionality."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._created_by: Optional[str] = None
        self._updated_by: Optional[str] = None
        self._deleted_by: Optional[str] = None
        self._deleted_at: Optional[datetime] = None
    
    @property
    def created_by(self) -> Optional[str]:
        return self._created_by
    
    @property
    def updated_by(self) -> Optional[str]:
        return self._updated_by
    
    @property
    def deleted_by(self) -> Optional[str]:
        return self._deleted_by
    
    @property
    def deleted_at(self) -> Optional[datetime]:
        return self._deleted_at
    
    def set_created_by(self, user_id: str):
        """Set who created this entity."""
        self._created_by = user_id
    
    def set_updated_by(self, user_id: str):
        """Set who updated this entity."""
        self._updated_by = user_id
        self.update_timestamp()
    
    def set_deleted_by(self, user_id: str):
        """Set who deleted this entity."""
        self._deleted_by = user_id
        self._deleted_at = datetime.utcnow()
        
    def get_audit_info(self) -> dict:
        """Get audit information as dictionary."""
        return {
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'deleted_by': self.deleted_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        }
