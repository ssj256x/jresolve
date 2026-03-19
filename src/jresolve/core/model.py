from typing import Any, get_args

from pydantic import BaseModel, ValidationError

from .helpers import is_jq_model, build_pipeline_from_field, is_list_of_jq_model, convert_pydantic_errors
from .resolver import Resolver
from .types import ResolutionMode, ResolutionResult, FieldResults, FieldResult


class JqModel(BaseModel):
    """
    The model class to define resolutions, transformation, etc. from a give json.
    Usage:

    ```python

    user_json = '''
        {
            "name": "John Doe"
            "address": {
                "street_name": "123-ABC Street"
                "Country": "Country Name"
                "State": "State Name"
            },
            "age": 20
            "email": abc@xyz.com
        }
    '''

    class UserNameAge(JqModel):
        name: Annotated[str, Jq(".name"), Transform(str.upper)]
        age: Annotated[int, Jq(".age")]

    user_name_age = UserNameAge.from_json(user_json)
    ```

    Resolution flow

    from_json
      → _resolve_fields
          → _resolve_field (for each field)
              → _resolve_with_resolver OR _resolve_nested_model
                  → (optional) _resolve_list_items
      → _construct_model

      Resolution flow with above example

      from_json
      ↓
    _resolve_fields
      ↓
    _resolve_field (name)
      ↓
    _resolve_with_resolver
      ↓
    Pipeline(Jq → Transform)
      ↓
    value = "SANJEET"

    _resolve_field (age)
      ↓
    Jq
      ↓
    value = 25

    _resolve_fields done
      ↓
    _construct_model
      ↓
    User(name="SANJEET", age=25)

    TODO:
	- Add step-by-step tracing logs
	- Add debug mode (print pipeline execution)
	- Add async resolution
	- Add performance optimizations
    """

    @classmethod
    def from_json(
            cls,
            data: dict[str, Any],
            *,
            mode: ResolutionMode = ResolutionMode.COLLECT_ALL
    ) -> ResolutionResult["JqModel"]:

        values, errors = cls._resolve_fields(data, mode)

        try:
            if mode == ResolutionMode.PARTIAL:
                model = cls.model_construct(**values)
            else:
                model = cls(**values)

        except ValidationError as e:
            pydantic_errors = convert_pydantic_errors(e)

            # 🔥 merge errors
            errors.update(pydantic_errors)

            if mode != ResolutionMode.PARTIAL:
                return ResolutionResult(None, errors)

            # In PARTIAL → still construct model
            model = cls.model_construct(**values)

        return ResolutionResult(model, errors)

    @classmethod
    def _resolve_fields(
            cls,
            data: dict[str, Any],
            mode: ResolutionMode
    ) -> FieldResults:
        """
        Goes over all the fields of the model, resolves each field and collects the
        values or errors based on the resolution
        :param data: The `json` to be resolved from
        :return: Resolved fields or error for fields during resolution
        """
        values: dict[str, Any] = {}
        errors: dict[str, Exception] = {}

        for field_name, field in cls.model_fields.items():
            value, error = cls._resolve_field(field_name, field, data, mode)

            if error:
                errors[field_name] = error
                if mode == ResolutionMode.FAIL_FAST:
                    return values, errors
                continue

            values[field_name] = value

        return values, errors

    @classmethod
    def _resolve_field(
            cls,
            field_name: str,
            field,
            data: dict[str, Any],
            mode: ResolutionMode
    ) -> FieldResult:
        field_type = field.annotation
        resolver = build_pipeline_from_field(field)
        try:
            # Case 1: Resolver Exists
            if resolver:
                return cls._resolve_with_resolver(field_name, field_type, resolver, data, mode)

            # Case 2: Nested Model
            if is_jq_model(field_type):
                return cls._resolve_nested_model(field_name, field_type, data, mode)

            return None, None
        except Exception as e:
            return None, e

    @classmethod
    def _resolve_with_resolver(
            cls,
            field_name: str,
            field_type,
            resolver: Resolver,
            data: dict[str, Any],
            mode: ResolutionMode
    ) -> FieldResult:
        value = resolver.resolve(data)

        if is_list_of_jq_model(field_type) and value is not None:
            return cls._resolve_list_items(field_name, field_type, value, mode)

        return value, None

    @classmethod
    def _resolve_list_items(
            cls,
            field_name: str,
            field_type,
            items: list,
            mode: ResolutionMode
    ) -> FieldResult:
        model_cls = get_args(field_type)[0]

        resolved_items = []
        errors = {}

        for idx, item in enumerate(items):
            result = model_cls.from_json(item, mode=mode)

            if result.is_failure:
                errors[f"{field_name}[{idx}]"] = result.errors
            else:
                resolved_items.append(result.value)

                if result.is_partial:
                    errors[f"{field_name}[{idx}]"] = result.errors

        if errors and mode != ResolutionMode.PARTIAL:
            return None, Exception(errors)

        return resolved_items, None

    @classmethod
    def _resolve_nested_model(
            cls,
            field_name: str,
            model_cls,
            data: dict[str, Any],
            mode: ResolutionMode
    ) -> FieldResult:
        result = model_cls.from_json(data, mode=mode)

        if result.is_failure:
            return None, Exception(result.errors)

        return result.value, None
