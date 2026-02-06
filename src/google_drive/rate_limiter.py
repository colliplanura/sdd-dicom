"""
Rate limiter para Google Drive API
"""
import time
from loguru import logger


class RateLimiter:
    """
    Controlar taxa de requisições para respeitar limites do Google Drive
    
    Limite: 5-10 requisições por segundo
    Estratégia: Token bucket simples
    """
    
    def __init__(self, requests_per_second: int = 5):
        """
        Inicializar rate limiter
        
        Args:
            requests_per_second: Requisições por segundo permitidas
        """
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0
    
    def wait(self) -> None:
        """Aguardar se necessário antes de fazer requisição"""
        elapsed = time.time() - self.last_request_time
        sleep_time = self.min_interval - elapsed
        
        if sleep_time > 0:
            logger.debug(f"Rate limiting: sleeping {sleep_time:.3f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def __enter__(self):
        """Context manager"""
        self.wait()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        pass
