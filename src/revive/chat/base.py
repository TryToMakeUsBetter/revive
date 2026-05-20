from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable


@dataclass
class IncomingMessage:
    sender_id: str
    sender_name: str
    sender_account: str | None
    text: str
    is_group: bool
    group_name: str | None
    is_at_me: bool


MessageHandler = Callable[[IncomingMessage], None]


class ChatClient(ABC):
    @abstractmethod
    def login(self) -> None:
        ...

    @abstractmethod
    def register_handler(self, handler: MessageHandler) -> None:
        ...

    @abstractmethod
    def send_text(self, text: str, to_id: str) -> None:
        ...

    @abstractmethod
    def run(self) -> None:
        ...
