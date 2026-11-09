"""
Intent Parser - Transforma texto em intenção estruturada
"""
from .patterns import IntentPatterns
from .classifier import IntentClassifier 
from typing import Dict, Optional, List, Any, Tuple
from flai.core.types import IntentData, IntentType

class IntentParser:
    """Parser de intenções do usuário"""
    
    def __init__(self):
        self.patterns = IntentPatterns()
        self.classifier = IntentClassifier()  # NOVO: instancia o classifier
    
    # def parse(self, user_input: str) -> Dict[str, Any]:
    def parse(self, user_input: str) -> IntentData:
        """
        Parseia entrada do usuário e retorna intenção estruturada
        
        Args:
            user_input: Texto do usuário
        
        Returns:
            Dict com intent, entity, fields, confidence, original
        """
        # PRIMEIRO: Tenta com regex (mais preciso)
        intent, entity = self.patterns.match_intent(user_input)
        fields = self.patterns.extract_fields(user_input)
        
        if intent:
            # Regex encontrou match - usa resultado do regex
            if intent == "help":
                return {
                    "original": user_input,
                    "intent": "help",
                    "entity": entity,
                    "fields": fields,
                    "confidence": 1.0,
                    "method": "regex",
                    "user_query": user_input  # Importante: preserva para diagnóstico
                }
            else:
                return {
                    "original": user_input,
                    "intent": intent,
                    "entity": entity,
                    "fields": fields,
                    "confidence": self._calculate_confidence(bool(entity), bool(fields)),
                    "method": "regex"
                }
        
            # # Calcula confiança baseada em match e campos
            # base_confidence = 0.7
            # if fields:
            #     base_confidence = min(0.95, base_confidence + 0.15)
            # if entity and len(entity) > 2:
            #     base_confidence = min(0.95, base_confidence + 0.05)
            # result["confidence"] = base_confidence
            
            # return result
        
        # SEGUNDO: Fallback com classifier (keywords expandidas)
        classification = self.classifier.classify(user_input)
        return {
            "original": user_input,
            "intent": classification["intent"],
            "entity": classification.get("entity"),
            "fields": classification.get("fields", []),
            "confidence": classification.get("confidence", 0.0),
            "method": classification.get("method")
        }
    
    def _calculate_confidence(self, has_entity: bool, has_fields: bool) -> float:
        """Calcula confiança baseada em match"""
        base = 0.7
        if has_entity:
            base += 0.15
        if has_fields:
            base += 0.10
        return min(base, 0.95)

    def is_command(self, user_input: str) -> bool:
        """
        Verifica se é um comando reconhecido
        
        Agora verifica tanto regex quanto keywords expandidas
        """
        # Primeiro tenta regex
        intent, _ = self.patterns.match_intent(user_input)
        if intent:
            return True
        
        # Depois tenta classifier
        classification = self.classifier.classify(user_input)
        return classification["intent"] != "unknown"
    
    def get_help_text(self) -> str:
        """Retorna texto de ajuda formatado com todas as intenções disponíveis"""
        help_text = """
## 📋 Comandos disponíveis

### 🚀 CRUD
| Comando | Exemplo |
|---------|---------|
| Criar CRUD | `criar crud de produtos`, `fazer crud de usuarios` |
| CRUD com campos | `criar crud de usuarios com nome, email, idade` |

### 📝 Formulários
| Comando | Exemplo |
|---------|---------|
| Criar formulário | `criar form login`, `fazer formulario de contato` |
| Form com campos | `criar formulario com nome, email, telefone` |

### 📄 Páginas
| Comando | Exemplo |
|---------|---------|
| Criar página | `criar pagina dashboard`, `nova tela de configuracoes` |
| Página com rota | `criar pagina perfil com rota /user/profile` |

### 🗄️ Modelos e Banco de Dados
| Comando | Exemplo |
|---------|---------|
| Criar model | `criar model produto`, `novo modelo de usuario` |
| Criar tabela | `criar tabela clientes` |

### 🔍 Análise e Busca
| Comando | Exemplo |
|---------|---------|
| Analisar componente | `analise o controller user`, `mostre a model produto` |
| Buscar no projeto | `onde esta o arquivo de configuracao?`, `cadê a funcao login?` |
| Refatorar código | `refatorar o service auth`, `melhorar este componente` |

### 🧪 Testes
| Comando | Exemplo |
|---------|---------|
| Criar testes | `criar testes para o crud`, `fazer teste unitario do model` |

### 🚀 Deploy
| Comando | Exemplo |
|---------|---------|
| Publicar app | `fazer deploy da aplicacao`, `subir para producao` |

### 📦 Dependências
| Comando | Exemplo |
|---------|---------|
| Gerenciar pacotes | `instalar requests`, `adicionar dependencia flet` |

### 🐛 Debug
| Comando | Exemplo |
|---------|---------|
| Depurar | `debugar este erro`, `ajuda a corrigir o bug` |

### ⚡ Performance
| Comando | Exemplo |
|---------|---------|
| Otimizar | `melhorar performance`, `deixar mais rapido` |

### 🛠️ Sistema
| Comando | Exemplo |
|---------|---------|
| Ajuda | `ajuda`, `help`, `?`, `o que voce faz` |
| Sair | `sair`, `exit`, `quit`, `fechar` |

---
💡 **Dicas:**
- Você pode especificar campos usando "com", "com os campos:" ou "contendo"
- Aceita comandos em português e inglês
- Erros de digitação pequenos são tolerados
"""
        return help_text

    def get_command_suggestions(self, user_input: str, limit: int = 3) -> List[Dict]:
        """
        NOVO: Sugere comandos similares quando o usuário digita algo não reconhecido
        
        Args:
            user_input: Texto do usuário
            limit: Número máximo de sugestões
        
        Returns:
            Lista de sugestões com intenção e confiança
        """
        if self.is_command(user_input):
            return []
        
        suggestions = self.classifier.suggest_intents(user_input, limit)
        
        return [
            {
                "intent": intent,
                "confidence": confidence,
                "description": self.classifier.get_intent_description(intent),
                "example": self._get_example_for_intent(intent)
            }
            for intent, confidence in suggestions
        ]
    
    def _get_example_for_intent(self, intent: str) -> str:
        """Retorna um exemplo de comando para determinada intenção"""
        examples = {
            "create_crud": "criar crud de produtos",
            "create_form": "criar form de login",
            "create_page": "criar pagina dashboard",
            "create_model": "criar model usuario",
            "create_test": "criar testes para o crud",
            "analyze": "analise o controller user",
            "where": "onde esta o arquivo de configuracao?",
            "refactor": "refatorar o service auth",
            "deploy": "fazer deploy da aplicacao",
            "dependencies": "instalar requests",
            "debug": "debugar este erro",
            "performance": "melhorar performance",
            "help": "ajuda",
            "exit": "sair"
        }
        return examples.get(intent, "comando disponivel")