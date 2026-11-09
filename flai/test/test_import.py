# test_imports.py
"""Testa se todos os imports da FASE 2 funcionam"""

def test_imports():
    print("🔍 Testando imports da FASE 2...\n")
    
    errors = []
    
    # Agents
    try:
        from flai.core.agents.router_agent import RouterAgent
        print("  ✅ core.agents.router_agent")
    except Exception as e:
        errors.append(f"core.agents.router_agent: {e}")
    
    try:
        from flai.core.agents.crud_agent import CRUDAgent
        print("  ✅ core.agents.crud_agent")
    except Exception as e:
        errors.append(f"core.agents.crud_agent: {e}")
    
    try:
        from flai.core.agents.project_agent import ProjectAgent
        print("  ✅ core.agents.project_agent")
    except Exception as e:
        errors.append(f"core.agents.project_agent: {e}")
    
    # Intent
    try:
        from flai.core.intent.parser import IntentParser
        print("  ✅ core.intent.parser")
    except Exception as e:
        errors.append(f"core.intent.parser: {e}")
    
    try:
        from flai.core.intent.patterns import IntentPatterns
        print("  ✅ core.intent.patterns")
    except Exception as e:
        errors.append(f"core.intent.patterns: {e}")
    
    # Generators
    # try:
    #     from flai.core.generators.crud_generator import CRUDGenerator
    #     print("  ✅ core.generators.crud_generator")
    # except Exception as e:
    #     errors.append(f"core.generators.crud_generator: {e}")
    
    # try:
    #     from flai.core.generators.form_generator import FormGenerator
    #     print("  ✅ core.generators.form_generator")
    # except Exception as e:
    #     errors.append(f"core.generators.form_generator: {e}")
    
    # Executors
    try:
        from flai.core.executors.fleting_executor import FletingExecutor
        print("  ✅ core.executors.fleting_executor")
    except Exception as e:
        errors.append(f"core.executors.fleting_executor: {e}")
    
    # REPL
    try:
        from ia.source.repl import FLAIREPL
        print("  ✅ cli.repl")
    except Exception as e:
        errors.append(f"cli.repl: {e}")
    
    print("\n" + "="*50)
    if errors:
        print(f"❌ {len(errors)} erros encontrados:")
        for err in errors:
            print(f"   • {err}")
    else:
        print("✅ TODOS OS IMPORTS FUNCIONAM!")
    
    return len(errors) == 0

if __name__ == "__main__":
    test_imports()