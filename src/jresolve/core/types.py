from enum import Enum
from typing import TypeVar, Any, Generic

T = TypeVar("T")

FieldResult = tuple[Any | None, Exception | None]
FieldResults = tuple[dict[str, Any | None], dict[str, Exception | None]]


class ResolutionMode(Enum):
    FAIL_FAST = "fail_fast"
    COLLECT_ALL = "collect_all"
    PARTIAL = "partial"


class JqMode(Enum):
    ONE = 'one'
    MANY = 'many'


class ResolutionResult(Generic[T]):
    def __init__(
            self,
            value: T | None,
            errors: dict[str, Exception]
    ):
        self.value = value
        self.errors = errors

    @property
    def is_success(self) -> bool:
        return self.value is not None and not self.errors

    @property
    def is_partial(self) -> bool:
        return self.value is not None and bool(self.errors)

    @property
    def is_failure(self) -> bool:
        return self.value is None and bool(self.errors)

    def __repr__(self):
        return f"ResolutionResult(value={self.value}, errors={self.errors})"
