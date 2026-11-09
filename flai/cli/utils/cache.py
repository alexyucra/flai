# flai/cli/utils/cache.py
"""
Sistema de cache thread-safe para evitar verificações repetidas
"""
import time
import threading
from pathlib import Path 
from typing import Any, Optional, Dict
from flai.core.platform import get_user_cache_dir

class FlaiCache:
    """Cache thread-safe com TTL"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._cache = {}
                    cls._instance._cache_dir = get_user_cache_dir() / "cache"
                    cls._instance._cache_dir.mkdir(parents=True, exist_ok=True)
                    cls._instance._cache_lock = threading.RLock()
        return cls._instance

    def _get_cache_file(self, key: str) -> Path:
        """Retorna caminho do arquivo de cache"""
        import hashlib
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return self._cache_dir / f"{safe_key}.json"
    
    def persist(self, key: str):
        """Persiste cache em disco (cross-platform)"""
        with self._cache_lock:
            if key in self._cache:
                cache_file = self._get_cache_file(key)
                import json
                cache_file.write_text(json.dumps({
                    'value': self._cache[key]['value'],
                    'expires': self._cache[key]['expires']
                }))

    def load_persisted(self, key: str):
        """Carrega cache persistido"""
        cache_file = self._get_cache_file(key)
        if cache_file.exists():
            import json
            data = json.loads(cache_file.read_text())
            if time.time() < data['expires']:
                self._cache[key] = {
                    'value': data['value'],
                    'expires': data['expires']
                }
                return data['value']
        return None

    def __init__(self):
        # Inicialização já feita no __new__
        if not hasattr(self, '_initialized'):
            self._cache: Dict[str, Dict] = {}
            self._cache_lock = threading.RLock()
            self._initialized = True
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """
        Armazena valor com tempo de vida
        
        Args:
            key: Chave do cache
            value: Valor a armazenar
            ttl: Tempo de vida em segundos (padrão 300)
        """
        with self._cache_lock:
            self._cache[key] = {
                'value': value,
                'expires': time.time() + ttl,
                'created_at': time.time()
            }
    
    def get(self, key: str, default: Any = None) -> Optional[Any]:
        """
        Obtém valor se não expirou
        
        Args:
            key: Chave do cache
            default: Valor padrão se não encontrado
        """
        with self._cache_lock:
            if key in self._cache:
                entry = self._cache[key]
                if time.time() < entry['expires']:
                    return entry['value']
                else:
                    # Remove expirado
                    del self._cache[key]
            return default
    
    def get_or_set(self, key: str, factory, ttl: int = 300) -> Any:
        """
        Obtém do cache ou cria se não existir (atomicamente)
        
        Args:
            key: Chave do cache
            factory: Função que gera o valor se não existir
            ttl: Tempo de vida em segundos
        """
        with self._cache_lock:
            value = self.get(key)
            if value is None:
                value = factory()
                self.set(key, value, ttl)
            return value
    
    def delete(self, key: str) -> bool:
        """Remove uma chave do cache"""
        with self._cache_lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self):
        """Limpa todo o cache"""
        with self._cache_lock:
            self._cache.clear()
    
    def has(self, key: str) -> bool:
        """Verifica se chave existe e não expirou"""
        with self._cache_lock:
            if key in self._cache:
                return time.time() < self._cache[key]['expires']
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        with self._cache_lock:
            active = len([k for k, v in self._cache.items() 
                         if time.time() < v['expires']])
            expired = len([k for k, v in self._cache.items() 
                          if time.time() >= v['expires']])
            return {
                'total_entries': len(self._cache),
                'active_entries': active,
                'expired_entries': expired,
                'keys': list(self._cache.keys())
            }
    
    def cleanup_expired(self):
        """Remove entradas expiradas (pode chamar periodicamente)"""
        with self._cache_lock:
            expired_keys = [k for k, v in self._cache.items() 
                           if time.time() >= v['expires']]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)

# Instância global
cache = FlaiCache()

import atexit
import threading

class CacheAutoCleanup:
    """Thread para limpeza automática do cache"""
    
    def __init__(self, interval: int = 300):
        self.interval = interval
        self._stop_event = threading.Event()
        self._thread = None
        self._running = False
    
    def start(self):
        """Inicia thread de limpeza"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Para thread de limpeza"""
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
    
    def _run(self):
        """Loop de limpeza"""
        while self._running:
            self._stop_event.wait(self.interval)
            if self._running:
                cleaned = cache.cleanup_expired()
                if cleaned > 0:
                    import logging
                    logging.debug(f"Cache cleanup: removed {cleaned} expired entries")

# Iniciar cleanup automático
_auto_cleanup = CacheAutoCleanup(interval=300)
_auto_cleanup.start()
atexit.register(lambda: _auto_cleanup.stop())