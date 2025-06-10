"""
Mixins untuk menambahkan functionality ke domain models.

Available mixins:
- TimestampMixin: Menambahkan created_at dan updated_at
- AuditMixin: Menambahkan audit trail (created_by, updated_by, dll)
- SoftDeleteMixin: Menambahkan soft delete functionality
"""

from .timestamp_mixin import TimestampMixin
from .audit_mixin import AuditMixin
from .softdelete_mixin import SoftDeleteMixin

__all__ = [
    'TimestampMixin',
    'AuditMixin', 
    'SoftDeleteMixin'
]
