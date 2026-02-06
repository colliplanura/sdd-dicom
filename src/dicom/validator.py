"""
Validação de arquivos DICOM e NIfTI
"""
from pathlib import Path
from typing import Tuple
from loguru import logger

from ..core.exceptions import ValidationError


class DIOMValidator:
    """Validar arquivos DICOM e NIfTI"""
    
    @staticmethod
    def validate_dicom_file(file_path: Path) -> bool:
        """
        Validar se arquivo é DICOM válido
        
        Verifica:
        - Magic number (128 bytes + "DICM")
        - Integridade do arquivo
        
        Args:
            file_path: Caminho do arquivo
        
        Returns:
            True se válido, False senão
        """
        try:
            file_path = Path(file_path)
            
            # Verificar tamanho mínimo
            if file_path.stat().st_size < 132:
                logger.warning(f"Arquivo muito pequeno: {file_path}")
                return False
            
            # Verificar magic number
            with open(file_path, 'rb') as f:
                # DICOM magic number está em 128 bytes
                f.seek(128)
                magic = f.read(4)
            
            is_valid = magic == b'DICM'
            
            if is_valid:
                logger.debug(f"✓ DICOM válido: {file_path.name}")
            else:
                logger.warning(f"Magic number inválido: {file_path.name}")
            
            return is_valid
        
        except Exception as e:
            logger.error(f"Erro validando DICOM: {e}")
            return False
    
    @staticmethod
    def validate_nifti_file(file_path: Path) -> bool:
        """
        Validar se arquivo é NIfTI válido
        
        Verifica:
        - Magic number "ni1" ou "n+1" para NIfTI-1
        - "n+2" para NIfTI-2
        - Tamanho mínimo
        
        Args:
            file_path: Caminho do arquivo .nii ou .nii.gz
        
        Returns:
            True se válido, False senão
        """
        try:
            file_path = Path(file_path)
            
            # Se é .gz, precisa descomprimir antes
            if file_path.suffix == '.gz':
                import gzip
                with gzip.open(file_path, 'rb') as f:
                    header = f.read(348)
            else:
                with open(file_path, 'rb') as f:
                    header = f.read(348)
            
            # NIfTI-1: 348 bytes header
            if len(header) < 348:
                logger.warning(f"Header muito pequeno: {file_path}")
                return False
            
            # Verificar magic number (bytes 344-347)
            magic = header[344:348]
            
            valid_magics = [b'ni1\0', b'n+1\0', b'n+2\0']
            is_valid = magic in valid_magics
            
            if is_valid:
                logger.debug(f"✓ NIfTI válido ({magic.decode('utf-8', errors='ignore')}): {file_path.name}")
            else:
                logger.warning(f"Magic number inválido: {file_path.name}")
            
            return is_valid
        
        except Exception as e:
            logger.error(f"Erro validando NIfTI: {e}")
            return False
    
    @staticmethod
    def validate_json_sidecar(file_path: Path) -> bool:
        """
        Validar se arquivo JSON é válido
        
        Args:
            file_path: Caminho do arquivo .json
        
        Returns:
            True se válido, False senão
        """
        try:
            import json
            with open(file_path, 'r') as f:
                json.load(f)
            logger.debug(f"✓ JSON válido: {file_path.name}")
            return True
        
        except Exception as e:
            logger.warning(f"JSON inválido: {e}")
            return False
