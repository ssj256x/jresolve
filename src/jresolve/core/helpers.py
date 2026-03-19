from typing import get_origin, get_args

from pydantic import ValidationError

from .resolver import Resolver, Pipeline
from .transform import Transform
from ..exceptions import ResolutionError


def build_pipeline_from_field(field) -> Resolver | None:
    base_resolver: Resolver | None = None
    transforms: list[Transform] = []

    for meta in field.metadata:
        # TODO : Try using match-case here
        if isinstance(meta, Resolver):
            base_resolver = meta
        elif isinstance(meta, Transform):
            transforms.append(meta)

    if base_resolver is None:
        return None

    return Pipeline(base_resolver, transforms) if transforms else base_resolver


def is_jq_model(_type) -> bool:
    from .model import JqModel
    return isinstance(_type, type) and issubclass(_type, JqModel)


def is_list_of_jq_model(tp):
    return (
            get_origin(tp) is list
            and is_jq_model(get_args(tp)[0])
    )


def convert_pydantic_errors(e: ValidationError) -> dict[str, Exception]:
    errors = {}

    for err in e.errors():
        path = ".".join(str(p) for p in err["loc"])
        message = err["msg"]

        errors[path] = ResolutionError(err)

    return errors