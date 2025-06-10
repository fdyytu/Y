# models/transaction/entities/invoice.py

from models.base import Entity
from models.core.mixins import AuditMixin
from models.transaction.value_objects.invoice_number import InvoiceNumber
from models.common.enums import StatusEnum
from models.order.entities.order import Order
from config.database.connection import get_db_session  # Jika butuh akses DB

class Invoice(Entity, AuditMixin):
    """Invoice entity untuk transaksi."""
    
    def __init__(self, invoice_number: InvoiceNumber, order: Order, status: StatusEnum = StatusEnum.PENDING):
        super().__init__()
        self.invoice_number = invoice_number
        self.order = order
        self.status = status

    def save(self):
        """Simpan invoice ke database."""
        session = get_db_session()
        # Implementation for saving to database would go here
        # This is just a placeholder following the guide structure
        pass
    
    def mark_as_paid(self):
        """Tandai invoice sebagai sudah dibayar."""
        self.status = StatusEnum.COMPLETED
    
    def cancel(self):
        """Batalkan invoice."""
        self.status = StatusEnum.CANCELLED
