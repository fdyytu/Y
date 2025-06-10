"""
Example usage of the audit system.

This file demonstrates how to properly use the audit logging system
following the established patterns and guidelines.
"""

import asyncio
from datetime import datetime
from uuid import uuid4
from models.audit import AuditLog, AuditService, AuditRepository
from models.common.enums import Status

# Mock database session for demonstration
class MockDatabaseSession:
    """Mock database session for example purposes."""
    
    def __init__(self):
        self.data = []
        self.last_id = 0
    
    async def execute(self, query, params=None):
        # Mock implementation
        if "INSERT" in query:
            self.last_id += 1
            return MockResult(self.last_id)
        elif "SELECT" in query:
            return MockResult(rows=self.data)
        elif "DELETE" in query:
            return MockResult(rowcount=len(self.data))
    
    async def commit(self):
        pass

class MockResult:
    def __init__(self, lastrowid=None, rows=None, rowcount=0):
        self.lastrowid = lastrowid
        self._rows = rows or []
        self.rowcount = rowcount
    
    async def fetchone(self):
        return self._rows[0] if self._rows else None
    
    async def fetchall(self):
        return self._rows

async def example_basic_audit_logging():
    """Example of basic audit logging."""
    print("=== Basic Audit Logging Example ===")
    
    # Setup
    db_session = MockDatabaseSession()
    audit_repo = AuditRepository(db_session)
    audit_service = AuditService(audit_repo)
    
    # Log a create action
    create_log = await audit_service.log_create_action(
        user_id="user123",
        resource_type="Product",
        resource_id="prod456",
        details="Created new product with name 'Laptop'",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0...",
        session_id="sess789",
        performed_by="user123"
    )
    
    print(f"Created audit log: {create_log.get_summary()}")
    print(f"Audit log ID: {create_log.id}")
    
    # Log an update action
    update_log = await audit_service.log_update_action(
        user_id="user123",
        resource_type="Product",
        resource_id="prod456",
        details="Updated product price from $1000 to $900",
        metadata={"old_price": 1000, "new_price": 900},
        performed_by="user123"
    )
    
    print(f"Updated audit log: {update_log.get_summary()}")
    
    # Log an access action
    access_log = await audit_service.log_access_action(
        user_id="user456",
        resource_type="Product",
        resource_id="prod456",
        details="Viewed product details",
        performed_by="user456"
    )
    
    print(f"Access audit log: {access_log.get_summary()}")

async def example_advanced_audit_features():
    """Example of advanced audit features."""
    print("\n=== Advanced Audit Features Example ===")
    
    # Setup
    db_session = MockDatabaseSession()
    audit_repo = AuditRepository(db_session)
    audit_service = AuditService(audit_repo)
    
    # Create an audit log with custom metadata
    audit_log = AuditLog(
        action="CUSTOM_ACTION",
        user_id="admin123",
        resource_type="System",
        resource_id="config001"
    )
    
    # Add custom metadata
    audit_log.add_metadata("config_key", "max_users")
    audit_log.add_metadata("old_value", 100)
    audit_log.add_metadata("new_value", 200)
    
    # Set request context
    audit_log.set_request_context(
        ip_address="10.0.0.1",
        user_agent="Admin Dashboard v2.0",
        session_id="admin_sess_001",
        request_id="req_12345"
    )
    
    # Log who performed the action
    audit_log.log_action("admin123")
    
    # Save the audit log
    saved_log = await audit_repo.save(audit_log)
    
    print(f"Custom audit log created: {saved_log.get_summary()}")
    print(f"Metadata: {saved_log.metadata}")
    print(f"Request context: IP={saved_log.ip_address}, Session={saved_log.session_id}")

async def example_audit_search_and_reporting():
    """Example of audit search and reporting features."""
    print("\n=== Audit Search and Reporting Example ===")
    
    # Setup
    db_session = MockDatabaseSession()
    audit_repo = AuditRepository(db_session)
    audit_service = AuditService(audit_repo)
    
    # Create some sample audit logs
    for i in range(5):
        await audit_service.log_action(
            action="VIEW" if i % 2 == 0 else "EDIT",
            user_id=f"user{i}",
            resource_type="Document",
            resource_id=f"doc{i}",
            details=f"Action {i} on document {i}",
            performed_by=f"user{i}"
        )
    
    # Search audit logs
    user_logs = await audit_service.get_user_audit_logs("user1", limit=10)
    print(f"Found {len(user_logs)} logs for user1")
    
    # Get audit summary
    summary = await audit_service.get_audit_summary("user1", days=30)
    print(f"Audit summary: {summary}")
    
    # Search with filters
    filtered_logs = await audit_service.search_audit_logs(
        resource_type="Document",
        action="VIEW",
        limit=10
    )
    print(f"Found {len(filtered_logs)} VIEW actions on Documents")

async def example_audit_mixin_usage():
    """Example of using audit functionality with domain models."""
    print("\n=== Audit Mixin Usage Example ===")
    
    from models.core.base_model import BaseModel
    from models.core.mixins.audit_mixin import AuditMixin
    
    class Product(BaseModel, AuditMixin):
        """Example product model with audit capabilities."""
        
        def __init__(self, name: str, price: float):
            super().__init__()
            self.name = name
            self.price = price
        
        def update_price(self, new_price: float, updated_by: str):
            """Update product price with audit trail."""
            old_price = self.price
            self.price = new_price
            self.set_updated_by(updated_by)
            
            return {
                'old_price': old_price,
                'new_price': new_price,
                'updated_by': updated_by,
                'updated_at': self.updated_at
            }
    
    # Create a product
    product = Product("Laptop", 1000.0)
    product.set_created_by("admin")
    
    print(f"Product created: {product.name} - ${product.price}")
    print(f"Audit info: {product.get_audit_info()}")
    
    # Update the product
    update_info = product.update_price(900.0, "manager")
    print(f"Product updated: {update_info}")
    print(f"Updated audit info: {product.get_audit_info()}")

async def main():
    """Run all examples."""
    print("Audit System Examples")
    print("=" * 50)
    
    await example_basic_audit_logging()
    await example_advanced_audit_features()
    await example_audit_search_and_reporting()
    await example_audit_mixin_usage()
    
    print("\n" + "=" * 50)
    print("All examples completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
