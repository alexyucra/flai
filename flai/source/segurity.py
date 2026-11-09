"""
Configurações de segurança para o FLAI
"""
from pathlib import Path
import os

class SecurityManager:
    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.allowed_paths = set()
        
    def validate_path(self, path: str) -> bool:
        """Valida se um caminho está dentro do projeto"""
        try:
            abs_path = (self.project_root / path).resolve()
            return abs_path.is_relative_to(self.project_root)
        except:
            return False
    
    def sanitize_response(self, response: str) -> str:
        """Remove referências a caminhos não autorizados"""
        import re
        
        # Padrões a remover
        patterns = [
            r'/home/[^/\s]+',  # Home directories Linux
            r'C:\\Users\\[^\\\s]+',  # Home directories Windows
            r'/root/',  # Root Linux
            r'C:\\',  # Root Windows
            r'Documentos', r'Imagens', r'Downloads',  # Pastas pessoais
            r'em meus arquivos', r'no meu sistema',  # Referências pessoais
        ]
        
        for pattern in patterns:
            response = re.sub(pattern, '[ACESSO RESTRITO]', response, flags=re.IGNORECASE)
        
        return response
    
    def create_security_warning(self) -> str:
        """Cria aviso de segurança para o prompt"""
        return f"""
⚠️ **AVISO DE SEGURANÇA FLAI** ⚠️

Você está operando em modo restrito:
- Projeto: {self.project_root.name}
- Acesso limitado a: {self.project_root}
- Não pode referenciar arquivos externos
- Não pode executar comandos
- Todas as respostas devem ser específicas deste projeto

Violar estas regras resultará em término da sessão.
"""