from datetime import datetime
from typing import Optional
from .timestamp_mixin import TimestampMixin

class AuditMixin(TimestampMixin):
    """Mixin untuk audit functionality (siapa yang create/update/delete)."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._created_by: Optional[str] = None
        self._updated_by: Optional[str] = None
        self._deleted_by: Optional[str] = None
        self._deleted_at: Optional[datetime] = None
        self._is_deleted: bool = False
    
    @property
    def created_by(self) -> Optional[str]:
        """User ID yang membuat entity ini."""
        return self._created_by
    
    @property
    def updated_by(self) -> Optional[str]:
        """User ID yang terakhir mengupdate entity ini."""
        return self._updated_by
    
    @property
    def deleted_by(self) -> Optional[str]:
        """User ID yang menghapus entity ini."""
        return self._deleted_by
    
    @property
    def deleted_at(self) -> Optional[datetime]:
        """Waktu entity dihapus (soft delete)."""
        return self._deleted_at
    
    @property
    def is_deleted(self) -> bool:
        """Apakah entity sudah dihapus (soft delete)."""
        return self._is_deleted
    
    def set_created_by(self, user_id: str):
        """Set siapa yang membuat entity ini."""
        self._created_by = user_id
    
    def set_updated_by(self, user_id: str):
        """Set siapa yang mengupdate entity ini."""
        self._updated_by = user_id
        self.update_timestamp()
    
    def set_deleted_by(self, user_id: str):
        """Soft delete entity ini."""
        self._deleted_by = user_id
        self._deleted_at = datetime.utcnow()
        self._is_deleted = True
    
    def restore(self, user_id: str):
        """Restore entity yang sudah di-soft delete."""
        self._deleted_by = None
        self._deleted_at = None
        self._is_deleted = False
        self.set_updated_by(user_id)
        
    def get_audit_info(self) -> dict:
        """Dapatkan informasi audit sebagai dictionary."""
        return {
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'deleted_by': self.deleted_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'is_deleted': self.is_deleted
        }
