"""
Testes para módulo DICOM
"""
import pytest
from pathlib import Path
import tempfile

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dicom.validator import DIOMValidator
from src.core.exceptions import ValidationError


def test_validate_dicom_file_invalid():
    """Testar validação DICOM com arquivo inválido"""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"not a dicom file")
        f.flush()
        
        validator = DIOMValidator()
        is_valid = validator.validate_dicom_file(Path(f.name))
        assert is_valid is False
        
        # Limpar
        Path(f.name).unlink()


def test_validate_nifti_file_invalid():
    """Testar validação NIfTI com arquivo inválido"""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"not a nifti file")
        f.flush()
        
        validator = DIOMValidator()
        is_valid = validator.validate_nifti_file(Path(f.name))
        assert is_valid is False
        
        # Limpar
        Path(f.name).unlink()
