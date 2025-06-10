"""Repository untuk Order domain."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from models.order.entities.order import Order
from models.order.value_objects.order_status import OrderStatus

class OrderRepository(ABC):
    """Abstract repository untuk Order."""
    
    @abstractmethod
    def save(self, order: Order) -> Order:
        """Simpan order."""
        pass
    
    @abstractmethod
    def find_by_id(self, order_id: UUID) -> Optional[Order]:
        """Cari order berdasarkan ID."""
        pass
    
    @abstractmethod
    def find_by_buyer_id(self, buyer_id: UUID) -> List[Order]:
        """Cari semua order dari buyer tertentu."""
        pass
    
    @abstractmethod
    def find_by_status(self, status: OrderStatus) -> List[Order]:
        """Cari order berdasarkan status."""
        pass
    
    @abstractmethod
    def delete(self, order_id: UUID) -> bool:
        """Hapus order."""
        pass

class InMemoryOrderRepository(OrderRepository):
    """Implementasi in-memory repository untuk testing."""
    
    def __init__(self):
        self._orders = {}
    
    def save(self, order: Order) -> Order:
        self._orders[order.id] = order
        return order
    
    def find_by_id(self, order_id: UUID) -> Optional[Order]:
        return self._orders.get(order_id)
    
    def find_by_buyer_id(self, buyer_id: UUID) -> List[Order]:
        return [order for order in self._orders.values() 
                if order._buyer_id == buyer_id]
    
    def find_by_status(self, status: OrderStatus) -> List[Order]:
        return [order for order in self._orders.values() 
                if order.status == status]
    
    def delete(self, order_id: UUID) -> bool:
        if order_id in self._orders:
            del self._orders[order_id]
            return True
        return False
