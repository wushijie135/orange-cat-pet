import base64

from .config import app_root, writable_root
from .embedded import ASSETS_B64

NAMES = ("idle", "blink", "talk", "happy", "sleep")
_assets_dir = None


def _ensure_dir():
    builtin = app_root() / "assets"
    if all((builtin / f"{name}.png").exists() for name in NAMES):
        return builtin
    fallback = writable_root() / "assets"
    fallback.mkdir(parents=True, exist_ok=True)
    for name in NAMES:
        target = fallback / f"{name}.png"
        if not target.exists():
            target.write_bytes(base64.b64decode(ASSETS_B64[name]))
    return fallback


def assets_dir():
    global _assets_dir
    if _assets_dir is None:
        _assets_dir = _ensure_dir()
    return _assets_dir


def asset_path(name: str):
    return assets_dir() / f"{name}.png"
