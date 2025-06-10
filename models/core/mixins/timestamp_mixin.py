from datetime import datetime

class TimestampMixin:
    """Mixin for timestamp functionality."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._created_at = datetime.utcnow()
        self._updated_at = datetime.utcnow()
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
        
    @property
    def updated_at(self) -> datetime:
        return self._updated_at
    
    def update_timestamp(self):
        """Update the last modified timestamp."""
        self._updated_at = datetime.utcnow()
