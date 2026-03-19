from typing import Callable, Any


class Transform:
    def __init__(
            self,
            fn,
            description: str = ""
    ):
        self.fn = fn
        self.description = description or fn.__name__

    def apply(self, data) -> Any:
        return self.fn(data)

    def __repr__(self):
        return f"Transform({self.fn.__name__})"
