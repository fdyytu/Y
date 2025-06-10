import datetime
import logging
from watchfiles import watch

# Konfigurasi logging untuk watcher
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Direktori yang akan dipantau
WATCHED_DIRECTORIES = [
    "./routes",
    "./models",
    "./services",
    "./config",
    "./utils"
]

def log_file_change(changed_files):
    """Mencatat file yang berubah ke log"""
    for change_type, file_path in changed_files:
        logger.info(f"Terdeteksi perubahan: {change_type} - {file_path}")

async def watch_directory(directories):
    """Fungsi untuk memantau direktori"""
    try:
        async for changes in watch(*directories, recursive=True):
            log_file_change(changes)
            yield changes
    except Exception as e:
        logger.error(f"Error dalam pemantauan file: {str(e)}")