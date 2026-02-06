"""
Setup de logging com loguru
"""
import sys
from pathlib import Path
from loguru import logger
from .config import Config


def setup_logging() -> None:
    """Configurar logging com loguru"""
    
    # Remover handler padrão
    logger.remove()
    
    # Console (colorido)
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> | <white>{message}</white>",
        level=Config.LOG_LEVEL,
        colorize=True
    )
    
    # Arquivo log geral
    log_file = Config.LOG_DIR / "app_{time:YYYY-MM-DD}.log"
    logger.add(
        str(log_file),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="500 MB",
        retention="30 days",
        compression="zip"
    )
    
    # Arquivo apenas erros
    error_log = Config.LOG_DIR / "errors_{time:YYYY-MM-DD}.log"
    logger.add(
        str(error_log),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} | {message}",
        level="ERROR",
        rotation="daily",
        retention="30 days"
    )
    
    logger.info("✓ Logging configurado")
