"""
Weight data filter module for Garmin sync.

Provides filtering functionality based on various health metrics like weight,
BMI, body fat percentage, etc.
"""

import logging
from enum import Enum
from typing import List, Dict, Any, Optional, Union

_LOGGER = logging.getLogger(__name__)


class FilterOperator(Enum):
    """Supported comparison operators for filtering."""
    EQ = "eq"          # Equal to
    NE = "ne"          # Not equal to
    GT = "gt"          # Greater than
    GTE = "gte"        # Greater than or equal to
    LT = "lt"          # Less than
    LTE = "lte"        # Less than or equal to
    BETWEEN = "between"  # Within range (inclusive)


# Mapping from config field names to data dictionary keys
SUPPORTED_FIELDS = {
    "Weight": "Weight",
    "BMI": "BMI",
    "BodyFat": "BodyFat",
    "BodyWater": "BodyWater",
    "BoneMass": "BoneMass",
    "MetabolicAge": "MetabolicAge",
    "MuscleMass": "MuscleMass",
    "VisceralFat": "VisceralFat",
    "BasalMetabolism": "BasalMetabolism",
}

# Expected field types for validation
FIELD_TYPES = {
    "Weight": float,
    "BMI": float,
    "BodyFat": float,
    "BodyWater": float,
    "BoneMass": float,
    "MetabolicAge": int,
    "MuscleMass": float,
    "VisceralFat": int,
    "BasalMetabolism": int,
}


def evaluate_condition(data_point: Dict, condition: Dict) -> bool:
    """
    Evaluate a single filter condition against a data point.

    Args:
        data_point: A single weight data point dictionary.
        condition: A filter condition dict with 'field', 'operator', and 'value' keys.

    Returns:
        True if the condition matches, False otherwise.
    """
    field = condition.get("field")
    operator = condition.get("operator")
    value = condition.get("value")

    # Validate field name
    if field not in SUPPORTED_FIELDS:
        raise ValueError(f"Unsupported field: {field}")

    # Get the data value
    data_key = SUPPORTED_FIELDS[field]
    data_value = data_point.get(data_key)

    # Handle missing values
    if data_value is None:
        _LOGGER.debug(f"Field '{data_key}' not found in data point")
        return False

    # Evaluate based on operator
    try:
        if operator == FilterOperator.EQ.value:
            return abs(float(data_value) - float(value)) < 0.001

        if operator == FilterOperator.NE.value:
            return abs(float(data_value) - float(value)) >= 0.001

        if operator == FilterOperator.GT.value:
            return float(data_value) > float(value)

        if operator == FilterOperator.GTE.value:
            return float(data_value) >= float(value)

        if operator == FilterOperator.LT.value:
            return float(data_value) < float(value)

        if operator == FilterOperator.LTE.value:
            return float(data_value) <= float(value)

        if operator == FilterOperator.BETWEEN.value:
            if not isinstance(value, list) or len(value) != 2:
                raise ValueError(f"'between' operator requires a list of 2 values, got: {value}")
            min_val, max_val = float(value[0]), float(value[1])
            return min_val <= float(data_value) <= max_val

        raise ValueError(f"Unsupported operator: {operator}")

    except (ValueError, TypeError) as e:
        _LOGGER.warning(f"Failed to evaluate condition {field} {operator} {value}: {e}")
        return False


def apply_filter(weights: List[Dict], filter_config: Dict) -> List[Dict]:
    """
    Apply filter rules to weight data.

    Args:
        weights: List of weight data dictionaries.
        filter_config: Filter configuration dict with 'enabled', 'conditions', and 'logic' keys.

    Returns:
        Filtered list of weight data.
    """
    if not filter_config or not filter_config.get("enabled"):
        return weights

    conditions = filter_config.get("conditions", [])
    logic = filter_config.get("logic", "and").lower()

    if not conditions:
        _LOGGER.debug("Filter enabled but no conditions specified, returning all data")
        return weights

    # Validate logic
    if logic not in ("and", "or"):
        _LOGGER.warning(f"Invalid logic '{logic}', defaulting to 'and'")
        logic = "and"

    total_count = len(weights)
    filtered_weights = []

    # Log filter details
    _LOGGER.info(f"Applying weight filter with {len(conditions)} condition(s) using '{logic.upper()}' logic")
    for i, cond in enumerate(conditions, 1):
        _LOGGER.debug(f"  Condition {i}: {cond['field']} {cond['operator']} {cond['value']}")

    for weight_data in weights:
        # Evaluate all conditions
        condition_results = []
        for condition in conditions:
            try:
                result = evaluate_condition(weight_data, condition)
                condition_results.append(result)
                _LOGGER.debug(
                    f"  Evaluated: {condition['field']} {condition['operator']} {condition['value']} -> {result} "
                    f"(actual value: {weight_data.get(SUPPORTED_FIELDS[condition['field']])})"
                )
            except Exception as e:
                _LOGGER.warning(f"Error evaluating condition: {e}")
                condition_results.append(False)

        # Apply logic combination
        if logic == "and":
            passes = all(condition_results)
        else:  # logic == "or"
            passes = any(condition_results)

        if passes:
            filtered_weights.append(weight_data)

    filtered_count = len(filtered_weights)
    filtered_out = total_count - filtered_count

    if filtered_count == 0:
        _LOGGER.warning(
            f"Filter applied: 0/{total_count} records passed. "
            f"All records were filtered out! FIT file may be empty."
        )
    elif filtered_out > 0:
        _LOGGER.info(f"Filter applied: {filtered_count}/{total_count} records passed ({filtered_out} filtered out)")
    else:
        _LOGGER.info(f"Filter applied: All {total_count} records passed (none filtered out)")

    return filtered_weights
