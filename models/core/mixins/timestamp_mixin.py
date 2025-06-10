from datetime import datetime

class TimestampMixin:
    """Mixin untuk menambahkan timestamp functionality ke entity."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._created_at = datetime.utcnow()
        self._updated_at = datetime.utcnow()
    
    @property
    def created_at(self) -> datetime:
        """Waktu entity dibuat."""
        return self._created_at
        
    @property
    def updated_at(self) -> datetime:
        """Waktu terakhir entity diupdate."""
        return self._updated_at
    
    def update_timestamp(self):
        """Update timestamp terakhir dimodifikasi."""
        self._updated_at = datetime.utcnow()
    
    def set_created_at(self, timestamp: datetime):
        """Set waktu created (untuk data import/migration)."""
        self._created_at = timestamp
    
    def set_updated_at(self, timestamp: datetime):
        """Set waktu updated (untuk data import/migration)."""
        self._updated_at = timestamp
