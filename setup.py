import os
import logging

logger = logging.getLogger(__name__)

def create_directory(path):
    """Membuat direktori jika belum ada"""
    try:
        if not os.path.exists(path):
            os.makedirs(path)
            logger.info(f"Direktori dibuat: {path}")
        return True
    except Exception as e:
        logger.error(f"Gagal membuat direktori {path}: {str(e)}")
        return False

def setup_project_structure():
    """Setup struktur folder project"""
    directories = [
        "./routes",
        "./models",
        "./services",
        "./config",
        "./utils",
        "./routes/v1",
        "./routes/v2",
        "./models/core",
        "./config/api",
        "./config/auth"
    ]
    
    success = True
    for directory in directories:
        if not create_directory(directory):
            success = False
    
    if success:
        logger.info("Setup struktur project berhasil")
    else:
        logger.warning("Beberapa direktori gagal dibuat")
    
    return success