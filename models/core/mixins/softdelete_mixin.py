from datetime import datetime
from typing import Optional

class SoftDeleteMixin:
    """Mixin untuk soft delete functionality."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._deleted_at: Optional[datetime] = None
        self._deleted_by: Optional[str] = None
        self._is_deleted: bool = False
    
    @property
    def deleted_at(self) -> Optional[datetime]:
        """Waktu entity dihapus."""
        return self._deleted_at
    
    @property
    def deleted_by(self) -> Optional[str]:
        """User ID yang menghapus entity."""
        return self._deleted_by
    
    @property
    def is_deleted(self) -> bool:
        """Apakah entity sudah dihapus."""
        return self._is_deleted
    
    def soft_delete(self, user_id: Optional[str] = None):
        """Soft delete entity."""
        self._deleted_at = datetime.utcnow()
        self._deleted_by = user_id
        self._is_deleted = True
    
    def restore(self, user_id: Optional[str] = None):
        """Restore entity yang sudah di-soft delete."""
        self._deleted_at = None
        self._deleted_by = None
        self._is_deleted = False
        
        # Update timestamp jika ada mixin timestamp
        if hasattr(self, 'update_timestamp'):
            self.update_timestamp()
        
        # Update audit info jika ada audit mixin
        if hasattr(self, 'set_updated_by') and user_id:
            self.set_updated_by(user_id)
    
    def is_active(self) -> bool:
        """Apakah entity masih aktif (tidak dihapus)."""
        return not self._is_deleted
