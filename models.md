# Models Documentation

## Overview

Sistem models dalam aplikasi ini menggunakan Domain-Driven Design (DDD) pattern dengan struktur yang terorganisir untuk mendukung berbagai domain bisnis. Models dibagi menjadi beberapa kategori utama:

- **Base Models**: Foundation classes untuk semua entity
- **Core Models**: Models inti untuk user management, authentication, dan access control
- **Business Domain Models**: Models untuk domain bisnis seperti PPOB, transaction, order, payment
- **Supporting Models**: Models pendukung seperti audit, notification, logging, reporting

## Architecture Pattern

### 1. Entity & Aggregate Root Pattern

```python
from models.base import Entity, AggregateRoot
from uuid import UUID

# Basic Entity
class MyEntity(Entity):
    def __init__(self, name: str, id: UUID = None):
        super().__init__(id)
        self._name = name
    
    @property
    def name(self) -> str:
        return self._name

# Aggregate Root dengan Domain Events
class MyAggregate(AggregateRoot):
    def __init__(self, name: str, id: UUID = None):
        super().__init__(id)
        self._name = name
    
    def perform_action(self):
        # Business logic
        self.add_domain_event(SomethingHappenedEvent(self.id))
```

### 2. Value Objects Pattern

```python
from models.common.value_objects import Money, Email, PhoneNumber, Address
from decimal import Decimal

# Menggunakan value objects
email = Email("user@example.com")
phone = PhoneNumber("08123456789")
amount = Money(Decimal("100000"), "IDR")
address = Address(
    street="Jl. Sudirman No. 1",
    city="Jakarta",
    province="DKI Jakarta", 
    postal_code="10110"
)

print(phone.formatted)  # +628123456789
print(address.full_address)  # Alamat lengkap
```

### 3. Mixins Pattern

```python
from models.core.mixins.timestamp_mixin import TimestampMixin
from models.core.mixins.audit_mixin import AuditMixin
from models.core.mixins.softdelete_mixin import SoftDeleteMixin

class MyModel(Entity, TimestampMixin, AuditMixin, SoftDeleteMixin):
    def __init__(self, name: str, id: UUID = None):
        super().__init__(id)
        self._name = name
    
    def update_name(self, new_name: str, updated_by: str):
        self._name = new_name
        self.update_timestamp()
        self.set_updated_by(updated_by)
```

## Core Models

### 1. Base Models (`models/base.py`)

**Entity**: Base class untuk semua domain entities
```python
from models.base import Entity
from uuid import UUID

class Product(Entity):
    def __init__(self, name: str, price: Decimal, id: UUID = None):
        super().__init__(id)
        self._name = name
        self._price = price
```

**AggregateRoot**: Base class untuk aggregate roots
```python
from models.base import AggregateRoot

class Order(AggregateRoot):
    def __init__(self, buyer_id: UUID, id: UUID = None):
        super().__init__(id)
        self._buyer_id = buyer_id
        self._items = []
    
    def add_item(self, item):
        self._items.append(item)
        self.add_domain_event(ItemAddedEvent(self.id, item))
```

### 2. Common Models (`models/common/`)

**Enums**: Status dan konstanta umum
```python
from models.common.enums import Status, RoleType, PaymentStatus, TransactionType

# Penggunaan enums
user_status = Status.ACTIVE
user_role = RoleType.BUYER
payment_status = PaymentStatus.PENDING
transaction_type = TransactionType.PURCHASE
```

**Value Objects**: Objects immutable untuk data terstruktur
```python
from models.common.value_objects import Money, Email, PhoneNumber, Address
from decimal import Decimal

# Membuat value objects
price = Money(Decimal("50000"), "IDR")
customer_email = Email("customer@example.com")
customer_phone = PhoneNumber("08123456789")
shipping_address = Address(
    street="Jl. Merdeka No. 10",
    city="Bandung",
    province="Jawa Barat",
    postal_code="40111"
)
```

