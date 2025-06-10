"""Core models dan base classes untuk domain models."""

from models.base import Entity, AggregateRoot, BaseModel
from .mixins import TimestampMixin, AuditMixin, SoftDeleteMixin

__all__ = [
    # Base Classes
    'Entity',
    'AggregateRoot', 
    'BaseModel',  # Deprecated, gunakan Entity atau AggregateRoot
    
    # Mixins
    'TimestampMixin',
    'AuditMixin',
    'SoftDeleteMixin'
]
