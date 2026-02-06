from typing import Any

from abc import ABC, abstractmethod


class BaseGraph(ABC):
    @abstractmethod
    def invoke(self, messages: list[dict[str, str]], user_profile: dict[str, Any]) -> str:
        pass