## Authentication & Authorization Models

### 1. Core Auth Models (`models/core/auth/`)

**Token Management**:
```python
from models.core.auth.token import Token, TokenType
from datetime import datetime, timedelta

# Membuat access token
access_token = Token(
    user_id=user.id,
    token_type=TokenType.ACCESS,
    expires_at=datetime.utcnow() + timedelta(hours=1)
)

# Membuat refresh token
refresh_token = Token(
    user_id=user.id,
    token_type=TokenType.REFRESH,
    expires_at=datetime.utcnow() + timedelta(days=30)
)
```

**Multi-Factor Authentication**:
```python
from models.core.auth.mfa import MFAMethod, MFAType

# Setup MFA
mfa = MFAMethod(
    user_id=user.id,
    mfa_type=MFAType.TOTP,
    secret_key="generated_secret"
)
mfa.enable()
```

### 2. User Management (`models/core/buyer/`, `models/core/seller/`)

**Buyer Model**:
```python
from models.core.buyer.buyer import Buyer
from models.core.buyer.buyer_profile import BuyerProfile
from models.common.value_objects import Email, PhoneNumber

# Membuat buyer
buyer = Buyer(
    name="John Doe",
    email=Email("john@example.com"),
    phone=PhoneNumber("08123456789")
)

# Update profile
profile = BuyerProfile(
    date_of_birth=date(1990, 1, 1),
    gender="M",
    occupation="Software Engineer"
)
buyer.update_profile(profile)
```

**Seller Model**:
```python
from models.core.seller.seller import Seller
from models.core.seller.seller_verification import SellerVerification

# Membuat seller
seller = Seller(
    business_name="Toko ABC",
    email=Email("seller@example.com"),
    phone=PhoneNumber("08123456789")
)

# Verifikasi seller
verification = SellerVerification(
    seller_id=seller.id,
    document_type="KTP",
    document_number="1234567890123456"
)
seller.submit_verification(verification)
```

## Business Domain Models

### 1. PPOB Models (`models/ppob/`)

**Product Management**:
```python
from models.ppob.product import PPOBProduct
from models.ppob.category import PPOBCategory
from models.ppob.provider import Provider

# Membuat kategori PPOB
category = PPOBCategory(
    name="Pulsa",
    description="Pulsa dan paket data"
)

# Membuat provider
provider = Provider(
    name="Telkomsel",
    code="TSEL",
    is_active=True
)

# Membuat produk PPOB
product = PPOBProduct(
    code="TSEL5",
    name="Telkomsel 5K",
    price=5500.0,
    provider_id=provider.id,
    category="PULSA",
    type="PREPAID"
)
```

**Transaction Processing**:
```python
from models.ppob.transaction.transaction import PPOBTransaction
from models.ppob.telco.entities.pulsa_transaction import PulsaTransaction

# Transaksi PPOB umum
transaction = PPOBTransaction(
    customer_id=customer.id,
    product_id=product.id,
    amount=Decimal("5500"),
    customer_number="08123456789"
)

# Transaksi pulsa spesifik
pulsa_transaction = PulsaTransaction(
    customer_id=customer.id,
    phone_number=PhoneNumber("08123456789"),
    amount=PulsaAmount(Decimal("5000")),
    provider=Provider.TELKOMSEL
)
```

### 2. Transaction Models (`models/transaction/`)

**Order Management**:
```python
from models.transaction.entities.order import Order
from models.transaction.entities.order_item import OrderItem

# Membuat order
order = Order(
    buyer_id=buyer.id,
    items=[]
)

# Menambah item ke order
item = OrderItem(
    product_id=product.id,
    quantity=2,
    unit_price=Decimal("25000")
)
order.add_item(item)
```

