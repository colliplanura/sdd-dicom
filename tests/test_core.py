"""
Testes para módulo core
"""
import pytest
from pathlib import Path
import tempfile

# Importar módulos a testar
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import Config
from src.core.exceptions import (
    ConfigurationError,
    AuthenticationError,
    DIOMConversionError,
    ValidationError,
)


def test_config_paths_exist():
    """Testar se caminhos de configuração existem"""
    Config.ensure_paths()
    assert Config.TEMP_DIR.exists()
    assert Config.LOG_DIR.exists()


def test_config_values():
    """Testar valores de configuração"""
    assert Config.MAX_WORKERS_DOWNLOAD > 0
    assert Config.MAX_WORKERS_UPLOAD > 0
    assert Config.TIMEOUT_DOWNLOAD_SECONDS > 0
    assert Config.RATE_LIMIT_REQUESTS_PER_SECOND > 0


def test_exceptions_are_exceptions():
    """Testar se exceções são derivadas de Exception"""
    assert issubclass(ConfigurationError, Exception)
    assert issubclass(AuthenticationError, Exception)
    assert issubclass(DIOMConversionError, Exception)
    assert issubclass(ValidationError, Exception)
