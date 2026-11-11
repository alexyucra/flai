"""
Estado da conversa: histórico, foco (entidade/arquivos) e pergunta pendente.

Fase 1 do assistente:
  - memória multi-turno (as últimas N trocas vão para /api/chat)
  - foco da sessão ("e o controller dele?" → usuarios)
  - pergunta/sugestão pendente: a próxima resposta do usuário continua a tarefa
    em vez de passar pelo classificador de intenções
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

AFFIRMATIVE = re.compile(r"^(s|sim|ok|pode|claro|isso|manda|faz|fa[cç]a|bora|yes|y)\b", re.I)
NEGATIVE = re.compile(r"^(n|n[aã]o|nao|cancela|deixa|no)\b", re.I)


@dataclass
class Session:
    max_turns: int = 6
    history: List[Dict[str, str]] = field(default_factory=list)  # role/content (texto final)
    focus_entity: Optional[str] = None
    recent_files: List[str] = field(default_factory=list)
    pending: Optional[str] = None  # última pergunta/sugestão do assistente

    # ------------------------------------------------------------ histórico
    def add_turn(self, user: str, assistant: str) -> None:
        self.history += [{"role": "user", "content": user},
                         {"role": "assistant", "content": assistant.strip()}]
        self.history = self.history[-2 * self.max_turns:]
        new_pending = self._extract_pending(assistant)
        # Mesma sugestão de novo = o modelo só repetiu; um "sim" não deve reexecutar
        self.pending = None if new_pending and new_pending == self.pending else new_pending

    def messages(self) -> List[Dict[str, str]]:
        return list(self.history)

    def drop_oldest(self) -> bool:
        """Remove a troca mais antiga (usado quando o contexto não cabe)."""
        if len(self.history) >= 2:
            del self.history[:2]
            return True
        return False

    def clear(self) -> None:
        self.history.clear()
        self.recent_files.clear()
        self.focus_entity = None
        self.pending = None

    @staticmethod
    def _extract_pending(text: str) -> Optional[str]:
        """Última linha terminada em '?' (pergunta ou sugestão de próximo passo)."""
        lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
        for line in reversed(lines[-3:]):
            if line.endswith("?"):
                return line
        return None

    # ----------------------------------------------------------------- foco
    def update_focus(self, text: str, entities: List[str]) -> None:
        # "_" separa palavras também: "usuarios_controller" → usuarios, controller
        words = set(re.split(r"[^a-z0-9à-ú]+", text.lower()))
        for e in sorted(entities, key=len, reverse=True):
            stem = e.rstrip("s")  # "usuario" também casa "usuarios"
            if len(stem) >= 3 and (stem in words or f"{stem}s" in words or e in words):
                self.focus_entity = e
                return

    def touch_file(self, rel_path: str) -> None:
        if rel_path in self.recent_files:
            self.recent_files.remove(rel_path)
        self.recent_files.insert(0, rel_path)
        del self.recent_files[5:]

    def context_line(self) -> str:
        parts = []
        if self.focus_entity:
            parts.append(f"Foco atual: {self.focus_entity}")
        if self.recent_files:
            parts.append("Arquivos recentes: " + ", ".join(self.recent_files))
        return " · ".join(parts)

    # -------------------------------------------------------- continuidade
    def is_continuation(self, text: str) -> bool:
        """A mensagem é um sim/não à pergunta pendente?"""
        t = text.strip()
        return bool(self.pending and (AFFIRMATIVE.match(t) or NEGATIVE.match(t)))
