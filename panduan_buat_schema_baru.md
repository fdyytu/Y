# Panduan Membuat Schema Baru di fdyytu/Y

Panduan ini menjelaskan lokasi, dependency, dan struktur yang tepat untuk membuat schema baru agar konsisten dengan struktur repo.

---

## 1. **Lokasi File Schema**
Semua schema ditempatkan dan diorganisasi dalam folder `schemas/` dan subfoldernya:

- `schemas/requests/`  
  - Untuk schema permintaan/request (input API)
  - Subfolder per domain:  
    - `schemas/requests/auth/`, `schemas/requests/product/`, `schemas/requests/transaction/`, dll
    - Sub-subfolder jika perlu: misal `schemas/requests/ppob/bills/bpjs.py`

- `schemas/responses/`  
  - Untuk schema response/output API
  - Subfolder per domain:  
    - `schemas/responses/auth/`, `schemas/responses/product/`, dll

- `schemas/enums/`  
  - Enum global, status, payment, transaction, dll

- `schemas/base/`  
  - Skema dasar: `base_schema.py`, `pagination.py`, `response.py`

- `schemas/validators/`  
  - Validator khusus: `type_validator.py`, `security_validator.py`, `network_validator.py`, dll

- `schemas/` (root)  
  - `__init__.py`, struktur base, dan import global

---

## 2. **Dependency Internal schemas/**
Saat membuat schema, biasanya:
- **Import base schema/class** dari:
  - `schemas/base/base_schema.py`
  - `schemas/base/response.py`, `pagination.py`
- **Import enum** dari:
  - `schemas/enums/status.py`, `schemas/enums/payment.py`, dll
- **Import validator/helper** dari:
  - `schemas/validators/type_validator.py`, `security_validator.py`, dsb

---

## 3. **Dependency Eksternal**
- **Import model** dari `models/` jika ingin schema langsung serialisasi dari model.
- **Import constant/config** dari:
  - `config/constants/`, `config/constants/app/features.py`, `config/constants/status.py`
- **Import utility/helper** dari:
  - `config/utils/`, `config/utils/helpers.py`

---

## 4. **Struktur File Schema (Contoh)**
```python
# schemas/requests/transaction/invoice.py

from schemas/base.base_schema import BaseSchema
from schemas/enums.status import InvoiceStatusEnum
from schemas/validators.type_validator import validate_invoice_number

class InvoiceRequestSchema(BaseSchema):
    invoice_number: str
    status: InvoiceStatusEnum

    def validate(self):
        validate_invoice_number(self.invoice_number)
```

```python
# schemas/responses/transaction/invoice.py

from schemas/base.response import ResponseSchema
from schemas/enums.status import InvoiceStatusEnum

class InvoiceResponseSchema(ResponseSchema):
    invoice_id: str
    status: InvoiceStatusEnum
    created_at: str
```

---

## 5. **Struktur Folder Dependency Schema**
- `schemas/requests/` (schema request per fitur/domain)
- `schemas/responses/` (schema response per fitur/domain)
- `schemas/enums/` (enum global dan domain)
- `schemas/base/` (base schema, response, pagination)
- `schemas/validators/` (validator custom)
- (opsional) import model dari `models/`
- (opsional) import konstanta dari `config/constants/`
- (opsional) import helper dari `config/utils/`

---

## 6. **Tips**
- Ikuti struktur subfolder sesuai domain agar maintainable.
- Gunakan base schema, enum, dan validator yang sudah tersedia agar schema konsisten.
- Untuk validasi custom, gunakan file di `schemas/validators/` atau buat baru jika perlu.
- Jika schema sering dipakai lintas domain, simpan di `schemas/base/` atau `schemas/enums/`.

---

**Dengan mengikuti panduan ini, schema yang kamu buat akan konsisten, mudah di-maintain, dan memanfaatkan semua file/folder yang ada di struktur repo.**