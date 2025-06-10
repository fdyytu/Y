"""
Audit module for tracking and logging system activities.

This module provides comprehensive audit logging functionality including:
- Base audit entry classes
- Enhanced audit log implementation
- Repository pattern for data persistence
- Service layer for business logic
"""

from .audit_base import AuditEntry
from .audit_log import AuditLog
from .audit_repository import AuditRepositoryInterface, AuditRepository
from .audit_service import AuditService

__all__ = [
    'AuditEntry',
    'AuditLog', 
    'AuditRepositoryInterface',
    'AuditRepository',
    'AuditService'
]

# Version information
__version__ = '1.0.0'
__author__ = 'System Architecture Team'
