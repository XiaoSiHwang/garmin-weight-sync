"""
Filter configuration validation module.

Provides validation for the filter configuration in users.json.
"""

import logging
from typing import Dict, Any, Optional, List

from garmin.filter import SUPPORTED_FIELDS, FIELD_TYPES, FilterOperator

_LOGGER = logging.getLogger(__name__)


class FilterConfigError(Exception):
    """Exception raised for filter configuration errors."""

    pass


class FilterConfigValidator:
    """Validator for weight filter configuration."""

    # Valid operators
    VALID_OPERATORS = [op.value for op in FilterOperator]

    @staticmethod
    def validate(filter_config: Optional[Dict]) -> None:
        """
        Validate the filter configuration.

        Args:
            filter_config: The filter configuration dict to validate.

        Raises:
            FilterConfigError: If the configuration is invalid.
        """
        if filter_config is None:
            return

        # Check basic structure
        if not isinstance(filter_config, dict):
            raise FilterConfigError("Filter config must be a dictionary")

        # Check enabled field
        if "enabled" in filter_config:
            if not isinstance(filter_config["enabled"], bool):
                raise FilterConfigError("'enabled' must be a boolean (true or false)")

        # If not enabled, no further validation needed
        if not filter_config.get("enabled", True):
            return

        # Check conditions
        if "conditions" not in filter_config:
            raise FilterConfigError("'conditions' is required when filter is enabled")

        conditions = filter_config["conditions"]
        if not isinstance(conditions, list):
            raise FilterConfigError("'conditions' must be a list")

        if len(conditions) == 0:
            raise FilterConfigError("'conditions' must not be empty when filter is enabled")

        # Validate each condition
        for i, condition in enumerate(conditions):
            FilterConfigValidator._validate_condition(condition, i)

        # Validate logic
        logic = filter_config.get("logic", "and")
        if logic not in ["and", "or"]:
            raise FilterConfigError(f"'logic' must be 'and' or 'or', got: '{logic}'")

    @staticmethod
    def _validate_condition(condition: Dict, index: int) -> None:
        """
        Validate a single filter condition.

        Args:
            condition: The condition dict to validate.
            index: The condition index for error reporting.

        Raises:
            FilterConfigError: If the condition is invalid.
        """
        condition_prefix = f"Condition {index}"

        # Check required fields
        required_fields = ["field", "operator", "value"]
        for field in required_fields:
            if field not in condition:
                raise FilterConfigError(f"{condition_prefix}: missing required field '{field}'")

        # Validate field name
        field = condition["field"]
        if field not in SUPPORTED_FIELDS:
            supported_list = ", ".join(f"'{f}'" for f in SUPPORTED_FIELDS.keys())
            raise FilterConfigError(
                f"{condition_prefix}: unsupported field '{field}'. "
                f"Supported fields: {supported_list}"
            )

        # Validate operator
        operator = condition["operator"]
        if operator not in FilterConfigValidator.VALID_OPERATORS:
            operator_list = ", ".join(f"'{op}'" for op in FilterConfigValidator.VALID_OPERATORS)
            raise FilterConfigError(
                f"{condition_prefix}: unsupported operator '{operator}'. "
                f"Supported operators: {operator_list}"
            )

        # Validate value
        value = condition["value"]
        FilterConfigValidator._validate_value(field, operator, value, index)

    @staticmethod
    def _validate_value(field: str, operator: str, value: Any, index: int) -> None:
        """
        Validate the value for a condition.

        Args:
            field: The field name.
            operator: The operator.
            value: The value to validate.
            index: The condition index for error reporting.

        Raises:
            FilterConfigError: If the value is invalid.
        """
        condition_prefix = f"Condition {index}"
        expected_type = FIELD_TYPES.get(field)

        if expected_type is None:
            raise FilterConfigError(f"{condition_prefix}: unknown field '{field}'")

        # Special handling for 'between' operator
        if operator == "between":
            if not isinstance(value, list):
                raise FilterConfigError(
                    f"{condition_prefix}: 'between' operator requires a list with 2 values, "
                    f"got type '{type(value).__name__}'"
                )

            if len(value) != 2:
                raise FilterConfigError(
                    f"{condition_prefix}: 'between' operator requires exactly 2 values, "
                    f"got {len(value)}"
                )

            # Validate both values
            for i, v in enumerate(value):
                try:
                    expected_type(v)
                except (ValueError, TypeError):
                    type_name = expected_type.__name__
                    raise FilterConfigError(
                        f"{condition_prefix}: value {i+1} must be {type_name} for field '{field}', "
                        f"got: '{v}' (type: {type(v).__name__})"
                    )

            # Check that min <= max
            try:
                if float(value[0]) > float(value[1]):
                    raise FilterConfigError(
                        f"{condition_prefix}: for 'between' operator, first value must be "
                        f"less than or equal to second value, got: [{value[0]}, {value[1]}]"
                    )
            except (ValueError, TypeError) as e:
                raise FilterConfigError(f"{condition_prefix}: invalid range values: {e}")

        else:
            # Single value validation
            try:
                expected_type(value)
            except (ValueError, TypeError):
                type_name = expected_type.__name__
                raise FilterConfigError(
                    f"{condition_prefix}: value must be {type_name} for field '{field}', "
                    f"got: '{value}' (type: {type(value).__name__})"
                )
