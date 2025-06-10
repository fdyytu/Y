from decimal import Decimal
from uuid import UUID
from models.base import Entity
from models.common.value_objects import Money

class OrderItem(Entity):
    """Item dalam order."""
    
    def __init__(
        self,
        product_id: UUID,
        product_name: str,
        price: Money,
        quantity: int,
        id: UUID = None
    ):
        super().__init__(id)
        self._product_id = product_id
        self._product_name = product_name
        self._price = price
        self._quantity = quantity
        
        if quantity <= 0:
            raise ValueError("Quantity harus lebih dari 0")
    
    @property
    def product_id(self) -> UUID:
        return self._product_id
    
    @property
    def product_name(self) -> str:
        return self._product_name
    
    @property
    def price(self) -> Money:
        return self._price
    
    @property
    def quantity(self) -> int:
        return self._quantity
    
    @property
    def subtotal(self) -> Money:
        """Hitung subtotal (price * quantity)."""
        return Money(
            self._price.amount * Decimal(self._quantity),
            self._price.currency
        )
    
    def update_quantity(self, new_quantity: int):
        """Update quantity item."""
        if new_quantity <= 0:
            raise ValueError("Quantity harus lebih dari 0")
        self._quantity = new_quantity
