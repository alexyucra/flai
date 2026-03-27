import gettext
import locale

from flai import DOMAIN, LOCALE_PATH

_t = gettext.gettext

locale.setlocale(locale.LC_ALL, "")


def tr(message: str) -> str:
    return _t(message)


def get_system_lang() -> str:
    """Detect the system language code (e.g., 'es', 'en')."""
    try:
        lang_code, _ = locale.getlocale()
        if not lang_code or lang_code in ["C", "POSIX"]:
            return "en"
        return lang_code.split("_")[0]
    except Exception:
        pass
    return "en"


def set_language(lang: str | None = None) -> None:
    global _t
    selected_lang = (
        lang if lang and lang.strip() not in ["C", "POSIX"] else get_system_lang()
    )
    translation = gettext.translation(
        domain=DOMAIN, localedir=LOCALE_PATH, languages=[selected_lang], fallback=True
    )
    translation.install()
    _t = translation.gettext


__all__ = ["tr", "set_language"]
