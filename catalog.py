"""
Каталог витрины: обнаружение изображений в папках static (см. CATALOG_STATIC_DIRS).

Имена файлов: «Название 1.jpg», «Название 2.jpg», …
→ название товара: «Название» (без номера в конце)
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from urllib.parse import quote

BASE_DIR = Path(__file__).resolve().parent

# Папки относительно static/ (можно несколько)
CATALOG_STATIC_DIRS = (
    Path("images") / "catalog",
    Path("catalog images"),
)

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}

# Метаданные по slug (12 hex от названия)
PRODUCT_META: dict[str, dict] = {}

DEFAULT_META = {
    "line": "Коллекция",
    "type": "in_stock",
    "price": "—",
    "detail": "",
}


def _stable_id(name: str) -> str:
    return hashlib.md5(name.encode("utf-8")).hexdigest()[:12]


def _static_url(relative_under_static: Path) -> str:
    """URL для файла под static/: /static/... с кодированием."""
    parts = relative_under_static.parts
    encoded = "/".join(quote(p, safe="") for p in parts)
    return f"/static/{encoded}"


def discover_catalog_from_filesystem() -> list[dict]:
    """Группирует файлы «Имя N.ext» по «Имя», сортирует по N."""
    static_root = BASE_DIR / "static"
    stem_pat = re.compile(r"^(.+?)\s+(\d+)$")
    # name -> list of (num, relpath_from_static, filename)
    groups: dict[str, list[tuple[int, Path, str]]] = {}

    for sub in CATALOG_STATIC_DIRS:
        folder = static_root / sub
        if not folder.is_dir():
            continue
        for f in sorted(folder.iterdir()):
            if not f.is_file() or f.suffix.lower() not in ALLOWED_EXT:
                continue
            m = stem_pat.match(f.stem)
            if not m:
                continue
            name = m.group(1).strip()
            num = int(m.group(2))
            rel = sub / f.name
            groups.setdefault(name, []).append((num, rel, f.name))

    out: list[dict] = []
    for name in sorted(groups.keys()):
        items = sorted(groups[name], key=lambda x: x[0])
        rel_paths = [t[1] for t in items]
        if not rel_paths:
            continue
        pid = _stable_id(name)
        meta = {**DEFAULT_META, **PRODUCT_META.get(pid, {})}
        images = [_static_url(p) for p in rel_paths]
        out.append(
            {
                "id": pid,
                "name": name,
                "line": meta["line"],
                "type": meta["type"],
                "price": meta["price"],
                "detail": meta.get("detail") or f"{name}. Смотрите детали в карточке.",
                "images": images,
            }
        )
    return out


def get_catalog() -> list[dict]:
    """Сначала каталог из БД (если есть строки), иначе с диска."""
    try:
        from models import CatalogProduct

        from extensions import db

        rows = CatalogProduct.query.order_by(CatalogProduct.sort_order, CatalogProduct.id).all()
        if rows:
            return [r.to_catalog_dict() for r in rows]
    except Exception:
        pass

    return discover_catalog_from_filesystem()
