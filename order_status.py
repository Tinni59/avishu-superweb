from i18n import gettext

ORDER_TYPES = ("in_stock", "preorder")
ORDER_STATUSES = ("created", "accepted", "in_production", "done")

_FRANCHISEE_EDGES = {
    "created": frozenset({"accepted"}),
}

_PRODUCTION_EDGES = {
    "accepted": frozenset({"in_production"}),
    "in_production": frozenset({"done"}),
}


def validate_new_order(order_type: str, deadline, locale: str = "ru"):
    if order_type not in ORDER_TYPES:
        return False, gettext(locale, "err_invalid_order_type")
    if order_type == "preorder" and deadline is None:
        return False, gettext(locale, "err_preorder_deadline")
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
