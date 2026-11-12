# flai/cli/repl_unified.py
"""
REPL Unificado do FLAI com Suporte a RAG e Histórico Markdown
"""
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio

from flai.core import get_agent_manager, get_rag, get_context_manager, get_ollama
from flai.core.agents.router_agent import RouterAgent
from flai.core.project import get_project_root
from flai.core.types import RouteResult, ResultType
from flai.cli.console.console import console
from flai.core.security import safe_name, safe_join

class ConversationHistory:
    """Gerencia histórico de conversa em Markdown"""
    
    def __init__(self, project_path: Path, session_name: Optional[str] = None):
        self.project_path = project_path
        self.sessions_dir = project_path / ".flai" / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        # Cria ou carrega sessão
        if session_name:
            self.session_name = safe_name(session_name)
            self.session_file = safe_join(self.sessions_dir, f"{self.session_name}.md")
        else:
            self.session_name = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.session_file = self.sessions_dir / f"session_{self.session_name}.md"
        
        self.conversation = []
        self._load_existing()
    
    def _load_existing(self):
        """Carrega conversa existente se o arquivo já existe"""
        if self.session_file.exists():
            console.print(f"[dim]📜 Carregando sessão existente: {self.session_name}[/dim]")
    
    def add_entry(self, user_input: str, assistant_response: str, metadata: Optional[Dict] = None):
        """
        Adiciona entrada ao histórico
        
        Args:
            user_input: Entrada do usuário
            assistant_response: Resposta do assistente
            metadata: Metadados adicionais (intenção, modelo usado, etc)
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user_input,
            "assistant": assistant_response,
            "metadata": metadata or {}
        }
        self.conversation.append(entry)
        self._save_to_markdown()
    
    def _save_to_markdown(self):
        """Salva conversa em formato Markdown estruturado"""
        lines = []
        
        # Cabeçalho da sessão
        lines.append(f"# 📝 Sessão FLAI: {self.session_name}\n")
        lines.append(f"**Início:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append(f"**Arquivo:** `{self.session_file.name}`\n")
        lines.append("---\n")
        
        # Estatísticas rápidas
        lines.append("## 📊 Estatísticas da Sessão\n")
        lines.append(f"- Total de interações: {len(self.conversation)}\n")
        
        # Categorias de intenção (se disponível)
        intents = {}
        for entry in self.conversation:
            intent = entry.get("metadata", {}).get("intent", "unknown")
            intents[intent] = intents.get(intent, 0) + 1
        
        if intents:
            lines.append("\n**Intenções detectadas:**\n")
            for intent, count in intents.items():
                lines.append(f"- `{intent}`: {count} vez(es)\n")
        
        lines.append("\n---\n")
        
        # Conversa
        lines.append("## 💬 Conversa\n")
        
        for i, entry in enumerate(self.conversation, 1):
            timestamp = datetime.fromisoformat(entry["timestamp"]).strftime("%H:%M:%S")
            
            # Entrada do usuário
            lines.append(f"\n### 🗣️ Usuário ({timestamp})\n")
            lines.append(f"{entry['user']}\n")
            
            # Metadados se houver
            if entry.get("metadata"):
                metadata = entry["metadata"]
                if metadata.get("intent"):
                    lines.append(f"*Intenção: `{metadata['intent']}`*\n")
                if metadata.get("model"):
                    lines.append(f"*Modelo: `{metadata['model']}`*\n")
                if metadata.get("rag_used"):
                    lines.append(f"*🔍 RAG utilizado: Sim*\n")
            
            # Resposta do assistente (com detecção de código)
            lines.append(f"\n### 🤖 FLAI ({timestamp})\n")
            
            # Detecta e formata blocos de código
            raw_response = entry.get('assistant', "")
            
            if isinstance(raw_response, dict):
                # Se for um dicionário residual, extrai o texto dele de forma segura
                response = raw_response.get("content", raw_response.get("text", str(raw_response)))
                if isinstance(response, dict):
                    import json
                    response = json.dumps(response, ensure_ascii=False, indent=2)
            else:
                response = str(raw_response)
            # response = entry['assistant']
            if '```' in response:
                # Já tem blocos de código, mantém como está
                lines.append(response)
            else:
                # Tenta detectar código inline
                import re
                code_pattern = r'(def |class |import |from |@app\.|ft\.)'
                if re.search(code_pattern, response):
                    # Pode conter código, adiciona em bloco
                    lines.append(f"```python\n{response}\n```")
                else:
                    lines.append(response)
            
            lines.append("\n---\n")
        
        # Rodapé
        lines.append(f"\n✨ **Fim da sessão**\n")
        lines.append(f"*Exportado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        # Salva arquivo
        content = "\n".join(lines)
        self.session_file.write_text(content, encoding='utf-8')
    
    def export_to_markdown(self, output_path: Optional[Path] = None) -> Path:
        """Exporta conversa para arquivo Markdown"""
        if output_path is None:
            output_path = self.sessions_dir / f"{self.session_name}_export.md"
        
        self._save_to_markdown()  # Garante que está atualizado
        import shutil
        shutil.copy(self.session_file, output_path)
        return output_path
    
    def get_last_n(self, n: int = 5) -> List[Dict]:
        """Retorna últimas N interações"""
        return self.conversation[-n:]
    
    def clear(self):
        """Limpa conversa atual (inicia nova)"""
        self.conversation = []
        self.session_name = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_file = self.sessions_dir / f"session_{self.session_name}.md"
        console.print("[yellow]🧹 Histórico limpo. Nova sessão iniciada.[/yellow]")


class FLAIUnifiedREPL:
    """
    REPL unificado do FLAI integrando RouterAgent, RAG e Histórico
    """
    
    def __init__(self, project_path: Optional[Path] = None, model: Optional[str] = None):
        self.project_path = project_path or get_project_root() or Path.cwd()
        self.model = model
        self.running = True
        
        # Carrega configuração
        self.config: Dict[str, Any] = {}
        self._load_config()
        
        # Confirmação antes de ações que alteram o projeto ou executam código dele
        self._status = None  # spinner ativo; para antes de qualquer pergunta ao usuário
        self._prompt = None  # PromptSession (prompt_toolkit) criado sob demanda
        self.router = RouterAgent(self.project_path, model=self.model, confirm=self._confirm,
                                  ask=self._ask)
        self.rag = get_rag(self.project_path, auto_index=True)     # ✅ Compartilhado
        self.agent_manager = get_agent_manager(self.project_path)  # ✅ Compartilhado
        self.context_manager = get_context_manager(self.project_path)  # ✅ Compartilhado
        self.ollama = get_ollama()  # ✅ Singleton

        # self.rag = IntegratedRAG(self.project_path, auto_index=True)
        self.history = ConversationHistory(self.project_path)
        # self.ollama = get_ollama_manager()
        
        # Cache para evitar verificações repetidas
        self._initialized = False
    
    SLASH_COMMANDS = ["/help", "/contexto", "/desfazer", "/history", "/export", "/clear",
                      "/tokens", "/tokens refresh", "/rag index", "/rag search", "/exit"]

    async def _read_input(self) -> str:
        """prompt_toolkit (histórico em disco + autocompletar) com fallback para input simples."""
        if self._prompt is None:
            try:
                from prompt_toolkit import PromptSession
                from prompt_toolkit.history import FileHistory
                from prompt_toolkit.completion import WordCompleter
                hist = self.project_path / ".flai" / "input_history"
                hist.parent.mkdir(parents=True, exist_ok=True)
                words = self.SLASH_COMMANDS + ["criar crud de", "fleting"] + self.router._entities()
                self._prompt = PromptSession(history=FileHistory(str(hist)),
                                             completer=WordCompleter(words, sentence=True))
            except ImportError:
                self._prompt = False
        if self._prompt:
            from prompt_toolkit.formatted_text import HTML
            pending = self.router.session.pending
            if pending:
                console.print(f"[dim]↪ responda à pergunta acima (s/n) ou peça outra coisa[/dim]")
            return await self._prompt.prompt_async(HTML("\n<ansicyan><b>💬 Você</b></ansicyan>: "))
        return console.input("\n[bold cyan]💬 Você[/bold cyan]: ")

    def _show_context(self):
        s = self.router.session
        console.print("[bold cyan]🧭 Contexto da conversa[/bold cyan]")
        console.print(f"  foco: {s.focus_entity or '-'}")
        console.print(f"  arquivos recentes: {', '.join(s.recent_files) or '-'}")
        console.print(f"  memória: {len(s.history) // 2} troca(s) (máx. {s.max_turns})")
        console.print(f"  pergunta pendente: {s.pending or '-'}")
        changed = self.router.toolbox.changed_files
        console.print(f"  alterados nesta sessão: {', '.join(changed) or '-'}")

    def _pause_spinner(self):
        if self._status is not None:
            self._status.stop()

    def _confirm(self, question: str) -> bool:
        from rich.markup import escape
        self._pause_spinner()  # senão o spinner sobrescreve a pergunta
        answer = console.input(f"[yellow]⚠️ {escape(question)} \\[s/N]: [/yellow]").strip().lower()
        return answer in ("s", "sim", "y", "yes")

    def _ask(self, question: str, default: str = "") -> str:
        from rich.markup import escape
        self._pause_spinner()
        hint = f" \\[{escape(default)}]" if default else ""
        answer = console.input(f"[cyan]❓ {escape(question)}{hint}: [/cyan]").strip()
        return answer or default

    def _load_config(self):
        """Carrega configuração do projeto"""
        config_file = self.project_path / ".flai" / "config.json"
        if config_file.exists():
            import json
            try:
                with open(config_file) as f:
                    config = json.load(f)
                    self.config = config
                    if not self.model:
                        self.model = config.get("model", "flai-coder")
            except:
                if not self.model:
                    self.model = "flai-coder"
        else:
            if not self.model:
                self.model = "flai-coder"
    
    def _initialize(self) -> bool:
        """Inicializa ambiente (verifica Ollama, etc)"""
        if self._initialized:
            return True
        
        console.print("[dim]🔍 Verificando ambiente...[/dim]")
        
        # Verifica Ollama
        if not self.ollama.ensure_ready(self.model, verbose=False):
            console.print("[red]❌ Ollama não está pronto. Execute 'flai init' primeiro.[/red]")
            return False
        
        # RAM e limites de tokens: usa modelo derivado com contexto reduzido
        self._prepare_tokens()
        self.router.warmup_async()  # carrega o modelo + system prompt enquanto o usuário digita

        # Mostra status do RAG
        rag_stats = self.rag.get_stats()
        if rag_stats.get("exists"):
            console.print(f"[dim]✅ RAG disponível: {rag_stats.get('total_documents', 0)} documentos indexados[/dim]")
        else:
            console.print("[dim]⚠️ RAG não disponível (instale langchain para busca semântica)[/dim]")
        
        self._initialized = True
        return True
    
    def _prepare_tokens(self):
        plan = self.router.prepare_model(
            context_tokens=int(self.config.get("context_tokens", 2048)),
            max_tokens=int(self.config.get("max_tokens", 512)),
            use_optimized=bool(self.config.get("use_optimized_model", True)),
            temperature=float(self.config.get("temperature", 0.7)),
        )
        self.model = self.router.model
        console.print(f"[dim]🧠 {plan.summary()}[/dim]")
        if self.model != self.router.base_model:
            console.print(f"[dim]⚙️ Modelo filtrado: {self.model} (base {self.router.base_model})[/dim]")
        for w in plan.warnings:
            console.print(f"[yellow]⚠️ {w}[/yellow]")

    def _show_tokens(self):
        plan = self.router.plan
        if not plan:
            console.print("[dim]Plano de tokens ainda não calculado[/dim]")
            return
        console.print(f"[cyan]🧠 {plan.summary()}[/cyan]")
        console.print(f"[dim]Orçamento do prompt: {plan.prompt_budget} tokens[/dim]")
        if self.router.last_tokens:
            t = self.router.last_tokens
            console.print(f"[dim]Última pergunta: estimado {t['estimated_prompt']} · "
                          f"real prompt {t['prompt']} + resposta {t['output']}[/dim]")
        console.print('[dim]Ajuste em .flai/config.json: "context_tokens", "max_tokens", '
                      '"use_optimized_model". /tokens refresh recalcula com a RAM atual.[/dim]')

    def _print_welcome(self):
        """Exibe mensagem de boas-vindas"""
        rag_status = "🔍 RAG: ✅" if self.rag.get_stats().get("exists") else "🔍 RAG: ❌"
        
        welcome = f"""
