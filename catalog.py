"""
Каталог витрины: обнаружение изображений в static/images/catalog/
Имена файлов: «Название 1.jpg», «Название 2.jpg», «Название 3.jpg»
→ название товара: «Название» (без цифр в конце)
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CATALOG_IMG_DIR = BASE_DIR / "static" / "images" / "catalog"
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}

# Метаданные по slug (12 hex от названия) — дополняйте под свои товары
PRODUCT_META: dict[str, dict] = {}

DEFAULT_META = {
    "line": "Коллекция",
    "type": "in_stock",
    "price": "—",
    "detail": "",
}


def _stable_id(name: str) -> str:
    return hashlib.md5(name.encode("utf-8")).hexdigest()[:12]


def discover_catalog_from_filesystem() -> list[dict]:
    """Группирует файлы «Имя N.ext» по «Имя», сортирует по N."""
    if not CATALOG_IMG_DIR.is_dir():
        return []

    stem_pat = re.compile(r"^(.+?)\s+(\d+)$")
    groups: dict[str, list[tuple[int, str]]] = {}

    for f in sorted(CATALOG_IMG_DIR.iterdir()):
        if not f.is_file() or f.suffix.lower() not in ALLOWED_EXT:
            continue
        m = stem_pat.match(f.stem)
        if not m:
            continue
        name = m.group(1).strip()
        num = int(m.group(2))
        groups.setdefault(name, []).append((num, f.name))

    out: list[dict] = []
    for name in sorted(groups.keys()):
        items = sorted(groups[name], key=lambda x: x[0])
        filenames = [fn for _, fn in items]
        if not filenames:
            continue
        pid = _stable_id(name)
        meta = {**DEFAULT_META, **PRODUCT_META.get(pid, {})}
        images = [f"/static/images/catalog/{fn}" for fn in filenames]
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

        rows = (
            CatalogProduct.query.order_by(CatalogProduct.sort_order, CatalogProduct.id).all()
        )
        if rows:
            return [r.to_catalog_dict() for r in rows]
    except Exception:
        pass

    return discover_catalog_from_filesystem()
