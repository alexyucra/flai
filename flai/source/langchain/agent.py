def run_agent(user_input: str):
    cfg = load_config()
    limits = cfg["limits"]

    monitor = IAMonitor()

    try:
        llm = get_llm(monitor)

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_input),
        ]

        response = llm.invoke(messages)

    except Exception as e:
        error_text = str(e).lower()

        # 🔐 Tratamento explícito de API KEY
        if "invalid api key" in error_text or "invalid_api_key" in error_text or "401" in error_text:
            msg = (
                "\n❌ IA não configurada corretamente\n\n"
                "A chave da IA (API Key) não foi encontrada ou é inválida.\n\n"
                "👉 Como resolver:\n"
                "1. Crie uma chave gratuita em: https://console.groq.com\n"
                "2. Crie o arquivo: core/ia/.env\n"
                "3. Adicione a linha:\n\n"
                "   GROQ_API_KEY=sua_chave_aqui\n\n"
                "💡 A Groq é gratuita e não exige cartão de crédito."
            )

            log_event("ERRO: API KEY inválida ou ausente")
            return msg, None, None

        # ❌ Qualquer outro erro inesperado
        log_event(f"ERRO inesperado: {str(e)}")
        return f"❌ Erro inesperado na IA: {e}", None, None

    # ✅ Sucesso
    stats = monitor.summary()
    daily_total = add_daily_usage(stats["total_tokens"])

    log_event(
        f"REQ={stats['requests']} "
        f"TOKENS={stats['total_tokens']} "
        f"DAILY={daily_total}"
    )

    warn = None
    percent = (daily_total / limits["daily_tokens"]) * 100

    if percent >= limits["warn_at_percent"]:
        warn = f"⚠ Uso alto de IA hoje: {int(percent)}% do limite diário"

    return response.content, stats, warn