**Payment Processing**:
```python
from models.transaction.payment.entities.bank_transfer import BankTransfer
from models.transaction.payment.entities.ewallet import EWallet
from models.transaction.payment.value_objects.bank_account import BankAccount

# Payment via bank transfer
bank_account = BankAccount(
    bank_code="BCA",
    account_number="1234567890",
    account_name="John Doe"
)
bank_payment = BankTransfer(
    order_id=order.id,
    amount=order.total_amount,
    bank_account=bank_account
)

# Payment via e-wallet
ewallet_payment = EWallet(
    order_id=order.id,
    amount=order.total_amount,
    wallet_type="GOPAY",
    phone_number="08123456789"
)
```

### 3. Order Models (`models/order/`)

**Order Entity**:
```python
from models.order.entities.order import Order
from models.order.entities.order_item import OrderItem
from models.order.value_objects.order_status import OrderStatus

# Membuat order dengan items
items = [
    OrderItem(product_id=product1.id, quantity=2, price=Decimal("10000")),
    OrderItem(product_id=product2.id, quantity=1, price=Decimal("15000"))
]

order = Order(
    buyer_id=buyer.id,
    items=items
)

# Update status order
order.update_status(OrderStatus.CONFIRMED)
```

## Supporting Models

### 1. Audit Models (`models/audit/`)

**Audit Logging**:
```python
from models.audit.audit_log import AuditLog
from models.common.enums import Status

# Membuat audit log
audit = AuditLog(
    action="CREATE_USER",
    user_id="admin123",
    resource_type="User",
    resource_id=str(user.id),
    details="User created successfully"
)

# Set request context
audit.set_request_context(
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0...",
    session_id="sess_123",
    request_id="req_456"
)

# Add metadata
audit.add_metadata("user_role", "buyer")
audit.add_metadata("registration_source", "mobile_app")
```

### 2. Notification Models (`models/notification/`)

**Email Notifications**:
```python
from models.notification.email import EmailNotification
from models.notification.template import NotificationTemplate

# Membuat template email
template = NotificationTemplate(
    name="welcome_email",
    subject="Welcome to Our Platform",
    body="Hello {{name}}, welcome to our platform!"
)

# Membuat email notification
email = EmailNotification(
    recipient=Email("user@example.com"),
    template=template,
    variables={"name": "John Doe"}
)
```

**Push Notifications**:
```python
from models.notification.push import PushNotification

# Membuat push notification
push = PushNotification(
    user_id=user.id,
    title="Order Confirmed",
    message="Your order #12345 has been confirmed",
    data={"order_id": "12345", "type": "order_update"}
)
```

### 3. Logging Models (`models/logging/`)

**Activity Logging**:
```python
from models.logging.activity_log import ActivityLog

# Log aktivitas user
activity = ActivityLog(
    user_id=user.id,
    action="LOGIN",
    description="User logged in successfully",
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0..."
)
```

**Error Logging**:
```python
from models.logging.error_log import ErrorLog

# Log error
error = ErrorLog(
    error_type="ValidationError",
    message="Invalid email format",
    stack_trace=traceback.format_exc(),
    user_id=user.id if user else None,
    request_path="/api/users",
    request_method="POST"
)
```

### 4. Reporting Models (`models/report/`)

**Sales Analytics**:
```python
from models.report.analytics.sales_stat import SalesStat
from datetime import date

# Membuat laporan penjualan
sales_report = SalesStat(
    date=date.today(),
    total_sales=Decimal("1000000"),
    total_orders=50,
    total_customers=30
)
```

**Financial Reports**:
```python
from models.report.financial.revenue import Revenue
from models.report.financial.profit import Profit

# Laporan revenue
revenue = Revenue(
    period="2024-01",
    gross_revenue=Decimal("5000000"),
    net_revenue=Decimal("4500000"),
    refunds=Decimal("500000")
)

# Laporan profit
profit = Profit(
    period="2024-01",
    revenue=Decimal("4500000"),
    costs=Decimal("3000000"),
    gross_profit=Decimal("1500000")
)
```

## Repository Pattern

