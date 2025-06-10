"""Exceptions untuk domain order."""

class OrderException(Exception):
    """Base exception untuk order domain."""
    pass

class InvalidOrderState(OrderException):
    """Exception ketika operasi tidak valid untuk status order saat ini."""
    pass

class OrderNotFound(OrderException):
    """Exception ketika order tidak ditemukan."""
    pass

class InvalidOrderItem(OrderException):
    """Exception ketika order item tidak valid."""
    pass

class InsufficientStock(OrderException):
    """Exception ketika stock tidak mencukupi."""
    pass

class OrderAlreadyPaid(OrderException):
    """Exception ketika order sudah dibayar."""
    pass

class OrderCancellationNotAllowed(OrderException):
    """Exception ketika order tidak bisa dibatalkan."""
    pass
