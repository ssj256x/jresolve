from abc import ABC, abstractmethod
from typing import Any, Callable

import jq

from .transform import Transform
from .types import JqMode


class Resolver(ABC):
    @abstractmethod
    def resolve(self, data: dict) -> Any | None:
        pass


class Pipeline(Resolver):
    def __init__(
            self,
            base: Resolver,
            transforms: list[Transform]
    ):
        self.base = base
        self.transforms = transforms

    def resolve(self, data: dict):
        value = self.base.resolve(data)

        for t in self.transforms:
            value = t.apply(value)

        return value


class Jq(Resolver):
    def __init__(
            self,
            expression: str,
            *,
            mode: JqMode = JqMode.ONE,
            required: bool = False
    ):
        self.expression = expression
        self.mode = mode
        self.required = required
        self.program = jq.compile(expression)

    def resolve(self, data: dict) -> Any | None:
        result = self.program.input_value(data).all()

        if not result:
            return None

        return result[0] if self.mode == JqMode.ONE else result

    def __repr__(self):
        return f'Jq({self.expression})'


class Computed(Resolver):
    def __init__(
            self,
            fn: Callable[[dict], Any],
            *,
            description: str = ""
    ):
        self.fn = fn
        self.description = description

    def resolve(self, data: dict):
        return self.fn(data)

    def __repr__(self):
        return f"Computed({self.fn.__name__})"
