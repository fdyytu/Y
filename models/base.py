from abc import ABC
from typing import Any, Optional
from datetime import datetime
from uuid import UUID, uuid4

class Entity(ABC):
    """Base entity untuk semua domain models.
    
    Menyediakan identitas unik dan basic functionality untuk semua entity.
    """
    
    def __init__(self, id: UUID = None):
        self._id = id or uuid4()
    
    @property
    def id(self) -> UUID:
        return self._id
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Entity):
            return False
        return self._id == other._id
    
    def __hash__(self) -> int:
        return hash(self._id)

class AggregateRoot(Entity):
    """Base class untuk aggregate roots dalam DDD pattern."""
    
    def __init__(self, id: UUID = None):
        super().__init__(id)
        self._domain_events = []
    
    def add_domain_event(self, event):
        """Tambahkan domain event."""
        self._domain_events.append(event)
    
    def clear_domain_events(self):
        """Hapus semua domain events."""
        self._domain_events.clear()
    
    @property
    def domain_events(self):
        """Dapatkan semua domain events."""
        return self._domain_events.copy()

class BaseModel(Entity):
    """Base model class yang kompatibel dengan struktur lama.
    
    Deprecated: Gunakan Entity atau AggregateRoot sebagai gantinya.
    """
    pass
