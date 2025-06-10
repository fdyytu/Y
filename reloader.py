import datetime
import sys
import logging
from importlib import reload
from watcher import WATCHED_DIRECTORIES

logger = logging.getLogger(__name__)

class AutoReloader:
    def __init__(self, app):
        self.app = app
        self.last_reload = datetime.datetime.utcnow()
        
    def should_reload(self):
        """Cek apakah perlu reload (minimal jeda 2 detik)"""
        current_time = datetime.datetime.utcnow()
        return (current_time - self.last_reload).total_seconds() > 2

    def reload_app(self):
        """Melakukan reload aplikasi"""
        logger.info(f"[{datetime.datetime.utcnow()}] Memulai reload aplikasi...")
        try:
            # Reload modul-modul yang berubah
            for module in list(sys.modules.keys()):
                if any(module.startswith(dir_name) for dir_name in WATCHED_DIRECTORIES):
                    try:
                        reload(sys.modules[module])
                        logger.info(f"Berhasil reload modul: {module}")
                    except:
                        pass
            self.last_reload = datetime.datetime.utcnow()
            logger.info("Reload aplikasi selesai")
        except Exception as e:
            logger.error(f"Error saat reload: {str(e)}")