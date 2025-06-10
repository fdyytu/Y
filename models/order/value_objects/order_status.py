from enum import Enum

class OrderStatus(Enum):
    """Status order dalam sistem."""
    
    CREATED = "created"
    CONFIRMED = "confirmed"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    
    def __str__(self):
        return self.value
    
    @classmethod
    def get_active_statuses(cls):
        """Dapatkan status yang masih aktif (belum selesai/dibatalkan)."""
        return [
            cls.CREATED,
            cls.CONFIRMED,
            cls.PAID,
            cls.PROCESSING,
            cls.SHIPPED,
            cls.DELIVERED
        ]
    
    @classmethod
    def get_final_statuses(cls):
        """Dapatkan status final (sudah selesai)."""
        return [
            cls.COMPLETED,
            cls.CANCELLED,
            cls.REFUNDED
        ]
    
    def is_active(self) -> bool:
        """Apakah status masih aktif."""
        return self in self.get_active_statuses()
    
    def is_final(self) -> bool:
        """Apakah status sudah final."""
        return self in self.get_final_statuses()
