import os
import yaml
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from core.ia.langchain.monitor import IAMonitor

# 🔥 caminho absoluto baseado neste arquivo
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

CONFIG_PATH = os.path.join(BASE_DIR, "flai.yml")
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)

def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(
            f"Arquivo de configuração não encontrado: {CONFIG_PATH}"
        )

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_llm(monitor: IAMonitor | None = None):
    cfg = load_config()
    ia = cfg["ia"]

    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model=ia["model"],
        temperature=ia.get("temperature", 0.2),
        max_tokens=ia.get("max_tokens", 800),
        callbacks=[monitor] if monitor else []
    )
