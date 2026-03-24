import shutil
import subprocess
import platform
from flai.cli.console.console import console


def install_ollama() -> None:
    if shutil.which("ollama"):
        console.print("[info]Ollama já instalado[/info]")
        return

    os_type = platform.system()
    console.print(f"[info]Instalando Ollama para {os_type}...[/info]")

    try:
        if os_type == "Windows":
            ps_command = (
                "$url = 'https://ollama.com/download/OllamaSetup.exe'; "
                '$out = "$env:TEMP\\OllamaSetup.exe"; '
                "Invoke-WebRequest -Uri $url -OutFile $out; "
                "Start-Process -FilePath $out -ArgumentList '/silent' -Wait; "
                "Remove-Item $out"
            )

            console.print(
                "[info]Baixando e instalando silenciosamente (aguarde)...[/info]"
            )

            subprocess.run(["powershell", "-Command", ps_command], check=True)
            console.print(
                "[success]Ollama instalado com sucesso via PowerShell![/success]"
            )

        elif os_type in ["Linux", "Darwin"]:
            subprocess.run(
                "curl -fsSL https://ollama.com/install.sh | sh", shell=True, check=True
            )

    except subprocess.CalledProcessError as e:
        console.print(f"[error]Falha en la instalación automática: {e}[/error]")
        console.print(
            "[yellow]Intente instalar manualmente em: https://ollama.com[/yellow]"
        )
        raise


def pull_model(model_id: str) -> None:
    subprocess.run(["ollama", "pull", model_id], check=True)


def run_ollama(model: str, prompt: str) -> str:
    process = subprocess.run(
        ["ollama", "run", model],
        input=prompt,
        text=True,
        encoding="utf-8",  # ← ESSENCIAL
        errors="replace",  # ← evita crash
        capture_output=True,
    )

    if process.returncode != 0:
        raise RuntimeError(process.stderr)

    return process.stdout.strip()
