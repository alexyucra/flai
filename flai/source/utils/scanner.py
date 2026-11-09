from pathlib import Path

IGNORED_DIRS = {".venv", "__pycache__", ".git"}

def scan_project(project_root: Path):
    result = {
        "app": {},
        "configs": [],
    }

    app_dir = project_root / "app"
    configs_dir = project_root / "configs"

    if app_dir.exists():
        result["app"] = scan_dir(app_dir)

    if configs_dir.exists():
        result["configs"] = list_files(configs_dir)

    return result


def scan_dir(base: Path):
    structure = {}

    for item in base.iterdir():
        if item.name in IGNORED_DIRS:
            continue

        if item.is_dir():
            structure[item.name] = scan_dir(item)
        else:
            structure[item.name] = summarize_file(item)

    return structure


def list_files(base: Path):
    return [f.name for f in base.glob("*") if f.is_file()]


def summarize_file(path: Path, max_lines=30):
    try:
        lines = path.read_text(errors="ignore").splitlines()
        return "\n".join(lines[:max_lines])
    except Exception:
        return ""
