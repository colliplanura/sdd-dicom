"""
SDD-DICOM - Sistema Automático de Conversão DICOM para NIfTI
"""

__version__ = "1.0.0"
__author__ = "Instituto IDOR"

from .core import Config, setup_logging
from .google_drive import GoogleDriveClient
from .dicom import DIOMConverter, DIOMValidator
from .pipeline import BatchPipeline

__all__ = [
    'Config',
    'setup_logging',
    'GoogleDriveClient',
    'DIOMConverter',
    'DIOMValidator',
    'BatchPipeline',
]