### Base Repository
```python
from models.core.repositories.base_repository import Repository
from typing import List, Optional
from uuid import UUID

class UserRepository(Repository[User]):
    async def get_by_id(self, id: UUID) -> Optional[User]:
        # Implementation
        pass
    
    async def save(self, user: User) -> User:
        # Implementation
        pass
    
    async def delete(self, id: UUID) -> bool:
        # Implementation
        pass
    
    async def find_by_email(self, email: str) -> Optional[User]:
        # Custom method
        pass
```

### Unit of Work Pattern
```python
from models.transaction.repositories.unit_of_work import UnitOfWork

async def create_order_with_payment(order_data, payment_data):
    async with UnitOfWork() as uow:
        # Create order
        order = Order(**order_data)
        await uow.orders.save(order)
        
        # Create payment
        payment = Payment(order_id=order.id, **payment_data)
        await uow.payments.save(payment)
        
        # Commit transaction
        await uow.commit()
```

## Event-Driven Architecture

### Domain Events
```python
from models.events.domain_event import DomainEvent

class OrderCreatedEvent(DomainEvent):
    def __init__(self, order_id: UUID, buyer_id: UUID):
        super().__init__(
            name="order.created",
            payload={
                "order_id": str(order_id),
                "buyer_id": str(buyer_id)
            }
        )

# Dalam aggregate
class Order(AggregateRoot):
    def create(self):
        # Business logic
        self.add_domain_event(OrderCreatedEvent(self.id, self.buyer_id))
```

## Best Practices

### 1. Model Creation
- Selalu gunakan Entity atau AggregateRoot sebagai base class
- Gunakan Value Objects untuk data yang immutable
- Implementasikan business logic di dalam entity, bukan di service layer

### 2. Data Validation
- Validasi data di constructor atau setter methods
- Gunakan Value Objects untuk validasi format data (email, phone, etc.)
- Raise exception untuk invalid data

### 3. Relationships
- Gunakan ID references antar entities, bukan object references
- Implementasikan lazy loading untuk relationships yang besar
- Gunakan Repository pattern untuk data access

### 4. Testing
```python
import pytest
from models.core.buyer.buyer import Buyer
from models.common.value_objects import Email, PhoneNumber

def test_buyer_creation():
    buyer = Buyer(
        name="Test User",
        email=Email("test@example.com"),
        phone=PhoneNumber("08123456789")
    )
    
    assert buyer.name == "Test User"
    assert buyer.email.value == "test@example.com"
    assert buyer.phone.formatted == "+628123456789"

def test_invalid_email():
    with pytest.raises(ValueError):
        Email("invalid-email")
```

## Migration Guide

### From Legacy Models
Jika menggunakan model lama, gunakan import compatibility:
```python
# Legacy import (deprecated)
from models.core.base_model import BaseModel

# New import (recommended)
from models.base import Entity, AggregateRoot
```

### Database Integration
```python
# SQLAlchemy integration example
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from models.base import Entity

Base = declarative_base()

class UserORM(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    
    def to_entity(self) -> User:
        return User(
            name=self.name,
            email=Email(self.email),
            id=UUID(self.id)
        )
    
    @classmethod
    def from_entity(cls, user: User) -> 'UserORM':
        return cls(
            id=str(user.id),
            name=user.name,
            email=user.email.value
        )
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Pastikan menggunakan absolute imports
2. **Circular Dependencies**: Gunakan TYPE_CHECKING untuk type hints
3. **Validation Errors**: Periksa format data input sesuai Value Object requirements

### Performance Tips

1. Gunakan lazy loading untuk relationships
2. Implement caching di repository layer
3. Batch operations untuk multiple entities
4. Gunakan async/await untuk I/O operations

---

Dokumentasi ini mencakup semua model yang tersedia dalam sistem. Untuk informasi lebih detail tentang model spesifik, lihat file source code di direktori `models/` yang sesuai.
