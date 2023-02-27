from typing import List

__all__: List[str] = [
    "EventDispatcherException",
    "BindError",
    "InvalidOptionError",
]


class EventDispatcherException(Exception):
    pass


class BindError(EventDispatcherException):
    pass


class InvalidOptionError(EventDispatcherException):
    def __init__(self, value: str, options: List[str]) -> None:
        self.value = value
        self.options = options

    def __str__(self) -> str:
        return (
            f"'{self.value}' is not one of the following allowed options:"
            f"{[i for i in self.options]}"
            )
