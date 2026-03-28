"""
Одноразовый импорт каталога в БД из static/images/catalog/

Запуск: python seed_catalog.py
(из корня проекта, после pip install -r requirements.txt)

Правила имён файлов: «Название 1.jpg», «Название 2.jpg», …
Папки: static/images/catalog/ и/или static/catalog images/
Название товара в БД — «Название» (без номера).
Если таблица уже заполнена — скрипт выходит без изменений.
"""

import json

from app import create_app
from catalog import discover_catalog_from_filesystem
from extensions import db
from models import CatalogProduct


def main():
    app = create_app()
    with app.app_context():
        db.create_all()

        if CatalogProduct.query.first():
            print("catalog_product уже содержит данные. Очистите таблицу вручную или удалите строки, затем запустите снова.")
            return

        items = discover_catalog_from_filesystem()
        if not items:
            print("Нет товаров: положите изображения в static/images/catalog/ (имена вида «Рубашка EVO 1.jpg»).")
            return

        for i, item in enumerate(items):
            row = CatalogProduct(
                slug=item["id"],
                name=item["name"],
                line=item["line"],
                product_type=item["type"],
                price=item["price"],
                detail=item.get("detail") or "",
                sort_order=i,
                images_json=json.dumps(item.get("images") or [], ensure_ascii=False),
            )
            db.session.add(row)

        db.session.commit()
        print(f"Импортировано позиций: {len(items)}")
        for it in items:
            print(f"  - {it['name']} ({len(it.get('images') or [])} фото)")


if __name__ == "__main__":
    main()
