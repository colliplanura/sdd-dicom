"""
Configuração centralizada do projeto SDD-DICOM
"""
import os
from pathlib import Path
from typing import Optional

class Config:
    """Configuração do aplicativo"""
    
    # Google Drive
    GOOGLE_DRIVE_FOLDER = os.getenv(
        'GD_FOLDER', 
        'Medicina/Doutorado IDOR/Exames/DICOM'
    )
    GOOGLE_DRIVE_OUTPUT_FOLDER = os.getenv(
        'GD_OUTPUT_FOLDER',
        'Medicina/Doutorado IDOR/Exames/NifTI'
    )
    CREDENTIALS_PATH = Path(
        os.getenv('CREDENTIALS_PATH', './config/credentials.json')
    )
    TOKEN_PATH = Path(
        os.getenv('TOKEN_PATH', './config/token.json')
    )
    
    # Processamento
    MAX_WORKERS_DOWNLOAD = int(os.getenv('MAX_WORKERS_DL', 5))
    MAX_WORKERS_UPLOAD = int(os.getenv('MAX_WORKERS_UL', 3))
    MAX_WORKERS_PROCESS = int(os.getenv('MAX_WORKERS_PROC', os.cpu_count() - 2 or 2))
    
    # Timeouts
    TIMEOUT_DOWNLOAD_SECONDS = int(os.getenv('TIMEOUT_DL', 300))
    TIMEOUT_CONVERSION_SECONDS = int(os.getenv('TIMEOUT_CONV', 600))
    TIMEOUT_UPLOAD_SECONDS = int(os.getenv('TIMEOUT_UL', 300))
    
    # Rate limiting
    RATE_LIMIT_REQUESTS_PER_SECOND = int(os.getenv('RATE_LIMIT', 5))
    
    # Retry
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
    RETRY_BACKOFF_FACTOR = int(os.getenv('RETRY_BACKOFF', 2))
    
    # Diretórios
    TEMP_DIR = Path(os.getenv('TEMP_DIR', './temp'))
    LOG_DIR = Path(os.getenv('LOG_DIR', './logs'))
    
    # Cache
    CACHE_TTL_HOURS = int(os.getenv('CACHE_TTL', 24))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT_JSON = os.getenv('LOG_FORMAT_JSON', 'false').lower() == 'true'
    
    @classmethod
    def ensure_paths(cls) -> None:
        """Garantir que diretórios necessários existem"""
        cls.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate(cls) -> bool:
        """Validar configuração"""
        if not cls.CREDENTIALS_PATH.exists():
            raise FileNotFoundError(
                f"Credentials file not found: {cls.CREDENTIALS_PATH}"
            )
        return True


# Scopes Google Drive
GOOGLE_DRIVE_SCOPES = [
    'https://www.googleapis.com/auth/drive',
]

# Configurações de dcm2niix
DCM2NIIX_CONFIG = {
    'compress': True,  # Gerar .nii.gz
    'bids': True,      # Gerar JSON sidecars
    'single_file': True,
    'filename_template': '%p_%t_%s',  # patient_time_series
}
