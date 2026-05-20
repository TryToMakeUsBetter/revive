from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Literal


Role = Literal["system", "user", "assistant"]


@dataclass
class Message:
    role: Role
    content: str

    def to_dict(self) -> dict:
        return asdict(self)


class LLM(ABC):
    @abstractmethod
    def chat(self, messages: list[Message], **kwargs) -> str:
        ...
