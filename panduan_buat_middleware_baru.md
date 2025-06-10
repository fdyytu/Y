# Panduan Membuat Middleware Baru di fdyytu/Y

Panduan ini menjelaskan lokasi, dependency, dan struktur yang tepat untuk membuat middleware baru agar konsisten dengan struktur repo.

---

## 1. **Lokasi File Middleware**
Semua middleware ditempatkan di `middleware/` dan subfoldernya, sesuai jenis dan fungsinya:

- `middleware/authentication/`  
  - Untuk autentikasi (JWT, OAuth, API key, dsb)
- `middleware/authorization/`  
  - Untuk otorisasi (policies, RBAC, role manager, dsb)
- `middleware/core/`  
  - Base handler, abstract, registry, dsb
- `middleware/error/`  
  - Error formatter, exception handler, retry handler
- `middleware/logging/`  
  - Logger request/response, dsb
- `middleware/monitoring/`  
  - Alerting, metrics, tracing
- `middleware/integration/`  
  - Payment gateway, provider, dsb (untuk middleware integrasi eksternal)
- `middleware/performance/`  
  - Rate limiter, cache, dsb
- `middleware/localization/`  
  - Bahasa, timezone, dsb
- `middleware/security/`  
  - Anti-fraud, encryption, CORS, XSS, SSL, dsb
- `middleware/maintenance/`  
  - Maintenance mode, version check

Setiap subfolder punya struktur __init__.py dan file sesuai fungsinya.

---

## 2. **Dependency Internal**
Saat membuat middleware, biasanya:
- **Import base handler/class** dari:
  - `middleware/core/abstract/base_handler.py`
  - `middleware/core/abstract/base_middleware.py`
- **Interface/Registry** dari:
  - `middleware/core/interfaces/`
  - `middleware/core/registry/`
- **Decorator/helper** dari:
  - `middleware/utils/decorators/`
  - `middleware/utils/helpers/`
- **Logger** dari:
  - `middleware/logging/` jika butuh logging di middleware
- **Error handler** dari:
  - `middleware/error/exception_handler.py` dsb jika perlu custom error

---

## 3. **Dependency Eksternal**
- **Config/setting** dari:
  - `config/settings/middleware.py`, `config/constants/`
- **Database/session** jika middleware perlu validasi ke DB:
  - `config/database/connection.py`
- **Provider/integrasi eksternal** dari:
  - `config/providers/`, `middleware/integration/`
- **Validator/util** dari:
  - `config/utils/`, `schemas/validators/`

---

## 4. **Struktur File Middleware (Contoh)**
```python
# middleware/authentication/jwt_middleware.py

from middleware/core/abstract/base_middleware import BaseMiddleware
from config/settings/middleware import JWT_SECRET
from exceptions/auth/authentication import AuthenticationException
from models/auth/services.authorization_service import AuthorizationService

class JWTMiddleware(BaseMiddleware):
    def process_request(self, request):
        token = request.headers.get("Authorization")
        if not token or not AuthorizationService.verify_token(token, JWT_SECRET):
            raise AuthenticationException("Invalid or missing JWT token")
        return request
```

---

## 5. **Struktur Folder Dependency Middleware**
- `middleware/` (wajib; lokasi utama)
  - `authentication/`
  - `authorization/`
  - `core/`
  - `error/`
  - `logging/`
  - `monitoring/`
  - `integration/`
  - `performance/`
  - `localization/`
  - `security/`
  - `maintenance/`
  - `utils/`
- `config/settings/`, `config/constants/` (setting/konstanta)
- `config/database/` (jika perlu akses DB)
- `config/providers/` (jika perlu integrasi eksternal)
- `exceptions/` (untuk custom error)
- `models/auth/services/` (misal otorisasi, session, dsb)
- `schemas/validators/`, `config/utils/` (validator/helper)

---

## 6. **Tips**
- **Jangan letakkan file middleware di luar folder middleware/**
- **Gunakan base handler/class/interface dari core** agar konsisten dengan arsitektur repo
- **Pakai subfolder sesuai jenis** (auth, security, error, dsb)
- **Integrasikan dengan config/setting jika perlu customisasi**
- **Pakai dependency yang sudah ada, jangan duplikasi logic**

---

**Dengan mengikuti panduan ini, middleware yang kamu buat akan konsisten, reusable, dan mudah di-maintain sesuai standar repo.**