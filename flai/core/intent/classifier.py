"""
Intent Classifier - Classificador de intenções (puro, sem LangChain)
"""
import re
from unidecode import unidecode
from typing import Dict, List, Tuple
from .patterns import IntentPatterns
from .flet_intents import FLET_DEVELOPER_INTENTS

class IntentClassifier:
    """Classificador simples de intenções baseado em padrões e keywords"""
    
    def __init__(self):
        self.patterns = IntentPatterns()

        self.keywords = FLET_DEVELOPER_INTENTS
    
    def _normalize(self, text: str) -> str:
        """Normaliza texto para melhor matching"""
        try:
            from unidecode import unidecode
            text = unidecode(text)
        except ImportError:
            # Fallback simples se unidecode não estiver instalado
            replacements = {
                'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a',
                'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
                'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
                'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o', 'ö': 'o',
                'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
                'ç': 'c', 'ñ': 'n'
            }
            for accented, unaccented in replacements.items():
                text = text.replace(accented, unaccented)
        
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)  # Remove pontuação
        text = ' '.join(text.split())  # Remove espaços extras
        return text

    def classify(self, text: str) -> Dict:
        """
        Classifica o texto e retorna intenção com metadados
        
        Args:
            text: Texto do usuário
        
        Returns:
            Dict com intenção classificada
        """
        # ========== ETAPA 1: Tentar Regex primeiro (mais preciso) ==========
        intent, entity = self.patterns.match_intent(text)
        fields = self.patterns.extract_fields(text)
        
        if intent:
            return {
                "intent": intent,
                "entity": entity,
                "fields": fields,
                "text": text,
                "method": "regex",
                "confidence": 0.9  # Regex tem alta confiança
            }
        
        # ========== ETAPA 2: Fallback com Keywords Expandidas ==========
        text_normalized = self._normalize(text)
        text_words = set(text_normalized.split())
        
        best_intent = "unknown"
        best_score = 0
        
        for intent_name, keywords in self.keywords.items():
            score = 0
            for keyword in keywords:
                keyword_normalized = self._normalize(keyword)
                
                # Match exato da frase completa
                if keyword_normalized in text_normalized:
                    score += len(keyword_normalized.split()) * 2  # Peso maior para match exato
                
                # Match por palavras individuais
                keyword_words = set(keyword_normalized.split())
                overlap = len(text_words & keyword_words)
                if overlap > 0:
                    score += overlap
            
            if score > best_score:
                best_score = score
                best_intent = intent_name
        
        # Calcula confiança (normalizada)
        confidence = min(1.0, best_score / 10) if best_score > 0 else 0.0
        
        # Extrai possível entidade (palavra após keywords)
        extracted_entity = None
        if best_intent != "unknown":
            text_lower = text.lower()
            words = text_lower.split()
            for i, word in enumerate(words):
                if word in ["de", "do", "da", "dos", "das"] and i + 1 < len(words):
                    extracted_entity = words[i + 1]
                    break
                if i > 0 and words[i-1] in ["crud", "form", "page", "página", "model", "pagina"]:
                    extracted_entity = word
                    break
        
        return {
            "intent": best_intent,
            "entity": extracted_entity,
            "fields": fields,
            "text": text,
            "method": "keyword_expanded" if best_intent != "unknown" else "none",
            "confidence": confidence
        }
    
    def suggest_intents(self, text: str, limit: int = 3) -> List[Tuple[str, float]]:
        """Sugere possíveis intenções baseadas em similaridade lexical"""
        suggestions = []
        text_lower = text.lower()
        text_normalized = self._normalize(text)
        text_words = set(text_normalized.split())
        
        for intent, keywords in self.keywords.items():
            max_score = 0.0
            
            # Score baseado nas keywords expandidas
            for keyword in keywords:
                keyword_normalized = self._normalize(keyword)
                keyword_words = set(keyword_normalized.split())
                
                if keyword_normalized in text_normalized:
                    score = len(keyword_normalized.split()) / max(1, len(text_words))
                    max_score = max(max_score, score)
                
                overlap = len(text_words & keyword_words)
                if overlap > 0:
                    score = overlap / len(keyword_words) if keyword_words else 0
                    max_score = max(max_score, score)
            
            if max_score > 0.1:
                suggestions.append((intent, max_score))
        
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return suggestions[:limit]
    
    def get_intent_description(self, intent: str) -> str:
        """Retorna descrição de uma intenção"""
        descriptions = {
            "create_crud": "Cria um CRUD completo para uma entidade",
            "create_form": "Cria um formulário Flet",
            "create_page": "Cria uma nova página",
            "create_model": "Cria um modelo de dados",
            "create_test": "Cria testes para o código",
            "analyze": "Analisa um componente do projeto",
            "where": "Busca informações no código do projeto",
            "refactor": "Sugere melhorias para o código",
            "deploy": "Publica/deploy da aplicação",
            "dependencies": "Gerencia dependências do projeto",
            "debug": "Ajuda a depurar código",
            "performance": "Análise de performance",
            "help": "Mostra ajuda com comandos",
            "exit": "Sai do programa",
            "unknown": "Comando não reconhecido"
        }
        return descriptions.get(intent, "Comando desconhecido")