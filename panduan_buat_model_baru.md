# Panduan Membuat Model Baru di fdyytu/Y

Panduan ini menjelaskan langkah serta dependency apa saja yang dibutuhkan jika ingin membuat model baru di project ini.

---

## 1. **Lokasi File Model**
- Semua file model HARUS dibuat di dalam folder `models/` dan subfolder domain yang sesuai.
  - Contoh:  
    - `models/transaction/entities/invoice.py`
    - `models/product/domain/product.py`
    - `models/core/base_model.py`

---

## 2. **Dependency Internal models/**
Saat membuat model, biasanya perlu:
- Mengimpor **base class** dari:
  - `models/base.py` atau `models/core/base_model.py`
- Mengimpor **mixin** (opsional):
  - `models/core/mixins/audit_mixin.py`, `timestamp_mixin.py`, dll
- Menggunakan **enum** atau **value object** dari:
  - `models/common/enums.py`, `models/common/value_objects.py`
  - atau subfolder value_objects di domain terkait
- Relasi ke **entity/domain lain** di models/
  - Contoh: `models/transaction/entities/order.py`, `models/transaction/value_objects/invoice_number.py`

---

## 3. **Dependency Eksternal (di luar models/)**
Jika model butuh akses/koneksi database atau migrasi, biasanya perlu import dari:
- `config/database/connection.py` (setup dan session database)
- `config/database/settings.py`, `migrations.py`, dll (jika perlu)

---

## 4. **Langkah Membuat Model Baru**
1. **Tentukan domain** (misal transaksi, produk, dsb).
2. **Buat file model** di subfolder yang tepat, misal:  
   `models/transaction/entities/invoice.py`
3. **Gunakan base class/mixin/enums/value object** sesuai kebutuhan.
4. **Jika model butuh CRUD ke database,** import koneksi dari `config/database/connection.py`.
5. **Jika model butuh relasi ke model lain,** import model tersebut dari folder models/ terkait.

---

## 5. **Contoh Struktur File Model**
```python
# models/transaction/entities/invoice.py

from models/base import BaseModel
from models/core/mixins/audit_mixin import AuditMixin
from models/transaction/value_objects.invoice_number import InvoiceNumber
from models/common/enums import StatusEnum
from models/transaction/entities.order import Order
from config/database.connection import get_db_session  # Jika butuh akses DB

class Invoice(BaseModel, AuditMixin):
    def __init__(self, invoice_number: InvoiceNumber, order: Order, status: StatusEnum):
        self.invoice_number = invoice_number
        self.order = order
        self.status = status

    def save(self):
        session = get_db_session()
        session.add(self)
        session.commit()
```

---

## 6. **Struktur Folder Dependency Model**
- `models/base.py`
- `models/core/base_model.py`
- `models/core/mixins/`
- `models/common/enums.py`
- `models/common/value_objects.py`
- `models/[domain]/entities/`
- `models/[domain]/value_objects/`
- (Jika perlu CRUD) `config/database/connection.py`
- (Opsional) repository/unit_of_work di `models/[domain]/repositories/`

---

## 7. **Tips**
- Ikuti struktur folder domain agar konsisten.
- Untuk operasi database, **WAJIB** gunakan helper dari `config/database/`.
- Semua file model tetap harus berada di dalam folder `models/`.

---

**Dengan mengikuti panduan ini, model yang kamu buat akan sesuai standar dan mudah digunakan di seluruh aplikasi.**