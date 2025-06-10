class InvoiceNumber:
    """Invoice number value object."""
    
    def __init__(self, number: str):
        if not number or not isinstance(number, str):
            raise ValueError("Invoice number must be a non-empty string")
        if len(number) < 3:
            raise ValueError("Invoice number must be at least 3 characters long")
        self._number = number.strip().upper()
    
    @property
    def number(self) -> str:
        return self._number
    
    def __str__(self) -> str:
        return self._number
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, InvoiceNumber):
            return False
        return self._number == other._number
    
    def __hash__(self) -> int:
        return hash(self._number)
