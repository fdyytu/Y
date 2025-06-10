# Panduan Membuat Service Baru di fdyytu/Y

Panduan ini menjelaskan langkah dan dependency apa saja yang dibutuhkan saat membuat service baru di project ini.

---

## 1. **Lokasi File Service**
- Semua file service sebaiknya dibuat di:
  - `services/` (misal: `services/transaction.py`, `services/product.py`)
  - atau, jika service sangat spesifik/domain driven:
    - subfolder `config/services/` (misal: `config/services/rate_limiter.py`, `config/services/cache.py`)
- Untuk service sangat modular, bisa juga di dalam subfolder domain, tetapi **services/** dan **config/services/** adalah lokasi utama di repo ini.

---

## 2. **Dependency Internal**
Saat membuat service, biasanya:
- **Import model** dari folder `models/`  
  Contoh:  
  - `from models/transaction/entities/invoice import Invoice`
- **Import repository/unit of work** jika pakai pattern itu  
  Contoh:  
  - `from models/transaction/repositories/repository import TransactionRepository`
- **Import exception** dari folder `exceptions/` (error handling)
  - Contoh: `from exceptions/business/transaction/payment import PaymentException`
- **Import helper/util** jika perlu, dari:
  - `config/utils/`
  - `schemas/validators/`
  - dsb

---

## 3. **Dependency Eksternal**
Jika service perlu akses database, message broker, dsb:
- **Database:**  
  - Import koneksi/session dari `config/database/connection.py`
- **Queue/Message broker:**  
  - Import dari `config/queue/` (misal: `config/queue/rabbitmq.py`)
- **Cache:**  
  - Import dari `config/cache/` (misal: `config/cache/redis_cache.py`)
- **Provider/integrasi eksternal:**  
  - Import dari `config/providers/` atau `middleware/integration/`

---

## 4. **Struktur Service Umum**
```python
# services/transaction.py

from models/transaction/entities.invoice import Invoice
from config/database.connection import get_db_session
from exceptions/business/transaction.payment import PaymentException

class TransactionService:
    def create_invoice(self, data):
        session = get_db_session()
        try:
            invoice = Invoice(**data)
            session.add(invoice)
            session.commit()
            return invoice
        except Exception as e:
            session.rollback()
            raise PaymentException(str(e))
```

---

## 5. **Struktur Folder Dependency Service**
- `services/` atau `config/services/` (letak file service)
- `models/[domain]/` (import model)
- `models/[domain]/repositories/` (import repository/unit of work)
- `exceptions/` (error handling)
- `config/database/` (akses DB)
- `config/queue/` (opsional, untuk messaging)
- `config/cache/` (opsional, untuk cache)
- `config/providers/` (opsional, untuk integrasi)
- `config/utils/`, `schemas/validators/` (opsional, untuk utilitas/validasi tambahan)

---

## 6. **Tips**
- Simpan logic bisnis utama di service, jangan di route.
- Service yang CRUD data biasanya akan import model dan akses database.
- Untuk service yang butuh eksternal (API, payment, dsb), gunakan provider yang sudah ada di repo.

---

**Dengan mengikuti panduan ini, service yang kamu buat akan konsisten dan mudah di-maintain.**