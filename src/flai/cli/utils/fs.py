from pathlib import Path
from typing import Any


def write_utf8(path: Path, content: Any) -> None:
    path.write_text(data=content, encoding="utf-8")


def read_utf8(path: Path) -> Any:
    return path.read_text(encoding="utf-8")
