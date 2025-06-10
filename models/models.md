# Dokumentasi Struktur Models

Dokumentasi ini menjelaskan struktur dan organisasi models dalam aplikasi.

## Struktur Umum

```
models/
├── base.py                     # Base classes (Entity, AggregateRoot)
├── common/                     # Common models dan value objects
│   ├── __init__.py
│   ├── enums.py               # Enums umum (Status, RoleType, dll)
│   └── value_objects.py       # Value objects umum (Money, Email, dll)
├── core/                      # Core functionality
│   ├── __init__.py
│   ├── base_model.py          # Deprecated, gunakan models/base.py
│   └── mixins/                # Mixins untuk functionality tambahan
│       ├── __init__.py
│       ├── audit_mixin.py     # Audit trail functionality
│       ├── timestamp_mixin.py # Timestamp functionality
│       └── softdelete_mixin.py # Soft delete functionality
└── [domain]/                  # Domain-specific models
    ├── __init__.py
    ├── entities/              # Domain entities
    ├── value_objects/         # Domain value objects
    ├── repositories/          # Repository interfaces
    └── exceptions.py          # Domain exceptions
```

## Base Classes

### Entity
Base class untuk semua domain entities. Menyediakan:
- Unique identifier (UUID)
- Equality comparison berdasarkan ID
- Hash function untuk collections

### AggregateRoot
Extends Entity, digunakan untuk aggregate roots dalam DDD pattern. Menyediakan:
- Domain events management
- Semua functionality dari Entity

### BaseModel (Deprecated)
Alias untuk Entity, disediakan untuk backward compatibility.

## Mixins

### TimestampMixin
Menambahkan timestamp functionality:
- `created_at`: Waktu entity dibuat
- `updated_at`: Waktu terakhir diupdate
- `update_timestamp()`: Method untuk update timestamp

### AuditMixin
Extends TimestampMixin, menambahkan audit trail:
- `created_by`: User yang membuat
- `updated_by`: User yang mengupdate
- `deleted_by`: User yang menghapus (soft delete)
- `deleted_at`: Waktu dihapus
- `is_deleted`: Flag soft delete

### SoftDeleteMixin
Standalone soft delete functionality:
- `deleted_at`: Waktu dihapus
- `deleted_by`: User yang menghapus
- `is_deleted`: Flag soft delete
- `soft_delete()`: Method untuk soft delete
- `restore()`: Method untuk restore

## Common Models

### Enums
- `Status`: Status umum (ACTIVE, INACTIVE, PENDING, dll)
- `StatusEnum`: Alias untuk Status (backward compatibility)
- `RoleType`: Tipe role user (ADMIN, OWNER, SELLER, BUYER)
- `PaymentStatus`: Status pembayaran
- `TransactionType`: Tipe transaksi

### Value Objects
- `Money`: Monetary amounts dengan currency
- `Email`: Email addresses dengan validasi
- `PhoneNumber`: Phone numbers dengan validasi
- `Address`: Alamat lengkap

## Domain Structure

Setiap domain harus mengikuti struktur standar:

### entities/
Berisi domain entities yang merupakan core business objects.

### value_objects/
Berisi value objects yang spesifik untuk domain tersebut.

### repositories/
Berisi repository interfaces untuk data access.

### exceptions.py
Berisi custom exceptions untuk domain tersebut.

## Contoh Penggunaan

### Membuat Entity Sederhana
```python
from models.base import Entity
from models.core.mixins import TimestampMixin

class Product(Entity, TimestampMixin):
    def __init__(self, name: str, price: Money):
        super().__init__()
        self.name = name
        self.price = price
```

### Membuat Aggregate Root
```python
from models.base import AggregateRoot
from models.core.mixins import AuditMixin

class Order(AggregateRoot, AuditMixin):
    def __init__(self, buyer_id: UUID, items: List[OrderItem]):
        super().__init__()
        self.buyer_id = buyer_id
        self.items = items
        self.status = OrderStatus.CREATED
```

### Menggunakan Value Objects
```python
from models.common import Money, Email

# Membuat money object
price = Money(Decimal("100000"), "IDR")

# Membuat email object
email = Email("user@example.com")
```

## Best Practices

1. **Gunakan Entity untuk domain objects dengan identity**
2. **Gunakan AggregateRoot untuk aggregate roots**
3. **Gunakan Value Objects untuk data tanpa identity**
4. **Gunakan Mixins untuk cross-cutting concerns**
5. **Ikuti struktur domain yang konsisten**
6. **Buat custom exceptions untuk setiap domain**
7. **Gunakan repository pattern untuk data access**

## Migration dari Struktur Lama

Jika ada model yang masih menggunakan struktur lama:

1. Update import dari `models/core/base_model.py` ke `models/base.py`
2. Update import mixins dari individual files ke `models/core/mixins`
3. Pindahkan file dari `domain/` ke struktur `entities/`, `value_objects/`, `repositories/`
4. Update import paths sesuai struktur baru

## Dependency Management

### Internal Dependencies
- Base classes: `models/base.py`
- Mixins: `models/core/mixins/`
- Common models: `models/common/`
- Domain models: `models/[domain]/`

### External Dependencies
- Database: `config/database/connection.py`
- Migrations: `config/database/migrations.py`

Dengan mengikuti struktur ini, models akan lebih terorganisir, mudah dimaintain, dan mengikuti best practices dalam domain-driven design.
