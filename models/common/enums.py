from enum import Enum

class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class StatusEnum(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class RoleType(Enum):
    ADMIN = "admin"
    OWNER = "owner"
    SELLER = "seller"
    BUYER = "buyer"
