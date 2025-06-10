# models/transaction/entities/invoice.py

from models.base import Entity
from models.core.mixins.audit_mixin import AuditMixin
from models.transaction.value_objects.invoice_number import InvoiceNumber
from models.common.enums import StatusEnum
from models.transaction.entities.order import Order
from config.database.connection import get_db_session  # Jika butuh akses DB

class Invoice(Entity, AuditMixin):
    def __init__(self, invoice_number: InvoiceNumber, order: Order, status: StatusEnum):
        super().__init__()
        self.invoice_number = invoice_number
        self.order = order
        self.status = status

    def save(self):
        session = get_db_session()
        # Implementation for saving to database would go here
        # This is just a placeholder following the guide structure
        pass
