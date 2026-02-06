"""
Detecção de arquivos DICOM sem extensão baseada em magic number
"""
from pathlib import Path
from typing import List, Optional
from loguru import logger


class DICOMFileDetector:
    """
    Detectar arquivos DICOM pelo magic number (DICM)
    
    Não depende de extensão de arquivo - busca pelo
    magic number DICOM em posição 128-132 (DICM)
    """
    
    DICOM_MAGIC_OFFSET = 128  # Posição onde está "DICM"
    DICOM_MAGIC = b'DICM'
    MIN_FILE_SIZE = 132  # 128 bytes offset + 4 bytes "DICM"
    
    @staticmethod
    def is_dicom_file(file_path: Path) -> bool:
        """
        Verificar se arquivo é DICOM pelo magic number
        
        Args:
            file_path: Caminho do arquivo
        
        Returns:
            True se é arquivo DICOM válido, False senão
        """
        try:
            file_path = Path(file_path)
            
            # Verificar tamanho mínimo
            if not file_path.exists() or file_path.is_dir():
                return False
            
            if file_path.stat().st_size < DICOMFileDetector.MIN_FILE_SIZE:
                return False
            
            # Verificar magic number
            with open(file_path, 'rb') as f:
                f.seek(DICOMFileDetector.DICOM_MAGIC_OFFSET)
                magic = f.read(4)
            
            return magic == DICOMFileDetector.DICOM_MAGIC
        
        except (OSError, IOError):
            return False
    
    @staticmethod
    def find_dicom_files(directory: Path) -> List[Path]:
        """
        Encontrar todos os arquivos DICOM em diretório
        (recursivo, sem dependência de extensão)
        
        Args:
            directory: Diretório para buscar
        
        Returns:
            Lista de caminhos de arquivos DICOM
        """
        dicom_files = []
        
        if not directory.is_dir():
            return dicom_files
        
        try:
            # Buscar todos os arquivos recursivamente
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    if DICOMFileDetector.is_dicom_file(file_path):
                        dicom_files.append(file_path)
                        logger.debug(f"DICOM encontrado: {file_path}")
        
        except Exception as e:
            logger.warning(f"Erro ao buscar arquivos DICOM em {directory}: {e}")
        
        return dicom_files
    
    @staticmethod
    def find_dicom_files_in_folder(
        directory: Path,
        max_files: Optional[int] = None
    ) -> List[Path]:
        """
        Encontrar arquivos DICOM com limite
        
        Args:
            directory: Diretório para buscar
            max_files: Máximo de arquivos (None = sem limite)
        
        Returns:
            Lista de caminhos de arquivos DICOM
        """
        dicom_files = []
        
        if not directory.is_dir():
            return dicom_files
        
        try:
            # Buscar arquivos até atingir limite
            for file_path in directory.rglob('*'):
                if max_files and len(dicom_files) >= max_files:
                    break
                
                if file_path.is_file():
                    if DICOMFileDetector.is_dicom_file(file_path):
                        dicom_files.append(file_path)
                        logger.debug(f"DICOM encontrado: {file_path}")
        
        except Exception as e:
            logger.warning(f"Erro ao buscar arquivos DICOM em {directory}: {e}")
        
        return dicom_files
