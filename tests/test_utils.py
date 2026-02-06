"""
Testes para módulo de utilidades
"""
import pytest
from pathlib import Path
import tempfile
import time

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.file_utils import (
    calculate_checksum,
    validate_checksum,
    get_file_size_mb,
)
from src.utils.retry import retry_with_backoff, CircuitBreaker


def test_calculate_checksum():
    """Testar cálculo de checksum"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        f.flush()
        
        checksum = calculate_checksum(Path(f.name))
        assert isinstance(checksum, str)
        assert len(checksum) == 32  # MD5
        
        # Limpar
        Path(f.name).unlink()


def test_retry_with_backoff():
    """Testar decorator retry"""
    call_count = 0
    
    @retry_with_backoff(max_retries=3)
    def failing_function():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("Test error")
        return "success"
    
    result = failing_function()
    assert result == "success"
    assert call_count == 2


def test_circuit_breaker():
    """Testar circuit breaker"""
    cb = CircuitBreaker(failure_threshold=2, timeout_seconds=1)
    
    def failing_func():
        raise Exception("Test")
    
    # Primeira falha
    with pytest.raises(Exception):
        cb.call(failing_func)
    
    # Segunda falha - circuit abre
    with pytest.raises(Exception):
        cb.call(failing_func)
    
    # Terceira tentativa - circuit está OPEN
    with pytest.raises(RuntimeError):
        cb.call(failing_func)
    
    # Aguardar timeout
    time.sleep(1.1)
    
    # Teste de reset (vai falhar, mas testa half-open)
    with pytest.raises(Exception):
        cb.call(failing_func)
