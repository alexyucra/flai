# flai/web/server.py
"""
Servidor Web para configuração do FLAI
"""
import flet as ft
import threading
import webbrowser
from pathlib import Path
from typing import Optional, Dict, Any
import json

from flai.core.agents.agent_manager import AgentManager
from flai.core.intent.intent_manager import IntentManager
from flai.core.context.context_manager import ContextManager
from flai.core.rag.integrated_rag import IntegratedRAG
from flai.cli.console.console import console

class FLAIWebServer:
    """Servidor web Flet para gerenciamento do FLAI"""
    
    def __init__(self, project_path: Path, port: int = 8080):
        self.project_path = project_path
        self.port = port
        self.page = None
        
        # Gerenciadores
        self.agent_manager = AgentManager(project_path)
        self.intent_manager = IntentManager(project_path)
        self.context_manager = ContextManager(project_path)
        self.rag = IntegratedRAG(project_path, auto_index=False)
        
        # Estado da aplicação
        self.current_page = "dashboard"
        self.selected_item = None
    
    def start(self, open_browser: bool = True):
        """Inicia o servidor web"""
        console.print(f"[cyan]🌐 Iniciando servidor web em http://localhost:{self.port}[/cyan]")
        
        if open_browser:
            webbrowser.open(f"http://localhost:{self.port}")
        
        ft.app(target=self.main, port=self.port, view=ft.AppView.WEB_BROWSER)
    
    def main(self, page: ft.Page):
        """Página principal do aplicativo"""
        self.page = page
        page.title = "FLAI - Configuração"
        page.theme_mode = ft.ThemeMode.DARK
        page.padding = 0
        page.spacing = 0
        
        # Configurações da página
        page.window_width = 1200
        page.window_height = 800
        page.window_min_width = 800
        page.window_min_height = 600
        
        # Layout principal
        self.setup_layout()
        
        # Navegação inicial
        self.navigate_to("dashboard")
    
    def setup_layout(self):
        """Configura o layout principal"""
        # Sidebar
        self.sidebar = self.create_sidebar()
        
        # Conteúdo principal
        self.content_area = ft.Container(
            expand=True,
            padding=20,
            content=ft.Column(spacing=20, scroll=ft.ScrollMode.AUTO)
        )
        
        # Layout
        self.page.add(
            ft.Row(
                spacing=0,
                expand=True,
                controls=[
                    self.sidebar,
                    ft.VerticalDivider(width=1),
                    self.content_area
                ]
            )
        )
    
    def create_sidebar(self) -> ft.Container:
        """Cria o menu lateral (sem ícones)"""
        nav_items = [
            {"label": "Dashboard", "page": "dashboard"},
            {"label": "Agentes", "page": "agents"},
            {"label": "Intenções", "page": "intents"},
            {"label": "Contextos", "page": "contexts"},
            {"label": "RAG", "page": "rag"},
            {"label": "MCP Servers", "page": "mcp"},
            {"label": "Configurações", "page": "settings"},
        ]
        
        nav_buttons = []
        for item in nav_items:
            btn = ft.Container(
                content=ft.Text(item["label"], size=14),
                padding=ft.padding.symmetric(horizontal=16, vertical=12),
                border_radius=8,
                ink=True,
                on_click=lambda e, p=item["page"]: self.navigate_to(p)
            )
            nav_buttons.append(btn)
        
        return ft.Container(
            width=200,
            bgcolor=ft.Colors.GREY_900,
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Text("FLAI", size=24, weight=ft.FontWeight.BOLD),
                        padding=20,
                    ),
                    ft.Divider(height=1),
                    ft.Column(nav_buttons, spacing=4),
                    ft.Container(expand=True),
                    ft.Divider(height=1),
                    ft.Container(
                        content=ft.Text("v1.0.0", size=12),
                        padding=16,
                    )
                ],
                spacing=0
            )
        )
    
    def navigate_to(self, page_name: str):
        """Navega para uma página específica"""
        self.current_page = page_name
        self.content_area.content.controls.clear()
        
        if page_name == "dashboard":
            self.show_dashboard()
        elif page_name == "agents":
            self.show_agents_page()
        elif page_name == "intents":
            self.show_intents_page()
        elif page_name == "contexts":
            self.show_contexts_page()
        elif page_name == "rag":
            self.show_rag_page()
        elif page_name == "mcp":
            self.show_mcp_page()
        elif page_name == "settings":
            self.show_settings_page()
        
        self.content_area.update()
    
    def show_dashboard(self):
        """Página de dashboard com estatísticas"""
        # Estatísticas dos agentes
        agent_stats = self.agent_manager.get_agent_stats()
        
        # Cards (sem ícones)
        cards = ft.ResponsiveRow(
            controls=[
                self.create_stat_card("🎭 Agentes", 
                                    f"{agent_stats['enabled_agents']}/{agent_stats['total_agents']}",
                                    "ativos"),
                self.create_stat_card("🎯 Intenções",
                                    str(len(self.intent_manager.list_intents())),
                                    "configuradas"),
                self.create_stat_card("📚 Contextos",
                                    str(len(self.context_manager.list_contexts())),
                                    "carregados"),
                self.create_stat_card("🔍 Documentos RAG",
                                    "0",
                                    "indexados"),
            ],
            columns=4
        )
        
        # Atividades recentes
        recent_activities = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("📋 Atividades Recentes", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text("Nenhuma atividade recente", color=ft.Colors.GREY_400)
                ]),
                padding=20
            )
        )
        
        # Ações rápidas
        quick_actions = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("⚡ Ações Rápidas", size=18, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        self.create_action_button("➕ Novo Agente", "agents"),
                        self.create_action_button("🔍 Testar Intenção", "intents"),
                        self.create_action_button("📥 Indexar RAG", "rag"),
                        self.create_action_button("🎨 Criar Skill", "skills"),
                    ], spacing=10, wrap=True)
                ]),
                padding=20
            )
        )
        
        self.content_area.content.controls.extend([
            ft.Text("Dashboard", size=30, weight=ft.FontWeight.BOLD),
            cards,
            ft.Row([recent_activities, quick_actions], expand=True)
        ])
    
    def create_stat_card(self, title: str, value: str, subtitle: str, icon_name: str = None) -> ft.Container:
        """Cria um card de estatística"""
        return ft.Container(
            col={"sm": 6, "md": 3},
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(name=icon_name, size=24, color=ft.Colors.CYAN) if icon_name else ft.Container(),
                            ft.Container(expand=True),
                            ft.Text(value, size=28, weight=ft.FontWeight.BOLD)
                        ]),
                        ft.Text(title, size=14, color=ft.Colors.GREY_400),
                        ft.Text(subtitle, size=11, color=ft.Colors.GREY_500)
                    ]),
                    padding=16
                )
            )
        )
    
    def create_action_button(self, text: str, page: str) -> ft.ElevatedButton:
        """Cria um botão de ação rápida"""
        return ft.ElevatedButton(
            content=ft.Text(text),
            on_click=lambda e: self.navigate_to(page)
        )
    
    def show_agents_page(self):
        """Página de gerenciamento de agentes"""
        agents = self.agent_manager.list_agents()
        
        # Título e botão de criar
        header = ft.Row([
            ft.Text("🤖 Agentes", size=30, weight=ft.FontWeight.BOLD),
            ft.Container(expand=True),
            ft.ElevatedButton(
                "➕ Novo Agente",
                on_click=self.show_create_agent_dialog
            )
        ])
        
        # Tabela de agentes
        agent_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Nome")),
                ft.DataColumn(ft.Text("Tipo")),
                ft.DataColumn(ft.Text("Prioridade")),
                ft.DataColumn(ft.Text("Triggers")),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Ações")),
            ],
            rows=[]
        )
        
        for agent in agents:
            # Badge de status
            status_badge = ft.Container(
                content=ft.Text("Ativo" if agent.enabled else "Inativo", size=12),
                bgcolor=ft.Colors.GREEN if agent.enabled else ft.Colors.GREY,
                border_radius=12,
                padding=ft.padding.symmetric(horizontal=12, vertical=4)
            )
            
            # Botões de ação (usando TextButton em vez de IconButton)
            actions = ft.Row([
                ft.TextButton("Editar", on_click=lambda e, a=agent: self.edit_agent(a)),
                ft.TextButton("Excluir", on_click=lambda e, a=agent: self.delete_agent(a)),
                ft.TextButton("Desabilitar" if agent.enabled else "Habilitar", 
                             on_click=lambda e, a=agent: self.toggle_agent(a))
            ], spacing=10)
            
            agent_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(agent.name)),
                    ft.DataCell(ft.Text(agent.type.value)),
                    ft.DataCell(ft.Text(agent.priority.name)),
                    ft.DataCell(ft.Text(", ".join(agent.triggers[:2]))),
                    ft.DataCell(status_badge),
                    ft.DataCell(actions),
                ])
            )
        
        self.content_area.content.controls = [header, agent_table]
    
    def show_create_agent_dialog(self, e):
        """Diálogo para criar novo agente"""
        name_field = ft.TextField(label="Nome do Agente", width=300)
        type_dropdown = ft.Dropdown(
            label="Tipo",
            options=[
                ft.dropdown.Option("custom", "Customizado"),
                ft.dropdown.Option("rag", "RAG Agent"),
                ft.dropdown.Option("crud", "CRUD Agent"),
            ],
            width=300
        )
        triggers_field = ft.TextField(label="Triggers (separados por vírgula)", width=300, 
                                       helper_text="Ex: create_crud, analyze")
        
        def on_create(e):
            name = name_field.value
            agent_type = type_dropdown.value
            triggers = [t.strip() for t in triggers_field.value.split(",")] if triggers_field.value else []
            
            if name:
                from flai.core.agents.agent_manager import AgentDefinition, AgentType, AgentPriority
                
                agent_def = AgentDefinition(
                    name=name,
                    description=f"Custom agent: {name}",
                    type=AgentType.CUSTOM,
                    module_path=f".flai.agents.custom.{name}.agent",
                    class_name=f"{name.capitalize()}Agent",
                    triggers=triggers
                )
                
                if self.agent_manager.add_agent(agent_def):
                    self.show_snackbar(f"Agente '{name}' criado!")
                    self.navigate_to("agents")
                else:
                    self.show_snackbar("Erro ao criar agente", is_error=True)
            
            dialog.open = False
            self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Criar Novo Agente"),
            content=ft.Column([name_field, type_dropdown, triggers_field], width=350, height=200),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.ElevatedButton("Criar", on_click=on_create)
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def show_intents_page(self):
        """Página de gerenciamento de intenções"""
        intents = self.intent_manager.list_intents()
        
        header = ft.Row([
            ft.Text("🎯 Intenções", size=30, weight=ft.FontWeight.BOLD),
            ft.Container(expand=True),
            ft.ElevatedButton(
                "➕ Nova Intenção",
                on_click=self.show_create_intent_dialog
            ),
            ft.ElevatedButton(
                "🧪 Testar Intenção",
                on_click=self.show_test_intent_dialog
            )
        ])
        
        # Cards de intenções
        intent_cards = ft.GridView(
            expand=True,
            runs_count=3,
            max_extent=350,
            spacing=10,
            run_spacing=10
        )
        
        for intent in intents:
            card = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(intent.name, size=16, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            ft.TextButton("Excluir", on_click=lambda e, i=intent: self.delete_intent(i.name))
                        ]),
                        ft.Text(intent.description, size=12, color=ft.Colors.GREY_400),
                        ft.Divider(height=1),
                        ft.Text(f"Padrões: {len(intent.patterns)}", size=11),
                        ft.Text(f"Keywords: {', '.join(intent.keywords[:3])}", size=11),
                        ft.Row([
                            ft.Text("✅ Ativo" if intent.enabled else "❌ Inativo", size=11)
                        ])
                    ]),
                    padding=12
                )
            )
            intent_cards.controls.append(card)
        
        self.content_area.content.controls = [header, intent_cards]
    
    def show_create_intent_dialog(self, e):
        """Diálogo para criar nova intenção"""
        name_field = ft.TextField(label="Nome da Intenção", width=350)
        desc_field = ft.TextField(label="Descrição", width=350, multiline=True)
        patterns_field = ft.TextField(label="Padrões Regex (um por linha)", width=350, multiline=True, min_lines=3)
        keywords_field = ft.TextField(label="Palavras-chave (separadas por vírgula)", width=350)
        
        def on_create(e):
            name = name_field.value
            description = desc_field.value
            patterns = [p.strip() for p in patterns_field.value.split('\n') if p.strip()]
            keywords = [k.strip() for k in keywords_field.value.split(',') if k.strip()]
            
            if name:
                from flai.core.intent.intent_manager import IntentDefinition, IntentPriority
                
                intent = IntentDefinition(
                    name=name,
                    description=description,
                    patterns=patterns,
                    keywords=keywords,
                    priority=IntentPriority.NORMAL
                )
                
                if self.intent_manager.add_intent(intent):
                    self.show_snackbar(f"Intenção '{name}' criada!")
                    self.navigate_to("intents")
                else:
                    self.show_snackbar("Erro ao criar intenção", is_error=True)
            
            dialog.open = False
            self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Criar Nova Intenção"),
            content=ft.Column([name_field, desc_field, patterns_field, keywords_field], 
                            width=400, height=450, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.ElevatedButton("Criar", on_click=on_create)
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def show_test_intent_dialog(self, e):
        """Diálogo para testar intenções"""
        text_field = ft.TextField(label="Texto para testar", width=400, multiline=True)
        result_field = ft.TextField(label="Resultado", width=400, multiline=True, read_only=True)
        
        def on_test(e):
            text = text_field.value
            if text:
                intent, entity = self.intent_manager.match_intent(text)
                fields = self.intent_manager.extract_fields(text)
                
                result = f"""
Intenção detectada: {intent or 'Nenhuma'}
Entidade: {entity or 'N/A'}
Campos: {', '.join(fields) if fields else 'Nenhum'}
"""
                result_field.value = result
                self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Testar Intenção"),
            content=ft.Column([text_field, result_field], width=450, height=300),
            actions=[
                ft.TextButton("Fechar", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.ElevatedButton("Testar", on_click=on_test)
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def show_contexts_page(self):
        """Página de gerenciamento de contextos"""
        contexts = self.context_manager.list_contexts()
        
        header = ft.Row([
            ft.Text("📚 Contextos", size=30, weight=ft.FontWeight.BOLD),
            ft.Container(expand=True),
            ft.ElevatedButton(
                "➕ Adicionar Contexto",
                on_click=self.show_add_context_dialog
            )
        ])
        
        # Lista de contextos
        context_list = ft.ListView(expand=True, spacing=10)
        
        for ctx in contexts:
            item = ft.Card(
                content=ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(ctx['name'], size=16, weight=ft.FontWeight.BOLD),
                            ft.Text(ctx['description'], size=12, color=ft.Colors.GREY_400),
                            ft.Row([
                                ft.Text(f"Tipo: {ctx['type']}", size=11),
                                ft.Text(f"Local: {ctx['location'][:50]}", size=11)
                            ], spacing=10)
                        ], expand=True),
                        ft.Column([
                            ft.TextButton("Atualizar", on_click=lambda e, id=ctx['id']: self.update_context(id)),
                            ft.TextButton("Indexar", on_click=lambda e, id=ctx['id']: self.index_context(id)),
                            ft.TextButton("Remover", on_click=lambda e, id=ctx['id']: self.delete_context(id))
                        ], alignment=ft.MainAxisAlignment.CENTER)
                    ]),
                    padding=12
                )
            )
            context_list.controls.append(item)
        
        self.content_area.content.controls = [header, context_list]
    
    def show_add_context_dialog(self, e):
        """Diálogo para adicionar contexto"""
        name_field = ft.TextField(label="Nome", width=350)
        desc_field = ft.TextField(label="Descrição", width=350)
        type_dropdown = ft.Dropdown(
            label="Tipo",
            options=[
                ft.dropdown.Option("git_repo", "Repositório Git"),
                ft.dropdown.Option("local_file", "Arquivo Local"),
                ft.dropdown.Option("url", "URL"),
                ft.dropdown.Option("project_code", "Código do Projeto"),
            ],
            width=350
        )
        location_field = ft.TextField(label="Localização (URL, caminho ou repo)", width=350)
        
        def on_add(e):
            name = name_field.value
            description = desc_field.value
            source_type = type_dropdown.value
            location = location_field.value
            
            if all([name, description, source_type, location]):
                if self.context_manager.add_context(
                    source_id=name.lower().replace(" ", "_"),
                    name=name,
                    description=description,
                    source_type=source_type,
                    location=location
                ):
                    self.show_snackbar(f"Contexto '{name}' adicionado!")
                    self.navigate_to("contexts")
                else:
                    self.show_snackbar("Erro ao adicionar contexto", is_error=True)
            
            dialog.open = False
            self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Adicionar Contexto"),
            content=ft.Column([name_field, desc_field, type_dropdown, location_field], 
                            width=400, height=350),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.ElevatedButton("Adicionar", on_click=on_add)
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def show_rag_page(self):
        """Página de gerenciamento RAG"""
        rag_stats = self.rag.get_stats()
        
        header = ft.Row([
            ft.Text("🔍 Gerenciamento RAG", size=30, weight=ft.FontWeight.BOLD),
            ft.Container(expand=True),
            ft.ElevatedButton(
                "📥 Indexar Projeto",
                on_click=self.index_project_rag
            ),
            ft.ElevatedButton(
                "🗑️ Limpar Índice",
                on_click=self.clear_rag_index
            )
        ])
        
        # Stats cards (sem ícones)
        stats_row = ft.ResponsiveRow([
            self.create_stat_card("📄 Documentos", str(rag_stats.get('total_documents', 0)), "indexados"),
            self.create_stat_card("📊 Chunks", str(rag_stats.get('total_chunks', 0)), "criados"),
            self.create_stat_card("💾 Tamanho", "N/A", "do índice"),
            self.create_stat_card("🕐 Última indexação", rag_stats.get('indexed_at', 'Nunca')[:10], ""),
        ], columns=4)
        
        # Status do RAG
        rag_status = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("📊 Status do RAG", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(f"LangChain disponível: {'✅' if rag_stats.get('is_available') else '❌'}"),
                    ft.Text(f"ChromaDB disponível: {'✅' if rag_stats.get('exists') else '❌'}"),
                    ft.Text(f"Caminho do índice: {rag_stats.get('path', 'N/A')}")
                ]),
                padding=20
            )
        )
        
        # Busca RAG
        search_field = ft.TextField(label="Buscar no código", hint_text="Digite sua pergunta...", expand=True)
        search_button = ft.ElevatedButton("🔍 Buscar")
        search_results = ft.Column(spacing=10)
        
        def on_search(e):
            query = search_field.value
            if query:
                results = self.rag.search(query, k=5)
                search_results.controls.clear()
                
                if results:
                    for result in results:
                        search_results.controls.append(
                            ft.Card(
                                content=ft.Container(
                                    content=ft.Column([
                                        ft.Text(f"📄 {Path(result['source']).name}", weight=ft.FontWeight.BOLD),
                                        ft.Text(f"Score: {(1 - result['score']):.2%}", size=11),
                                        ft.Text(result['content'][:300], size=12, color=ft.Colors.GREY_300),
                                    ]),
                                    padding=10
                                )
                            )
                        )
                else:
                    search_results.controls.append(ft.Text("Nenhum resultado encontrado"))
                
                self.page.update()
        
        search_button.on_click = on_search
        search_row = ft.Row([search_field, search_button])
        
        self.content_area.content.controls = [header, stats_row, rag_status, search_row, search_results]
    
    def index_project_rag(self, e):
        """Indexa o projeto para RAG"""
        self.show_snackbar("Indexando projeto...")
        
        def do_index():
            self.rag.rag.index_project(verbose=True)
            self.show_snackbar("Indexação concluída!")
            self.navigate_to("rag")
        
        import threading
        threading.Thread(target=do_index, daemon=True).start()
    
    def clear_rag_index(self, e):
        """Limpa o índice RAG"""
        if self.rag.rag.clear_index(verbose=True):
            self.show_snackbar("Índice RAG limpo!")
            self.navigate_to("rag")
    
    def show_mcp_page(self):
        """Página de configuração MCP"""
        header = ft.Row([
            ft.Text("🔌 MCP Servers", size=30, weight=ft.FontWeight.BOLD),
            ft.Container(expand=True),
            ft.ElevatedButton(
                "➕ Adicionar Servidor",
                on_click=self.show_add_mcp_dialog
            )
        ])
        
        mcp_list = ft.ListView(expand=True, spacing=10)
        mcp_list.controls.append(ft.Text("Em desenvolvimento..."))
        
        self.content_area.content.controls = [header, mcp_list]
    
    def show_add_mcp_dialog(self, e):
        """Diálogo para adicionar servidor MCP"""
        self.show_snackbar("Em desenvolvimento...")
    
    def show_settings_page(self):
        """Página de configurações gerais"""
        self.content_area.content.controls = [
            ft.Text("⚙️ Configurações", size=30, weight=ft.FontWeight.BOLD),
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Configurações Gerais", size=18, weight=ft.FontWeight.BOLD),
                        ft.Divider(),
                        ft.Text("Em desenvolvimento...")
                    ]),
                    padding=20
                )
            )
        ]
    
    # Ações auxiliares
    def show_snackbar(self, message: str, is_error: bool = False):
        """Mostra uma mensagem temporária"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED if is_error else ft.Colors.GREEN
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def toggle_agent(self, agent):
        """Habilita/desabilita um agente"""
        self.agent_manager.enable_agent(agent.name, not agent.enabled)
        self.navigate_to("agents")
    
    def delete_agent(self, agent):
        """Remove um agente"""
        def confirm(e):
            if self.agent_manager.delete_agent(agent.name):
                self.show_snackbar(f"Agente '{agent.name}' removido")
                self.navigate_to("agents")
            dialog.open = False
            self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Confirmar exclusão"),
            content=ft.Text(f"Tem certeza que deseja remover o agente '{agent.name}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.ElevatedButton("Excluir", on_click=confirm)
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def edit_agent(self, agent):
        """Edita um agente"""
        self.show_snackbar(f"Editar {agent.name} - Em desenvolvimento")
    
    def update_context(self, context_id: str):
        """Atualiza um contexto"""
        if self.context_manager.update_context(context_id, force=True):
            self.show_snackbar(f"Contexto atualizado!")
            self.navigate_to("contexts")
    
    def index_context(self, context_id: str):
        """Indexa um contexto para RAG"""
        if self.context_manager.index_context(context_id, verbose=True):
            self.show_snackbar(f"Contexto indexado!")
            self.navigate_to("contexts")
    
    def delete_context(self, context_id: str):
        """Remove um contexto"""
        def confirm(e):
            if self.context_manager.remove_context(context_id):
                self.show_snackbar(f"Contexto removido")
                self.navigate_to("contexts")
            dialog.open = False
            self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Confirmar exclusão"),
            content=ft.Text(f"Tem certeza que deseja remover este contexto?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.ElevatedButton("Excluir", on_click=confirm)
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def delete_intent(self, intent_name: str):
        """Remove uma intenção"""
        def confirm(e):
            if self.intent_manager.delete_intent(intent_name):
                self.show_snackbar(f"Intenção '{intent_name}' removida")
                self.navigate_to("intents")
            dialog.open = False
            self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Confirmar exclusão"),
            content=ft.Text(f"Tem certeza que deseja remover a intenção '{intent_name}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.ElevatedButton("Excluir", on_click=confirm)
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()