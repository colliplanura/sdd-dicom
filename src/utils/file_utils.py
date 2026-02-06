"""
Utilitários para manipulação de arquivos
"""
import hashlib
from pathlib import Path
from typing import Optional
from loguru import logger


def calculate_checksum(file_path: Path, algorithm: str = 'md5') -> str:
    """
    Calcular checksum de arquivo
    
    Args:
        file_path: Caminho do arquivo
        algorithm: 'md5' ou 'sha256'
    
    Returns:
        Checksum em formato hexadecimal
    """
    try:
        if algorithm == 'md5':
            hasher = hashlib.md5()
        elif algorithm == 'sha256':
            hasher = hashlib.sha256()
        else:
            raise ValueError(f"Algoritmo desconhecido: {algorithm}")
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        
        return hasher.hexdigest()
    
    except Exception as e:
        logger.error(f"Erro ao calcular checksum: {e}")
        raise


def validate_checksum(
    file_path: Path,
    expected_checksum: str,
    algorithm: str = 'md5'
) -> bool:
    """
    Validar checksum de arquivo
    
    Args:
        file_path: Caminho do arquivo
        expected_checksum: Checksum esperado
        algorithm: 'md5' ou 'sha256'
    
    Returns:
        True se matches, False senão
    """
    actual = calculate_checksum(file_path, algorithm)
    
    if actual == expected_checksum:
        logger.debug(f"✓ Checksum validado: {file_path.name}")
        return True
    else:
        logger.error(
            f"Checksum mismatch: {actual} != {expected_checksum}"
        )
        return False


def get_file_size_mb(file_path: Path) -> float:
    """Obter tamanho de arquivo em MB"""
    return file_path.stat().st_size / (1024 * 1024)


def ensure_directory(path: Path) -> Path:
    """Garantir que diretório existe"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def clean_temp_directory(temp_dir: Path, max_age_hours: int = 24) -> int:
    """
    Limpar diretório temporário
    
    Args:
        temp_dir: Diretório a limpar
        max_age_hours: Remover arquivos mais antigos que isso
    
    Returns:
        Número de arquivos removidos
    """
    import time
    from pathlib import Path
    
    temp_dir = Path(temp_dir)
    if not temp_dir.exists():
        return 0
    
    removed = 0
    current_time = time.time()
    cutoff_time = current_time - (max_age_hours * 3600)
    
    try:
        for item in temp_dir.rglob('*'):
            if item.is_file() and item.stat().st_mtime < cutoff_time:
                item.unlink()
                removed += 1
                logger.debug(f"Removido: {item}")
    
    except Exception as e:
        logger.error(f"Erro ao limpar temp: {e}")
    
    return removed
