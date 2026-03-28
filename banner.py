"""Баннер витрины: файлы в static/images/banner/.

Ожидаемые имена (любое расширение .jpg/.jpeg/.png/.webp):
  — в названии есть «Десктоп» или «desktop»
  — в названии есть «Мобил» или «mobile»

Если найден только один вариант, он используется и для мобильного, и для десктопа.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

BASE_DIR = Path(__file__).resolve().parent
BANNER_DIR = BASE_DIR / "static" / "images" / "banner"
ALLOWED_EXT = frozenset({".jpg", ".jpeg", ".png", ".webp"})


def _static_url(relative_under_static: str) -> str:
    rel = relative_under_static.replace("\\", "/").lstrip("/")
    return "/static/" + quote(rel)


def get_showcase_banner_urls() -> dict[str, str | None]:
    out: dict[str, str | None] = {"desktop": None, "mobile": None}
    if not BANNER_DIR.is_dir():
        return out

    for path in sorted(BANNER_DIR.iterdir()):
        if not path.is_file() or path.suffix.lower() not in ALLOWED_EXT:
            continue
        if path.name.startswith("."):
            continue
        stem = path.stem.casefold()
        rel = f"images/banner/{path.name}"
        url = _static_url(rel)
        if "десктоп" in stem or "desktop" in stem:
            out["desktop"] = url
        elif "мобил" in stem or "mobile" in stem:
            out["mobile"] = url

    if out["desktop"] and not out["mobile"]:
        out["mobile"] = out["desktop"]
    elif out["mobile"] and not out["desktop"]:
        out["desktop"] = out["mobile"]

    return out
