"""
Assistente conversacional do FLAI: memória + ferramentas + ciclo planejar/agir/verificar.

Ordem das mensagens (pensada para o cache de prefixo do Ollama):
    [system fixo + mapa do código]  ← igual entre perguntas → reaproveita o KV cache
    [histórico: user/assistant ...] ← só cresce no fim
    [pergunta atual + contexto do turno (foco, arquivo citado, RAG)]
Assim só a parte nova do prompt é processada a cada mensagem.
"""
from __future__ import annotations

import json
import re
from typing import Callable, Dict, List, Optional

from flai.cli.console.console import console
from flai.core.resources import estimate_tokens
from .session import Session
from .tools import TOOL_SPECS, TOOL_NAMES, ToolBox, select_tools

MAX_STEPS = 5
TOOLS_TOKENS = estimate_tokens(json.dumps(TOOL_SPECS, ensure_ascii=False))
# Abaixo disto o assistente (system + mapa + ferramentas) não cabe com folga
MIN_ASSISTANT_CTX = 4096

ASSISTANT_RULES = """
## Como trabalhar
- Seja CURTO: até 8 linhas ou um bloco de código pequeno. Sem introdução nem resumo.
- Para responder sobre código, LEIA o arquivo com ler_arquivo antes; não invente conteúdo.
- Para criar OU reescrever um método (ex.: render) use escrever_metodo com o def COMPLETO.
- Mudança pequena de poucas linhas: editar_arquivo (trecho exato). Arquivo novo: criar_arquivo.
  O usuário vê o diff e confirma. Se cancelar, pergunte o que ajustar.
- Só diga que alterou algo se a ferramenta respondeu "OK".
- NUNCA pergunte "quer que eu edite?" antes de editar: chame a ferramenta direto. O FLAI já
  mostra o diff e pede a confirmação do usuário.
- Listagem/tabela de registros numa view: use criar_listagem(entidade).
- Para criar CRUD/tabela use criar_crud. Para comandos Fleting use a ferramenta fleting.
- Implemente POR DOMÍNIO e nesta ordem: migração → model → controller → view (+rota) →
  verificação. Antes, veja o que existe com fleting "list pages" (e "list routes").
  Cada domínio no seu arquivo: regra de dados no model/controller, tela só na view.
- Se uma ferramenta retornar ERRO, corrija e tente de novo (no máximo uma vez).
- Se faltar informação essencial, faça UMA pergunta objetiva e pare.
- Ao concluir uma ação, termine com UMA sugestão curta de próximo passo, em forma de
  pergunta (ex.: "Quer que eu crie a listagem na usuarios_view?").
- Se o usuário responder "sim" a uma sugestão sua, execute-a.
- Perguntas conceituais simples: responda direto, sem ferramentas.
"""


class StreamGate:
    """
    Repassa tokens ao terminal, mas segura o início se parecer uma chamada de ferramenta
    escrita como texto (modelos pequenos às vezes emitem o JSON em vez de tool_calls).
    """

    # "```python" libera logo no 4º caractere; só "```json", "{" e "<tool_call>" seguram
    PREFIXES = ("{", "```json", "<tool_call>")

    def __init__(self, sink: Optional[Callable[[str], None]]):
        self.sink = sink
        self.buf = ""
        self.open = False

    def __call__(self, chunk: str) -> None:
        if self.open:
            if self.sink:
                self.sink(chunk)
            return
        self.buf += chunk
        head = self.buf.lstrip()
        if not head:
            return
        if any(p.startswith(head[:len(p)]) for p in self.PREFIXES):
            return  # pode ser JSON de ferramenta: segura até o fim desta geração
        self.flush()

    def flush(self) -> None:
        self.open = True
        if self.buf and self.sink:
            self.sink(self.buf)
        self.buf = ""

    @property
    def held(self) -> str:
        return "" if self.open else self.buf


