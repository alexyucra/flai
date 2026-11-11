"""
Registro central de componentes - Evita duplicação de instâncias
"""
from pathlib import Path
from typing import Dict, Any, Optional, TypeVar, Callable
import threading

T = TypeVar('T')

class ComponentRegistry:
    """
    Registro singleton de componentes
    
    Garante que cada componente seja instanciado apenas uma vez por projeto
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._components = {}
                    cls._instance._factories = {}
                    cls._instance._lock = threading.RLock()
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._components: Dict[str, Any] = {}
            self._factories: Dict[str, Callable] = {}
            self._component_lock = threading.RLock()
            self._initialized = True
    
    def register_factory(self, name: str, factory: Callable, overwrite: bool = False):
        """
        Registra uma fábrica para criar o componente sob demanda
        
        Args:
            name: Nome único do componente
            factory: Função que cria o componente
            overwrite: Se pode sobrescrever existente
        """
        with self._component_lock:
            if name in self._factories and not overwrite:
                raise KeyError(f"Fábrica já registrada: {name}")
            self._factories[name] = factory
    
    def get(self, name: str, project_path: Optional[Path] = None, **kwargs) -> Any:
        """
        Obtém um componente do registro
        
        Args:
            name: Nome do componente
            project_path: Caminho do projeto (para componentes específicos)
            **kwargs: Argumentos adicionais para fábrica
        
        Returns:
            Instância do componente
        """
        # Chave composta inclui project_path para componentes específicos do projeto
        key = f"{name}:{project_path}" if project_path else name
        
        with self._component_lock:
            if key not in self._components:
                factory = self._factories.get(name)
                if not factory:
                    raise KeyError(f"Nenhuma fábrica registrada para: {name}")
                
                # Cria nova instância
                instance = factory(project_path, **kwargs) if project_path else factory(**kwargs)
                self._components[key] = instance
            
            return self._components[key]
    
    def set(self, name: str, instance: Any, project_path: Optional[Path] = None):
        """
        Define uma instância diretamente no registro
        
        Args:
            name: Nome do componente
            instance: Instância a registrar
            project_path: Caminho do projeto (opcional)
        """
        key = f"{name}:{project_path}" if project_path else name
        
        with self._component_lock:
            self._components[key] = instance
    
    def has(self, name: str, project_path: Optional[Path] = None) -> bool:
        """Verifica se componente já está registrado"""
        key = f"{name}:{project_path}" if project_path else name
        with self._component_lock:
            return key in self._components
    
    def clear(self):
        """Limpa todos os componentes (útil para testes)"""
        with self._component_lock:
            self._components.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do registro"""
        with self._component_lock:
            return {
                'total_components': len(self._components),
                'registered_factories': len(self._factories),
                'component_names': list(set(k.split(':')[0] for k in self._components.keys()))
            }


# Instância global
_registry = ComponentRegistry()

def get_component(name: str, project_path: Optional[Path] = None, **kwargs) -> Any:
    """
    Atalho para obter componente do registro
    
    Example:
        >>> rag = get_component('rag', project_path)
        >>> agent_manager = get_component('agent_manager', project_path)
    """
    return _registry.get(name, project_path, **kwargs)


def register_component(name: str, factory: Callable, overwrite: bool = False):
    """
    Atalho para registrar fábrica de componente
    
    Example:
        >>> register_component('rag', lambda path: IntegratedRAG(path))
    """
    _registry.register_factory(name, factory, overwrite)


def has_component(name: str, project_path: Optional[Path] = None) -> bool:
    """Verifica se componente já foi instanciado"""
    return _registry.has(name, project_path)