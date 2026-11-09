import os
from datetime import datetime

LOG_PATH = "flai/logs/flai.log"

os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

def log_event(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")