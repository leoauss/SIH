"""Single-window view switching. No extra desktop windows."""

from typing import Callable, Dict, Optional

import tkinter as tk


class Navigation:
    def __init__(self, container: tk.Widget):
        self.container = container
        self._factories: Dict[str, Callable] = {}
        self._current = None
        self._name = ""

    def register(self, name: str, factory: Callable) -> None:
        self._factories[name] = factory

    @property
    def current_name(self) -> str:
        return self._name

    def show(self, name: str, **kwargs) -> None:
        factory = self._factories.get(name)
        if factory is None:
            raise KeyError("Unknown view: %s" % name)
        if self._current is not None:
            self._current.destroy()
        self._current = factory(self.container, **kwargs)
        self._current.pack(fill="both", expand=True)
        self._name = name