╔══════════════════════════════════════════════════════════════════════╗
║   🚀 FLAI - Framework Local de IA (REPL Unificado v2.0)             ║
║   📁 Projeto: {self.project_path.name:<52}║
║   🤖 Modelo: {self.model:<54}║
║   {rag_status:<62}║
╠══════════════════════════════════════════════════════════════════════╣
║   💡 Comandos:                                                       ║
║      • criar crud de <entidade>                                     ║
║      • criar form de <nome>                                         ║
║      • analise o <componente>                                       ║
║      • onde está <código/busca>                                     ║
║      • criar página <nome> | criar model <nome>                     ║
║      • fleting <comando>  (ex.: fleting list pages, fleting doctor) ║
║      • converse livremente: a IA lê, edita (com diff) e lembra      ║
║      • /contexto        - Foco, memória e arquivos recentes         ║
║      • /desfazer        - Reverte a última alteração de arquivo     ║
║      • /help            - Mostra ajuda completa                     ║
║      • /history         - Mostra histórico da sessão                ║
║      • /export          - Exporta histórico para Markdown           ║
║      • /clear           - Limpa histórico (nova sessão)             ║
║      • /tokens [refresh] - RAM, contexto e uso de tokens            ║
║      • /rag index       - (Re)indexa projeto para busca semântica   ║
║      • /rag search <q>  - Busca semântica no código                 ║
║      • /exit ou /quit   - Sai do programa                           ║
╚══════════════════════════════════════════════════════════════════════╝
"""
        console.print(welcome)
    
    def _handle_command(self, cmd: str) -> bool:
        """
        Processa comandos especiais (iniciados com /)
        
        Returns:
            True se foi comando, False se é pergunta normal
        """
        if not cmd.startswith('/'):
            return False
        
        cmd_parts = cmd[1:].lower().split()
        if not cmd_parts:
            return True
        
        command = cmd_parts[0]
        
        # Comandos de sistema
        if command in ['exit', 'quit', 'sair']:
            self.running = False
            console.print("[yellow]👋 Saindo...[/yellow]")
            return True
        
        elif command == 'help':
            self._show_help()
            return True
        
        elif command == 'history':
            self._show_history()
            return True
        
        elif command == 'clear':
            self.history.clear()
            self.router.session.clear()
            console.print("[dim]🧹 Memória da conversa limpa[/dim]")
            return True

        elif command in ('contexto', 'context'):
            self._show_context()
            return True

        elif command in ('desfazer', 'undo'):
            msg = self.router.undo()
            console.print(f"[green]{msg}[/green]" if msg else "[dim]Nada para desfazer[/dim]")
            return True

        elif command == 'tokens':
            if len(cmd_parts) > 1 and cmd_parts[1] == 'refresh':
                self.router.model = self.router.base_model
                self._prepare_tokens()
            self._show_tokens()
            return True
        
        elif command == 'export':
            output = Path(cmd_parts[1]) if len(cmd_parts) > 1 else None
            exported = self.history.export_to_markdown(output)
            console.print(f"[green]✅ Histórico exportado para: {exported}[/green]")
            return True
        
        # Comandos RAG
        elif command == 'rag':
            if len(cmd_parts) < 2:
                console.print("[yellow]Uso: /rag index | /rag search <consulta>[/yellow]")
                return True
            
            subcmd = cmd_parts[1]
            
            if subcmd == 'index':
                console.print("[yellow]📚 Reindexando projeto...[/yellow]")
                if self.rag.rag.index_project(verbose=True):
                    console.print("[green]✅ Indexação concluída![/green]")
                else:
                    console.print("[red]❌ Falha na indexação. LangChain instalado?[/red]")
                return True
            
            elif subcmd == 'search' and len(cmd_parts) > 2:
                query = ' '.join(cmd_parts[2:])
                console.print(f"[dim]🔍 Buscando: {query}[/dim]")
                results = self.rag.search(query, k=5)
                
                if results:
                    console.print(f"[green]✅ Encontrados {len(results)} resultados:[/green]\n")
                    for i, result in enumerate(results, 1):
                        console.print(f"{i}. 📄 {Path(result['source']).name}")
                        console.print(f"   Similaridade: {(1 - result['score']):.2%}")
                        console.print(f"   {result['content'][:200]}...\n")
                else:
                    console.print("[yellow]ℹ️ Nenhum resultado encontrado[/yellow]")
                return True
            
            else:
                console.print("[yellow]Comando RAG inválido. Use: /rag index | /rag search <consulta>[/yellow]")
                return True
        
        else:
            console.print(f"[yellow]Comando desconhecido: {command}. Use /help[/yellow]")
            return True
    
    def _show_help(self):
        """Mostra ajuda detalhada"""
        help_text = """
