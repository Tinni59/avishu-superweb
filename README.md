# AVISHU

Веб-приложение на Flask: витрина для клиента, зона франчайзи, очередь производства, заказы в реальном времени (Socket.IO).

## Требования

- Python 3.10+ (рекомендуется 3.12)
- [pip](https://pip.pypa.io/)

## Установка и запуск

```bash
cd /path/to/project
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

База SQLite создаётся автоматически при первом запуске в каталоге `instance/` (файл `instance/avishu.db`).

### Запуск сервера разработки

```bash
python main.py
```

Либо через CLI Flask:

```bash
flask --app main run --debug
```

По умолчанию приложение слушает `http://127.0.0.1:5000`. Для Socket.IO используется тот же процесс (`socketio.run` в `main.py`).

### Тестовые пользователи

```bash
python seed.py
```

Создаются три учётные записи (если их ещё нет):

| Роль        | Email                     | Пароль        |
|-------------|---------------------------|---------------|
| client      | client@avishu.app         | client123     |
| franchisee  | franchisee@avishu.app     | franchisee123 |
| production  | production@avishu.app     | production123 |

Регистрация новых пользователей доступна в интерфейсе (можно выбрать роль).

### Каталог витрины

- Картинки можно положить в `static/images/catalog/` и/или `static/catalog images/` (имена вида «Название 1.jpg», «Название 2.jpg»).
- Опционально: импорт в таблицу БД — `python seed_catalog.py` (см. комментарии в скрипте).

### Баннер на главной (клиент)

Файлы в `static/images/banner/`: в имени должны встречаться подстроки **Десктоп** / **desktop** и **Мобил** / **mobile** (расширения `.jpg`, `.jpeg`, `.png`, `.webp`).

### Язык интерфейса

Переключатель в шапке: cookie `av_lang` (`ru` / `kk`).

## Структура проекта (кратко)

| Путь | Назначение |
|------|------------|
| `main.py` | Точка входа, запуск с Socket.IO |
| `app.py` | Фабрика приложения Flask |
| `models.py` | Модели SQLAlchemy |
| `routes/` | Blueprint’ы (auth, client, franchisee, production, API) |
| `templates/` | Jinja2-шаблоны |
| `static/` | CSS, JS, изображения |
| `instance/` | SQLite и прочие данные экземпляра (не коммитить БД в проде без необходимости) |

Описание таблиц и связей — в файле **[DATABASE.md](DATABASE.md)**.
