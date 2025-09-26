import contextvars
from typing import Any

DATA = contextvars.ContextVar[dict[str, Any] | None]("DATA", default=None)


def get_data():
    result = DATA.get()
    return result


def set_data(data: dict[str, Any]):
    return DATA.set(data)
