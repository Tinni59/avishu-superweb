"""Строгие правила переходов статусов заказов."""

ORDER_TYPES = ("in_stock", "preorder")
ORDER_STATUSES = ("created", "accepted", "in_production", "done")

# Франчайзи: created → accepted → in_production
_FRANCHISEE_EDGES = {
    "created": frozenset({"accepted"}),
    "accepted": frozenset({"in_production"}),
}

# Производство: accepted → in_production → done (без пропуска шага)
_PRODUCTION_EDGES = {
    "accepted": frozenset({"in_production"}),
    "in_production": frozenset({"done"}),
}


def validate_new_order(order_type: str, deadline):
    """preorder требует дедлайн; in_stock — дедлайн не обязателен."""
    if order_type not in ORDER_TYPES:
        return False, "Некорректный тип заказа."
    if order_type == "preorder" and deadline is None:
        return False, "Для предзаказа укажите дедлайн."
    return True, None


def next_statuses_for_franchisee(current: str) -> frozenset:
    return _FRANCHISEE_EDGES.get(current, frozenset())


def next_statuses_for_production(current: str) -> frozenset:
    return _PRODUCTION_EDGES.get(current, frozenset())


def is_valid_franchisee_transition(current: str, new: str) -> bool:
    if new not in ORDER_STATUSES:
        return False
    return new in _FRANCHISEE_EDGES.get(current, frozenset())


def is_valid_production_transition(current: str, new: str) -> bool:
    if new not in ORDER_STATUSES:
        return False
    return new in _PRODUCTION_EDGES.get(current, frozenset())
