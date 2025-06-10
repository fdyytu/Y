from datetime import datetime
from typing import Optional

class SoftDeleteMixin:
    """Mixin for soft delete functionality."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._deleted_at: Optional[datetime] = None
        self._is_deleted: bool = False
    
    @property
    def deleted_at(self) -> Optional[datetime]:
        return self._deleted_at
    
    @property
    def is_deleted(self) -> bool:
        return self._is_deleted
    
    def soft_delete(self):
        """Mark entity as deleted without removing from database."""
        self._deleted_at = datetime.utcnow()
        self._is_deleted = True
        self.update_timestamp()
    
    def restore(self):
        """Restore soft deleted entity."""
        self._deleted_at = None
        self._is_deleted = False
        self.update_timestamp()
