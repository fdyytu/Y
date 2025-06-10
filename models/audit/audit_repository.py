from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from models.audit.audit_log import AuditLog
from models.common.enums import Status

class AuditRepositoryInterface(ABC):
    """Interface for audit repository."""
    
    @abstractmethod
    async def save(self, audit_log: AuditLog) -> AuditLog:
        """Save audit log entry."""
        pass
    
    @abstractmethod
    async def find_by_id(self, audit_id: UUID) -> Optional[AuditLog]:
        """Find audit log by ID."""
        pass
    
    @abstractmethod
    async def find_by_user(self, user_id: str, limit: int = 100) -> List[AuditLog]:
        """Find audit logs by user ID."""
        pass
    
    @abstractmethod
    async def find_by_resource(self, resource_type: str, resource_id: str, limit: int = 100) -> List[AuditLog]:
        """Find audit logs by resource."""
        pass
    
    @abstractmethod
    async def find_by_date_range(self, start_date: datetime, end_date: datetime, limit: int = 100) -> List[AuditLog]:
        """Find audit logs by date range."""
        pass
    
    @abstractmethod
    async def find_with_filters(self,
                              user_id: Optional[str] = None,
                              resource_type: Optional[str] = None,
                              resource_id: Optional[str] = None,
                              action: Optional[str] = None,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None,
                              status: Optional[Status] = None,
                              limit: int = 100,
                              offset: int = 0) -> List[AuditLog]:
        """Find audit logs with multiple filters."""
        pass
    
    @abstractmethod
    async def count_by_filters(self,
                             user_id: Optional[str] = None,
                             resource_type: Optional[str] = None,
                             resource_id: Optional[str] = None,
                             action: Optional[str] = None,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None,
                             status: Optional[Status] = None) -> int:
        """Count audit logs with filters."""
        pass
    
    @abstractmethod
    async def delete_old_logs(self, older_than: datetime) -> int:
        """Delete audit logs older than specified date."""
        pass

class AuditRepository(AuditRepositoryInterface):
    """Concrete implementation of audit repository."""
    
    def __init__(self, database_session):
        self._session = database_session
    
    async def save(self, audit_log: AuditLog) -> AuditLog:
        """Save audit log entry."""
        # Implementation would depend on your database layer
        # This is a placeholder for the actual database operations
        query = """
            INSERT INTO audit_logs (
                id, action, user_id, resource_type, resource_id,
                details, status, created_at, updated_at, metadata,
                ip_address, user_agent, session_id, request_id,
                created_by, updated_by, deleted_by, deleted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        values = (
            str(audit_log.id),
            audit_log.action,
            audit_log.user_id,
            audit_log.resource_type,
            audit_log.resource_id,
            audit_log.details,
            audit_log.status.value,
            audit_log.created_at,
            audit_log.updated_at,
            audit_log.metadata,
            audit_log.ip_address,
            audit_log.user_agent,
            audit_log.session_id,
            audit_log.request_id,
            audit_log.created_by,
            audit_log.updated_by,
            audit_log.deleted_by,
            audit_log.deleted_at
        )
        
        await self._session.execute(query, values)
        await self._session.commit()
        return audit_log
    
    async def find_by_id(self, audit_id: UUID) -> Optional[AuditLog]:
        """Find audit log by ID."""
        query = "SELECT * FROM audit_logs WHERE id = ?"
        result = await self._session.execute(query, (str(audit_id),))
        row = await result.fetchone()
        return AuditLog.from_dict(dict(row)) if row else None
    
    async def find_by_user(self, user_id: str, limit: int = 100) -> List[AuditLog]:
        """Find audit logs by user ID."""
        query = "SELECT * FROM audit_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?"
        result = await self._session.execute(query, (user_id, limit))
        rows = await result.fetchall()
        return [AuditLog.from_dict(dict(row)) for row in rows]
    
    async def find_by_resource(self, resource_type: str, resource_id: str, limit: int = 100) -> List[AuditLog]:
        """Find audit logs by resource."""
        query = """
            SELECT * FROM audit_logs 
            WHERE resource_type = ? AND resource_id = ? 
            ORDER BY created_at DESC LIMIT ?
        """
        result = await self._session.execute(query, (resource_type, resource_id, limit))
        rows = await result.fetchall()
        return [AuditLog.from_dict(dict(row)) for row in rows]
    
    async def find_by_date_range(self, start_date: datetime, end_date: datetime, limit: int = 100) -> List[AuditLog]:
        """Find audit logs by date range."""
        query = """
            SELECT * FROM audit_logs 
            WHERE created_at BETWEEN ? AND ? 
            ORDER BY created_at DESC LIMIT ?
        """
        result = await self._session.execute(query, (start_date, end_date, limit))
        rows = await result.fetchall()
        return [AuditLog.from_dict(dict(row)) for row in rows]
    
    async def find_with_filters(self,
                              user_id: Optional[str] = None,
                              resource_type: Optional[str] = None,
                              resource_id: Optional[str] = None,
                              action: Optional[str] = None,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None,
                              status: Optional[Status] = None,
                              limit: int = 100,
                              offset: int = 0) -> List[AuditLog]:
        """Find audit logs with multiple filters."""
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if resource_type:
            query += " AND resource_type = ?"
            params.append(resource_type)
            
        if resource_id:
            query += " AND resource_id = ?"
            params.append(resource_id)
        
        if action:
            query += " AND action = ?"
            params.append(action)
        
        if start_date:
            query += " AND created_at >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND created_at <= ?"
            params.append(end_date)
            
        if status:
            query += " AND status = ?"
            params.append(status.value)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        result = await self._session.execute(query, params)
        rows = await result.fetchall()
        return [AuditLog.from_dict(dict(row)) for row in rows]
    
    async def count_by_filters(self,
                             user_id: Optional[str] = None,
                             resource_type: Optional[str] = None,
                             resource_id: Optional[str] = None,
                             action: Optional[str] = None,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None,
                             status: Optional[Status] = None) -> int:
        """Count audit logs with filters."""
        query = "SELECT COUNT(*) FROM audit_logs WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if resource_type:
            query += " AND resource_type = ?"
            params.append(resource_type)
            
        if resource_id:
            query += " AND resource_id = ?"
            params.append(resource_id)
        
        if action:
            query += " AND action = ?"
            params.append(action)
        
        if start_date:
            query += " AND created_at >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND created_at <= ?"
            params.append(end_date)
            
        if status:
            query += " AND status = ?"
            params.append(status.value)
        
        result = await self._session.execute(query, params)
        row = await result.fetchone()
        return row[0] if row else 0
    
    async def delete_old_logs(self, older_than: datetime) -> int:
        """Delete audit logs older than specified date."""
        query = "DELETE FROM audit_logs WHERE created_at < ?"
        result = await self._session.execute(query, (older_than,))
        await self._session.commit()
        return result.rowcount
