from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from uvicorn.config import Config
import datetime
import os
import logging
import sys
from setup import setup_project_structure
from watcher import watch_directory, WATCHED_DIRECTORIES
from reloader import AutoReloader

# Konfigurasi logging yang lebih lengkap
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Output ke console
        logging.FileHandler('server.log')   # Output ke file
    ]
)

# Buat logger khusus untuk server
logger = logging.getLogger('server')
logger.setLevel(logging.INFO)

# Inisialisasi FastAPI
app = FastAPI()

# Tambahkan CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Log saat server mulai"""
    logger.info("Server mulai berjalan")

@app.on_event("shutdown")
async def shutdown_event():
    """Log saat server berhenti"""
    logger.info("Server berhenti")

if __name__ == "__main__":
    # Setup struktur project
    if not setup_project_structure():
        logger.error("Gagal setup struktur project")
        exit(1)
    
    # Informasi startup
    current_time = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    current_user = os.getenv("USER", "fdyytu")
    
    startup_message = f"""
=== Server Status ===
📅 Waktu Start (UTC): {current_time}
👤 User: {current_user}

🔍 Monitoring Direktori:
{chr(10).join(f'   └── {dir_path}' for dir_path in WATCHED_DIRECTORIES)}

🚀 Server mulai dengan konfigurasi:
├── FastAPI: API utama dan endpoints
├── Django: Admin panel dan reporting
└── Flask: Payment gateway dan webhooks
"""
    
    # Log informasi startup
    logger.info(startup_message)
    print(startup_message)  # Tampilkan juga di console
    
    try:
        # Konfigurasi uvicorn dengan logging
        uvicorn_config = Config(
            "server:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=WATCHED_DIRECTORIES,
            log_level="info",
            log_config={
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "default": {
                        "()": "uvicorn.logging.DefaultFormatter",
                        "fmt": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                        "use_colors": True,
                    },
                },
                "handlers": {
                    "default": {
                        "formatter": "default",
                        "class": "logging.StreamHandler",
                        "stream": "ext://sys.stdout",
                    },
                },
                "loggers": {
                    "server": {"handlers": ["default"], "level": "INFO"},
                }
            }
        )
        
        # Inisialisasi AutoReloader
        reloader = AutoReloader(app)
        logger.info("AutoReloader diinisialisasi")
        
        # Setup dan jalankan file watcher
        watcher = Watcher(WATCHED_DIRECTORIES, reloader.reload_app)
        logger.info("File Watcher diinisialisasi")
        
        # Jalankan watcher di thread terpisah
        import threading
        watcher_thread = threading.Thread(target=watcher.start)
        watcher_thread.daemon = True
        watcher_thread.start()
        logger.info("File Watcher thread dimulai")
        
        # Log sebelum server mulai
        logger.info("Memulai server Uvicorn...")
        
        # Jalankan server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=True,
            reload_dirs=WATCHED_DIRECTORIES
        )
        
    except Exception as e:
        logger.error(f"Error saat menjalankan server: {str(e)}")
    except KeyboardInterrupt:
        logger.info("Server dihentikan oleh user")
        watcher.stop()