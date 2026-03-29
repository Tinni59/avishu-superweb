# Структура базы данных

Приложение использует **SQLite** через Flask-SQLAlchemy. URI по умолчанию:

`sqlite:///<корень_проекта>/instance/avishu.db`

Таблицы создаются при старте приложения (`db.create_all()` в `app.py`).

---

## Таблица `user`

Пользователи и роли (`flask_login`).

| Колонка   | Тип           | Ограничения        | Описание |
|-----------|---------------|--------------------|----------|
| `id`      | INTEGER       | PK, autoincrement  | Идентификатор |
| `email`   | VARCHAR(255)  | UNIQUE, NOT NULL, индекс | Email (логин) |
| `password`| VARCHAR(255)  | NOT NULL           | Хэш пароля (werkzeug) |
| `role`    | VARCHAR(32)   | NOT NULL, индекс   | Одна из: `client`, `franchisee`, `production` |

**Связи:** один ко многим с `order` (`user.id` ← `order.user_id`, каскадное удаление дочерних заказов при удалении пользователя — см. `models.py`).

---

## Таблица `order`

Заказы клиентов.

| Колонка        | Тип           | Ограничения | Описание |
|----------------|---------------|-------------|----------|
| `id`           | INTEGER       | PK          | Номер заказа |
| `user_id`      | INTEGER       | FK → `user.id`, NOT NULL, индекс | Владелец (клиент) |
| `product_name` | VARCHAR(255)  | NOT NULL    | Название изделия |
| `type`         | VARCHAR(32)   | NOT NULL    | Тип: `in_stock`, `preorder` |
| `status`       | VARCHAR(32)   | NOT NULL, default `created`, индекс | См. статусы ниже |
| `deadline`     | DATETIME      | NULL        | Срок (обязателен для `preorder`) |
| `created_at`   | DATETIME      | NOT NULL, default UTC now | Время создания |

### Значения `order.type`

- `in_stock` — в наличии  
- `preorder` — предзаказ (нужен `deadline`)

### Значения `order.status` (жизненный цикл)

Допустимые коды: `created`, `accepted`, `in_production`, `done`.

Типичные переходы (логика в `order_status.py`):

1. **Клиент** создаёт заказ → `created`.
2. **Франчайзи** принимает → `accepted` (только из `created`).
3. **Производство** → `in_production` (из `accepted`), затем `done` (из `in_production`).

---

## Таблица `catalog_product`

Опциональное хранение позиций витрины (альтернатива — только файлы в `static/`, см. `catalog.py` / `seed_catalog.py`).

| Колонка        | Тип           | Ограничения | Описание |
|----------------|---------------|-------------|----------|
| `id`           | INTEGER       | PK          | Внутренний id |
| `slug`         | VARCHAR(64)   | UNIQUE, NOT NULL, индекс | Стабильный ключ карточки |
| `name`         | VARCHAR(255)  | NOT NULL    | Название |
| `line`         | VARCHAR(128)  | NOT NULL, default | Линейка / коллекция |
| `product_type` | VARCHAR(32)   | NOT NULL, default `in_stock` | `in_stock` / `preorder` |
| `price`        | VARCHAR(64)   | NOT NULL    | Отображаемая цена (строка) |
| `detail`       | TEXT          | NULL        | Описание |
| `sort_order`   | INTEGER       | NOT NULL, default 0 | Порядок сортировки |
| `images_json`  | TEXT          | NOT NULL, default `[]` | JSON-массив URL путей к изображениям |

---

## Прочее

- Сессия корзины клиента хранится во **Flask session** (не в этих таблицах).
- JSON API заказов и события Socket.IO используют те же сущности `Order` / `User`; схема REST описана в коде `routes/orders_api.py`.