╔══════════════════════════════════════════════════════════════════════╗
║                          📚 AJUDA COMPLETA                           ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  🚀 CRUD e Formulários                                               ║
║  ────────────────────────────────────────────────────────────────── ║
║  • criar crud de produtos                                            ║
║  • criar crud de usuarios com nome, email, senha                     ║
║  • criar formulário de contato                                       ║
║  • criar form login com usuario, senha                               ║
║                                                                      ║
║  🔍 Análise e Busca                                                  ║
║  ────────────────────────────────────────────────────────────────── ║
║  • analise o controller user                                        ║
║  • onde está a função de autenticação?                               ║
║  • mostre o model produto                                           ║
║                                                                      ║
║  🔎 Busca Semântica (RAG)                                            ║
║  ────────────────────────────────────────────────────────────────── ║
║  • /rag index              - Indexa/Reindexa o projeto               ║
║  • /rag search validação email - Busca no código                     ║
║                                                                      ║
║  💾 Histórico e Sessão                                               ║
║  ────────────────────────────────────────────────────────────────── ║
║  • /history               - Mostra histórico da sessão               ║
║  • /export [arquivo.md]   - Exporta conversa para Markdown           ║
║  • /clear                 - Limpa histórico (nova sessão)            ║
║                                                                      ║
║  🛠️ Sistema                                                          ║
║  ────────────────────────────────────────────────────────────────── ║
║  • /help                  - Mostra esta ajuda                        ║
║  • /exit ou /quit         - Sai do programa                          ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""
        console.print(help_text)
    
    def _show_history(self):
        """Mostra histórico da conversa atual"""
        conv = self.history.get_last_n(10)
        
        if not conv:
            console.print("[dim]ℹ️ Nenhuma conversa ainda[/dim]")
            return
        
        console.print("\n[bold cyan]📜 Histórico Recente:[/bold cyan]\n")
        
        for i, entry in enumerate(conv, 1):
            timestamp = datetime.fromisoformat(entry["timestamp"]).strftime("%H:%M:%S")
            console.print(f"[dim]{i}. [{timestamp}][/dim]")
            console.print(f"   [bold yellow]💬 Você:[/bold yellow] {entry['user'][:80]}")
            
            # Mostra preview da resposta
            response_preview = entry['assistant'][:100] + "..." if len(entry['assistant']) > 100 else entry['assistant']
            console.print(f"   [bold green]🤖 FLAI:[/bold green] {response_preview}\n")
    
    async def run(self):
        """Executa o REPL principal"""
        if not self._initialize():
            return
        
        self._print_welcome()
        
        while self.running:
            try:
                # Input do usuário (↑ histórico, Tab autocompleta comandos/entidades)
                user_input = (await self._read_input()).strip()
                
                if not user_input:
                    continue
                
                # Verifica se é comando
                if user_input.startswith('/'):
                    self._handle_command(user_input)
                    continue
                
                # O router monta o contexto (RAG incluso) sem alterar o texto do usuário,
                # para o histórico da conversa guardar a pergunta original.
                enhanced_input = user_input

                # Spinner até o primeiro token; depois o texto aparece enquanto é gerado
                status = console.status("[dim]🤔 Pensando...")
                status.start()
                self._status = status
                started = []

                def on_token(chunk: str):
                    if not started:
                        status.stop()
                        console.print("\n[bold green]🤖 FLAI:[/bold green]")
                        console.print("─" * 60)
                        started.append(True)
                    console.out(chunk, end="", highlight=False)

                self.router.on_token = on_token
                try:
                    result = await self.router.route(enhanced_input)
                finally:
                    status.stop()
                    self._status = None
                    self.router.on_token = None

                if not isinstance(result, dict):
                    result = {"type": "unknown", "content": str(result)}

                # Formata resposta para exibição
                response_text = self._format_result(result)
                
                # Salva no histórico com metadados
                metadata = {
                    "intent": result.get("type", "unknown"),
                    "model": self.model,
                    "rag_used": enhanced_input != user_input,
                    "timestamp": datetime.now().isoformat()
                }
                self.history.add_entry(user_input, response_text, metadata)
                
                # Exibe resposta (se veio por streaming, já está na tela: só as notas)
                if result.get("streamed") and started:
                    console.print("\n" + "─" * 60)
                    for note in result.get("notes", []):
                        console.print(f"[dim]{note}[/dim]")
                else:
                    self._display_response(response_text, result.get("type"))
                
            except KeyboardInterrupt:
                console.print("\n[yellow]⚠️ Interrompido. Digite /exit para sair[/yellow]")
            except Exception as e:
                console.print(f"[red]❌ Erro: {e}[/red]")
                import traceback
                traceback.print_exc()
    
    def _format_result(self, result: RouteResult) -> str:
        """Formata resultado tipado para exibição garantindo retorno em string"""
        if not result:
            return "Nenhum resultado retornado."

        if isinstance(result, str):
            return result

        result_type = result.get("type", ResultType.ERROR)
        
        if result_type == ResultType.CRUD_RESULT:
            lines = [f"{'✅' if s['success'] else '⏭️'} {s['message']}" for s in result.get("steps", [])]
            if result.get("success"):
                lines.insert(0, f"✅ CRUD '{result.get('entity')}' criado com sucesso!")
            else:
                errors = result.get("errors") or ["Falha"]
                lines.insert(0, f"❌ Erro: {errors[0]}")
            return "\n".join(lines)

        elif result_type == "fleting":
            return result.get("content", "")
        
        elif result_type == ResultType.FORM_RESULT:
            return f"✅ {result.get('content', {}).get('message', 'Formulário criado')}"
        
        elif result_type == ResultType.ANALYSIS:
            return result.get("content", "")
        
        elif result_type == ResultType.SEARCH_RESULTS:
            content = result.get("content", [])
            if content:
                return f"🔍 Encontrados {len(content)} resultados"
            return "ℹ️ Nenhum resultado encontrado"
        
        elif result_type == ResultType.HELP:
            return result.get("content", "")
        
        elif result_type == ResultType.EXIT:
            return "Saindo..."
        
        elif result_type == ResultType.LLM_RESPONSE:
            return result.get("content", "")
        
        else:
            return str(result.get("content", "Comando processado."))
    
    def _display_response(self, response: str, result_type: ResultType):
        """Exibe resposta formatada"""
        console.print("\n[bold green]🤖 FLAI:[/bold green]")
        console.print("─" * 60)

        if isinstance(response, dict):
            raw_content = response.get("content", response.get("text", response.get("report", str(response))))
            if isinstance(raw_content, dict):
                import json
                response = json.dumps(raw_content, ensure_ascii=False, indent=2)
            else:
                response = str(raw_content)
        else:
            # Garante que qualquer outro tipo não-string vire string
            response = str(response)
        
        if result_type == ResultType.SEARCH_RESULTS and "```" not in response:
            # Resultado de busca - formato especial
            console.print(response)
        elif "```" in response:
            console.print(response)
        else:
            # Detecta código
            import re
            if re.search(r'^\s{4}(def |class |import |from )', response, re.MULTILINE):
                console.print("[cyan]```python[/cyan]")
                console.print(response)
                console.print("[cyan]```[/cyan]")
            else:
                console.print(response)
        
        console.print("─" * 60)


def run_unified_repl(project_path: Optional[Path] = None, model: Optional[str] = None,
                     session: Optional[str] = None):
    """Função principal para iniciar o REPL unificado"""
    repl = FLAIUnifiedREPL(project_path, model)
    if session:
        repl.history = ConversationHistory(repl.project_path, session)
    asyncio.run(repl.run())
    # repl.run()