def parse_text_tool_call(text: str) -> List[Dict]:
    """Extrai {"name": ..., "arguments": {...}} escrito como texto pelo modelo."""
    body = re.sub(r"^```(?:json)?|```$|</?tool_call>", "", text.strip(), flags=re.M).strip()
    decoder, calls, i = json.JSONDecoder(), [], 0
    # Pode haver vários objetos seguidos (um por linha): decodifica um a um
    while i < len(body):
        start = body.find("{", i)
        if start < 0:
            break
        try:
            data, end = decoder.raw_decode(body, start)
        except ValueError:
            i = start + 1
            continue
        i = end
        for item in data if isinstance(data, list) else [data]:
            if isinstance(item, dict) and item.get("name") in TOOL_NAMES:
                calls.append({"function": {"name": item["name"],
                                           "arguments": item.get("arguments") or item.get("parameters") or {}}})
    return calls


class Assistant:
    def __init__(self, ollama, toolbox: ToolBox, session: Session,
                 system_prompt: str, code_map: Callable[[], str]):
        self.ollama = ollama
        self.tools = toolbox
        self.session = session
        self.base_system = system_prompt
        self.code_map = code_map
        self._system_cache: Optional[str] = None
        self._map_cache: Optional[str] = None

    def system_message(self) -> str:
        """Prompt fixo; só muda quando o mapa do código muda (arquivo criado etc.)."""
        code_map = self.code_map()
        if self._system_cache is None or code_map != self._map_cache:
            self._map_cache = code_map
            self._system_cache = (f"{self.base_system}\n{ASSISTANT_RULES}\n"
                                  f"## Mapa do código (arquivo: classes/métodos)\n{code_map}")
        return self._system_cache

    @staticmethod
    def _fit(messages: List[Dict], budget: int) -> List[Dict]:
        """
        Cabe no orçamento sem deixar o Ollama cortar o INÍCIO do prompt (o system):
        1º remove trocas antigas do histórico; 2º encurta o contexto do turno atual.
        """
        def size(ms):
            return sum(estimate_tokens(m.get("content") or "") + 4 for m in ms)
        while size(messages) > budget and len(messages) > 3 and messages[1]["role"] == "user" \
                and messages[2]["role"] == "assistant":
            del messages[1:3]  # mantém o system [0] e a pergunta atual
        excess = size(messages) - budget
        if excess > 0:
            # Encurta a maior mensagem que não seja o system (contexto do turno / saída de ferramenta)
            idx = max(range(1, len(messages)), key=lambda i: len(messages[i].get("content") or ""))
            text = messages[idx]["content"]
            keep = max(200, len(text) - int(excess * 3.2) - 50)
            messages[idx] = {**messages[idx], "content": text[:keep] + "\n[... cortado por limite de contexto]"}
        return messages

    def run(self, user_input: str, turn_context: str, plan, on_token=None,
            num_predict: Optional[int] = None) -> Dict:
        system = self.system_message()
        user_msg = user_input if not turn_context else f"{user_input}\n\n## Contexto\n{turn_context}"
        messages = [{"role": "system", "content": system}, *self.session.messages(),
                    {"role": "user", "content": user_msg}]
        num_predict = num_predict or plan.num_predict
        # A definição das ferramentas também ocupa o contexto (~1000 tokens), mais o template
        budget = max(256, plan.effective_ctx - num_predict - TOOLS_TOKENS - 96)
        # Temperatura baixa: escolha de ferramenta e argumentos precisam ser determinísticos
        options = {"num_ctx": plan.effective_ctx, "num_predict": num_predict, "temperature": 0.1}
        # Lista de ferramentas fixa (faz parte do prefixo em cache); a seleção por pedido vai
        # como dica no fim da mensagem e chamadas fora dela são recusadas com orientação.
        tools = TOOL_SPECS
        allowed = [t["function"]["name"] for t in select_tools(user_input)]
        messages[-1]["content"] += f"\n\n(Ferramentas indicadas: {', '.join(allowed)})"
        seen_calls = set()

        totals = {"prompt": 0, "output": 0, "eval_seconds": 0.0, "prompt_seconds": 0.0, "steps": 0}
        final_text, done_reason, used_tools = "", None, []
        self.tools.failed_writes.clear()
        for step in range(MAX_STEPS):
            messages = self._fit(messages, budget)
            gate = StreamGate(on_token)
            res = self.ollama.chat(self.tools_model, messages, tools=tools,
                                   options=options, on_token=gate)
            totals["steps"] += 1
            for k_src, k_dst in (("output_tokens", "output"), ("eval_seconds", "eval_seconds"),
                                 ("prompt_seconds", "prompt_seconds")):
                totals[k_dst] += res.get(k_src) or 0
            totals["prompt"] = max(totals["prompt"], res.get("prompt_tokens") or 0)  # maior passo
            if not res.get("ok"):
                return {"ok": False, "text": res.get("text", "erro"), "tokens": totals}

            calls = res.get("tool_calls") or []
            if not calls and gate.held and allowed:
                calls = parse_text_tool_call(gate.held)
                if not calls:
                    gate.flush()  # era texto normal começando com { ou ```
            done_reason = res.get("done_reason")
            if not calls:
                final_text = res.get("text", "")
                break

            messages.append({"role": "assistant", "content": res.get("text", "") if gate.open else "",
                             "tool_calls": calls})
            for call in calls[:3]:
                fn = call.get("function") or {}
                name, args = fn.get("name", ""), fn.get("arguments") or {}
                console.print(f"[dim]🔧 {name}({self._args_preview(args)})[/dim]")
                key = (name, json.dumps(args, sort_keys=True, ensure_ascii=False))
                if key in seen_calls:
                    # Loop: mesma chamada de novo. Para e responde com o que tem.
                    out = ("ERRO: chamada repetida e idêntica. NÃO chame ferramentas de novo; "
                           "diga ao usuário em 1 frase o que falhou.")
                    allowed = []
                elif name not in allowed:
                    out = (f"ERRO: '{name}' não serve para este pedido. Use uma destas: "
                           f"{', '.join(allowed) or 'nenhuma — responda em texto'}.")
                else:
                    seen_calls.add(key)
                    out = self.tools.run(name, args)
                used_tools.append(name)
                messages.append({"role": "tool", "content": out, "tool_name": name})
            if done_reason == "interrupted":
                break
        else:
            final_text = final_text or "⚠️ Limite de passos atingido. Diga como quer continuar."
            if on_token:
                on_token(final_text)

        # Não deixa o modelo afirmar sucesso de algo que não foi aplicado
        if self.tools.failed_writes:
            warn = ("\n\n⚠️ Alteração NÃO aplicada em: " + ", ".join(sorted(set(self.tools.failed_writes)))
                    + ". O arquivo continua como estava.")
            final_text += warn
            if on_token:
                on_token(warn)
        self.session.add_turn(user_input, final_text or "(ação executada)")
        return {"ok": True, "text": final_text, "tokens": totals, "done_reason": done_reason,
                "tools": used_tools, "num_predict": num_predict}

    def warmup(self, plan) -> None:
        """Pré-processa o system prompt (fica no KV cache): a 1ª pergunta já responde rápido."""
        self.ollama.chat(self.tools_model, [{"role": "system", "content": self.system_message()},
                                            {"role": "user", "content": "ok"}],
                         tools=TOOL_SPECS,
                         options={"num_ctx": plan.effective_ctx, "num_predict": 1})

    tools_model: str = ""

    @staticmethod
    def _args_preview(args) -> str:
        if not isinstance(args, dict):
            return str(args)[:60]
        parts = []
        for k, v in args.items():
            v = str(v).replace("\n", "⏎")
            parts.append(f"{k}={v[:40] + '…' if len(v) > 40 else v}")
        return ", ".join(parts)
