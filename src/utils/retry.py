"""
Retry logic com exponential backoff
"""
import time
import random
from typing import Callable, Any, Optional, Type
from functools import wraps
from loguru import logger

from ..core.exceptions import SddDicomError


def retry_with_backoff(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,)
):
    """
    Decorator para retry com exponential backoff
    
    Args:
        max_retries: Número máximo de tentativas
        backoff_factor: Fator multiplicador (2^n * backoff_factor)
        jitter: Adicionar variação aleatória
        exceptions: Exceções que ativam retry
    
    Example:
        @retry_with_backoff(max_retries=3)
        def my_function():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries - 1:
                        logger.error(
                            f"Failed after {max_retries} attempts: {func.__name__}"
                        )
                        raise
                    
                    # Exponential backoff com jitter
                    wait_time = (backoff_factor ** attempt)
                    if jitter:
                        wait_time += random.uniform(0, 1)
                    
                    logger.warning(
                        f"Retry {attempt + 1}/{max_retries} "
                        f"(waiting {wait_time:.2f}s): {e}"
                    )
                    
                    time.sleep(wait_time)
        
        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit Breaker pattern para proteção
    
    Estados:
    - CLOSED: Normal, permitindo operações
    - OPEN: Bloqueando operações, aguardando timeout
    - HALF_OPEN: Testando se serviço está disponível
    """
    
    class State:
        CLOSED = "closed"
        OPEN = "open"
        HALF_OPEN = "half_open"
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        success_threshold: int = 2
    ):
        """
        Inicializar circuit breaker
        
        Args:
            failure_threshold: Falhas antes de abrir
            timeout_seconds: Tempo antes de tentar half-open
            success_threshold: Sucessos antes de fechar
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.success_threshold = success_threshold
        
        self.state = self.State.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Executar função através do circuit breaker
        
        Args:
            func: Função a executar
            *args, **kwargs: Argumentos da função
        
        Returns:
            Resultado da função
        
        Raises:
            RuntimeError: Se circuit breaker está OPEN
        """
        if self.state == self.State.OPEN:
            if self._should_attempt_reset():
                self.state = self.State.HALF_OPEN
                logger.info("Circuit breaker: HALF_OPEN (tentando reset)")
            else:
                raise RuntimeError("Circuit breaker está OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Registrar sucesso"""
        self.failure_count = 0
        
        if self.state == self.State.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = self.State.CLOSED
                self.success_count = 0
                logger.info("Circuit breaker: CLOSED")
    
    def _on_failure(self):
        """Registrar falha"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = self.State.OPEN
            logger.warning(f"Circuit breaker: OPEN (falhas: {self.failure_count})")
    
    def _should_attempt_reset(self) -> bool:
        """Verificar se deve tentar reset"""
        if not self.last_failure_time:
            return True
        
        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.timeout_seconds
