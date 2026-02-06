"""
Testes para módulo Google Drive
"""
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.google_drive.rate_limiter import RateLimiter


def test_rate_limiter_initialization():
    """Testar inicialização do rate limiter"""
    limiter = RateLimiter(requests_per_second=5)
    assert limiter.requests_per_second == 5
    assert limiter.min_interval == 0.2  # 1/5


def test_rate_limiter_context_manager():
    """Testar rate limiter como context manager"""
    limiter = RateLimiter(requests_per_second=10)
    
    with limiter:
        pass
    
    # Não deve gerar erro
    assert True
