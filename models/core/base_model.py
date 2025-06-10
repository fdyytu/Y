# Deprecated: File ini sudah dipindahkan ke models/base.py
# Import dari sini untuk backward compatibility

from models.base import Entity, AggregateRoot, BaseModel

# Alias untuk kompatibilitas
__all__ = ['Entity', 'AggregateRoot', 'BaseModel']
