from enum import Enum

class Status(Enum):
    """Status umum untuk entity."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

# Alias untuk backward compatibility
StatusEnum = Status

class RoleType(Enum):
    """Tipe role user dalam sistem."""
    ADMIN = "admin"
    OWNER = "owner"
    SELLER = "seller"
    BUYER = "buyer"

class PaymentStatus(Enum):
    """Status pembayaran."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class TransactionType(Enum):
    """Tipe transaksi."""
    PURCHASE = "purchase"
    REFUND = "refund"
    TOPUP = "topup"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
