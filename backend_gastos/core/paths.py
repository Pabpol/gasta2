"""
Path configuration for the expense management backend.
Defines all file and directory paths used throughout the application.
"""
import os
from pathlib import Path

# Base directory - project root
BASE_DIR = Path(__file__).parent.parent

# Data directory (created at runtime)
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Main data files
PARQUET = DATA_DIR / "movimientos_normalizados.parquet"
EXCEL = BASE_DIR / "Presupuesto_Auto.xlsx"

# Configuration files
MERCHANT_MAP = BASE_DIR / "merchant_map.csv"
CONFIG_YAML = BASE_DIR / "config.yaml"

# ML model path
MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / "clf.joblib"

# Ensure directories exist
MODEL_DIR.mkdir(exist_ok=True)

# Environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def ensure_data_dir():
    """Ensure data directory exists"""
    DATA_DIR.mkdir(exist_ok=True)

def get_data_path(filename: str) -> Path:
    """Get path for a file in the data directory"""
    ensure_data_dir()
    return DATA_DIR / filename
