"""
Decoradores para tratamento consistente de erros
"""
import functools
import time
import logging
from typing import Callable, Any, Optional, Type, Tuple
from flai.core.logging import get_logger

def handle_errors(
    default_return: Any = None,
    log_errors: bool = True,
    reraise: bool = False,
    error_types: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorador para tratamento padrão de erros
    
    Args:
        default_return: Valor retornado em caso de erro
        log_errors: Se deve logar o erro
        reraise: Se deve relançar a exceção
        error_types: Tipos de erro a capturar
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            
            try:
                return func(*args, **kwargs)
            except error_types as e:
                if log_errors:
                    logger.error(
                        f"Erro em {func.__name__}: {str(e)}",
                        exc_info=True
                    )
                
                if reraise:
                    raise
                
                return default_return
        
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            
            try:
                return await func(*args, **kwargs)
            except error_types as e:
                if log_errors:
                    logger.error(
                        f"Erro em {func.__name__}: {str(e)}",
                        exc_info=True
                    )
                
                if reraise:
                    raise
                
                return default_return
        
        if functools.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    
    return decorator


def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorador para retry automático em caso de falha
    
    Args:
        max_attempts: Número máximo de tentativas
        delay: Delay inicial entre tentativas
        backoff: Fator de multiplicação do delay
        exceptions: Exceções que disparam retry
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"Falha após {max_attempts} tentativas em {func.__name__}: {e}",
                            exc_info=True
                        )
                        raise
                    
                    logger.warning(
                        f"Tentativa {attempt + 1}/{max_attempts} falhou em {func.__name__}: {e}. "
                        f"Re-tentando em {current_delay}s..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            return None  # não deve chegar aqui
        
        return wrapper
    
    return decorator