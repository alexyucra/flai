"""
Gerenciamento de event loops para execução assíncrona segura
"""
import asyncio
import threading
from typing import TypeVar, Any, Optional
import functools

T = TypeVar('T')


def get_or_create_eventloop() -> asyncio.AbstractEventLoop:
    """
    Obtém o event loop atual ou cria um novo se não existir
    
    Returns:
        Event loop válido
    """
    try:
        loop = asyncio.get_running_loop()
        return loop
    except RuntimeError:
        # Não há loop rodando
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Loop closed")
            return loop
        except (RuntimeError, RuntimeError):
            # Cria novo loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop


def run_async(coro, timeout: Optional[int] = None) -> Any:
    """
    Executa uma corrotina de forma segura a partir de código síncrono
    
    Args:
        coro: Corrotina ou função assíncrona
        timeout: Timeout em segundos (opcional)
    
    Returns:
        Resultado da corrotina
    
    Example:
        >>> result = run_async(my_async_function())
    """
    try:
        # Levanta RuntimeError se não há loop rodando
        asyncio.get_running_loop()
        
        # Se já há loop rodando, precisamos de uma nova thread
        # (situação rara no FLAI)
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result(timeout=timeout)
            
    except RuntimeError:
        # Sem loop rodando - podemos criar um novo
        return asyncio.run(coro)
    
    except Exception as e:
        raise RuntimeError(f"Erro na execução assíncrona: {e}") from e


class AsyncHelper:
    """Helper para gerenciamento de operações assíncronas"""
    
    def __init__(self):
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
    
    def start_background_loop(self):
        """Inicia event loop em thread separada (para operações longas)"""
        if self._running:
            return
        
        self._running = True
        
        def run_loop():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()
        
        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()
    
    def stop_background_loop(self):
        """Para event loop em background"""
        if not self._running or not self._loop:
            return
        
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._running = False
        
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        self._loop = None
    
    def run_coro(self, coro, timeout: Optional[int] = None) -> Any:
        """
        Executa corrotina no loop em background
        
        Args:
            coro: Corrotina a executar
            timeout: Timeout em segundos
        """
        if not self._running or not self._loop:
            self.start_background_loop()
        
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=timeout)


# Instância global para operações em background
background_helper = AsyncHelper()


def ensure_async(func):
    """
    Decorador que permite função síncrona ser chamada como assíncrona
    
    Example:
        @ensure_async
        def sync_function():
            return "result"
        
        # Agora pode ser awaitada
        result = await sync_function()
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Executa função síncrona em thread pool
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
    
    return wrapper