from typing import Callable


def log_all_methods(decorator: Callable) -> Callable:
    def decorate(cls: type) -> type:
        for attr in cls.__dict__:
            if callable(getattr(cls, attr)) and not attr.startswith("_"):
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls
    return decorate