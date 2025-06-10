from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from uvicorn.config import Config
import asyncio
import datetime
import os
import logging
from setup import setup_project_structure
from watcher import watch_directory, WATCHED_DIRECTORIES
from reloader import AutoReloader

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

async def start_file_watcher(reloader):
    """Menjalankan file watcher"""
    async for changes in watch_directory(WATCHED_DIRECTORIES):
        if reloader.should_reload():
            reloader.reload_app()

if __name__ == "__main__":
    # Setup struktur project
    if not setup_project_structure():
        logger.error("Gagal setup struktur project")
        exit(1)
    
    # Informasi startup
    current_time = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SS")
    current_user = os.getenv("USER", "fdyytu")
    
    print(f"\n=== Server Status ===")
    print(f"📅 Waktu Start (UTC): {current_time}")
    print(f"👤 User: {current_user}")
    print("\n🔍 Monitoring Direktori:")
    for dir_path in WATCHED_DIRECTORIES:
        print(f"   └── {dir_path}")
    
    print("\n🚀 Server mulai dengan konfigurasi:")
    print("├── FastAPI: API utama dan endpoints")
    print("├── Django: Admin panel dan reporting")
    print("└── Flask: Payment gateway dan webhooks")
    
    # Konfigurasi uvicorn
    config = Config(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=WATCHED_DIRECTORIES,
        log_level="info"
    )
    
    # Inisialisasi AutoReloader
    reloader = AutoReloader(app)
    server = uvicorn.Server(config)
    
    # Jalankan server dan file watcher
    async def run_server():
        await asyncio.gather(
            server.serve(),
            start_file_watcher(reloader)
        )
    
    # Jalankan dengan asyncio
    asyncio.run(run_server())