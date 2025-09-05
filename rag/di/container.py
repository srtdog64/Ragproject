# di/container.py
from __future__ import annotations
from typing import Any, Callable, Dict

class Container:
    def __init__(self):
        self._factories: Dict[str, Callable[[Container], Any]] = {}

    def register(self, key: str, factory: Callable[[Any], Any]) -> None:
        self._factories[key] = factory

    def resolve(self, key: str) -> Any:
        if key not in self._factories:
            raise KeyError(f"Factory not found: {key}")
        return self._factories[key](self)
