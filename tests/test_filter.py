"""
Unit tests for the weight filter module.
"""

import unittest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from garmin.filter import evaluate_condition, apply_filter, FilterOperator, SUPPORTED_FIELDS


class TestEvaluateCondition(unittest.TestCase):
    """Test the evaluate_condition function."""

    def setUp(self):
        """Set up test data."""
        self.sample_data = {
            'Date': '2026-01-11 10:30:45',
            'Timestamp': 1704880245,
            'Weight': 70.5,
            'BMI': 23.8,
            'BodyFat': 15.2,
            'BodyWater': 58.3,
            'BoneMass': 2.8,
            'MetabolicAge': 28,
            'MuscleMass': 30.1,
            'VisceralFat': 5,
            'BasalMetabolism': 1650,
        }

    def test_eq_operator(self):
        """Test equal operator."""
        condition = {'field': 'Weight', 'operator': 'eq', 'value': 70.5}
        self.assertTrue(evaluate_condition(self.sample_data, condition))

        condition = {'field': 'Weight', 'operator': 'eq', 'value': 71.0}
        self.assertFalse(evaluate_condition(self.sample_data, condition))

    def test_ne_operator(self):
        """Test not equal operator."""
        condition = {'field': 'Weight', 'operator': 'ne', 'value': 71.0}
        self.assertTrue(evaluate_condition(self.sample_data, condition))

        condition = {'field': 'Weight', 'operator': 'ne', 'value': 70.5}
        self.assertFalse(evaluate_condition(self.sample_data, condition))

    def test_gt_operator(self):
        """Test greater than operator."""
        condition = {'field': 'Weight', 'operator': 'gt', 'value': 70.0}
        self.assertTrue(evaluate_condition(self.sample_data, condition))

        condition = {'field': 'Weight', 'operator': 'gt', 'value': 71.0}
        self.assertFalse(evaluate_condition(self.sample_data, condition))

    def test_gte_operator(self):
        """Test greater than or equal operator."""
        condition = {'field': 'Weight', 'operator': 'gte', 'value': 70.5}
        self.assertTrue(evaluate_condition(self.sample_data, condition))

        condition = {'field': 'Weight', 'operator': 'gte', 'value': 70.0}
        self.assertTrue(evaluate_condition(self.sample_data, condition))

        condition = {'field': 'Weight', 'operator': 'gte', 'value': 71.0}
        self.assertFalse(evaluate_condition(self.sample_data, condition))

    def test_lt_operator(self):
        """Test less than operator."""
        condition = {'field': 'Weight', 'operator': 'lt', 'value': 71.0}
        self.assertTrue(evaluate_condition(self.sample_data, condition))

        condition = {'field': 'Weight', 'operator': 'lt', 'value': 70.0}
        self.assertFalse(evaluate_condition(self.sample_data, condition))

    def test_lte_operator(self):
        """Test less than or equal operator."""
        condition = {'field': 'Weight', 'operator': 'lte', 'value': 70.5}
        self.assertTrue(evaluate_condition(self.sample_data, condition))

        condition = {'field': 'Weight', 'operator': 'lte', 'value': 71.0}
        self.assertTrue(evaluate_condition(self.sample_data, condition))

        condition = {'field': 'Weight', 'operator': 'lte', 'value': 70.0}
        self.assertFalse(evaluate_condition(self.sample_data, condition))

    def test_between_operator(self):
        """Test between operator."""
        condition = {'field': 'Weight', 'operator': 'between', 'value': [60, 80]}
        self.assertTrue(evaluate_condition(self.sample_data, condition))

        condition = {'field': 'Weight', 'operator': 'between', 'value': [70.5, 80]}
        self.assertTrue(evaluate_condition(self.sample_data, condition))

        condition = {'field': 'Weight', 'operator': 'between', 'value': [60, 70.5]}
        self.assertTrue(evaluate_condition(self.sample_data, condition))

        condition = {'field': 'Weight', 'operator': 'between', 'value': [71, 80]}
        self.assertFalse(evaluate_condition(self.sample_data, condition))

        condition = {'field': 'Weight', 'operator': 'between', 'value': [50, 60]}
        self.assertFalse(evaluate_condition(self.sample_data, condition))

    def test_bmi_field(self):
        """Test filtering by BMI."""
        condition = {'field': 'BMI', 'operator': 'lte', 'value': 25}
        self.assertTrue(evaluate_condition(self.sample_data, condition))

        condition = {'field': 'BMI', 'operator': 'gt', 'value': 25}
        self.assertFalse(evaluate_condition(self.sample_data, condition))

    def test_body_fat_field(self):
        """Test filtering by BodyFat."""
        condition = {'field': 'BodyFat', 'operator': 'between', 'value': [15, 16]}
        self.assertTrue(evaluate_condition(self.sample_data, condition))

    def test_integer_field_metabolic_age(self):
        """Test filtering by integer field MetabolicAge."""
        condition = {'field': 'MetabolicAge', 'operator': 'eq', 'value': 28}
        self.assertTrue(evaluate_condition(self.sample_data, condition))

    def test_integer_field_visceral_fat(self):
        """Test filtering by integer field VisceralFat."""
        condition = {'field': 'VisceralFat', 'operator': 'lte', 'value': 10}
        self.assertTrue(evaluate_condition(self.sample_data, condition))

    def test_missing_field_returns_false(self):
        """Test that missing fields return False."""
        condition = {'field': 'Weight', 'operator': 'gt', 'value': 60}
        data_without_weight = {'BMI': 23.0}
        self.assertFalse(evaluate_condition(data_without_weight, condition))

    def test_unsupported_field_raises_error(self):
        """Test that unsupported fields raise ValueError."""
        condition = {'field': 'InvalidField', 'operator': 'eq', 'value': 100}
        with self.assertRaises(ValueError):
            evaluate_condition(self.sample_data, condition)

    def test_unsupported_operator_returns_false(self):
        """Test that unsupported operators return False (logs warning)."""
        condition = {'field': 'Weight', 'operator': 'invalid', 'value': 70}
        # Unsupported operators log a warning and return False
        self.assertFalse(evaluate_condition(self.sample_data, condition))


class TestApplyFilter(unittest.TestCase):
    """Test the apply_filter function."""

    def setUp(self):
        """Set up test data."""
        self.sample_weights = [
            {'Weight': 55, 'BMI': 20, 'BodyFat': 12},
            {'Weight': 65, 'BMI': 22, 'BodyFat': 15},
            {'Weight': 75, 'BMI': 25, 'BodyFat': 18},
            {'Weight': 85, 'BMI': 28, 'BodyFat': 22},
            {'Weight': 95, 'BMI': 31, 'BodyFat': 25},
        ]

    def test_no_filter_returns_all(self):
        """Test that no filter returns all data."""
        result = apply_filter(self.sample_weights, {})
        self.assertEqual(len(result), 5)

    def test_disabled_filter_returns_all(self):
        """Test that disabled filter returns all data."""
        filter_config = {
            'enabled': False,
            'conditions': [{'field': 'Weight', 'operator': 'gt', 'value': 70}]
        }
        result = apply_filter(self.sample_weights, filter_config)
        self.assertEqual(len(result), 5)

    def test_single_condition_filter(self):
        """Test filtering with a single condition."""
        filter_config = {
            'enabled': True,
            'conditions': [
                {'field': 'Weight', 'operator': 'gt', 'value': 70}
            ],
            'logic': 'and'
        }
        result = apply_filter(self.sample_weights, filter_config)
        self.assertEqual(len(result), 3)  # 75, 85, 95

    def test_and_logic_multiple_conditions(self):
        """Test AND logic with multiple conditions."""
        filter_config = {
            'enabled': True,
            'conditions': [
                {'field': 'Weight', 'operator': 'gte', 'value': 60},
                {'field': 'Weight', 'operator': 'lte', 'value': 80}
            ],
            'logic': 'and'
        }
        result = apply_filter(self.sample_weights, filter_config)
        self.assertEqual(len(result), 2)  # 65, 75

    def test_or_logic_multiple_conditions(self):
        """Test OR logic with multiple conditions."""
        filter_config = {
            'enabled': True,
            'conditions': [
                {'field': 'Weight', 'operator': 'lte', 'value': 60},
                {'field': 'Weight', 'operator': 'gte', 'value': 90}
            ],
            'logic': 'or'
        }
        result = apply_filter(self.sample_weights, filter_config)
        self.assertEqual(len(result), 2)  # 55, 95

    def test_between_operator_filter(self):
        """Test filtering with between operator."""
        filter_config = {
            'enabled': True,
            'conditions': [
                {'field': 'Weight', 'operator': 'between', 'value': [60, 80]}
            ],
            'logic': 'and'
        }
        result = apply_filter(self.sample_weights, filter_config)
        self.assertEqual(len(result), 2)  # 65, 75

    def test_all_filtered_out(self):
        """Test when all records are filtered out."""
        filter_config = {
            'enabled': True,
            'conditions': [
                {'field': 'Weight', 'operator': 'gt', 'value': 100}
            ],
            'logic': 'and'
        }
        result = apply_filter(self.sample_weights, filter_config)
        self.assertEqual(len(result), 0)

    def test_all_pass_filter(self):
        """Test when all records pass the filter."""
        filter_config = {
            'enabled': True,
            'conditions': [
                {'field': 'Weight', 'operator': 'gt', 'value': 50}
            ],
            'logic': 'and'
        }
        result = apply_filter(self.sample_weights, filter_config)
        self.assertEqual(len(result), 5)

    def test_empty_weights_list(self):
        """Test with empty weights list."""
        result = apply_filter([], {'enabled': True, 'conditions': [], 'logic': 'and'})
        self.assertEqual(len(result), 0)

    def test_empty_conditions_returns_all(self):
        """Test that empty conditions returns all data."""
        filter_config = {
            'enabled': True,
            'conditions': [],
            'logic': 'and'
        }
        result = apply_filter(self.sample_weights, filter_config)
        self.assertEqual(len(result), 5)

    def test_multi_field_filter(self):
        """Test filtering on multiple fields."""
        filter_config = {
            'enabled': True,
            'conditions': [
                {'field': 'Weight', 'operator': 'gt', 'value': 60},
                {'field': 'BMI', 'operator': 'lt', 'value': 30}
            ],
            'logic': 'and'
        }
        result = apply_filter(self.sample_weights, filter_config)
        self.assertEqual(len(result), 3)  # 65, 75, 85 (BMI 22, 25, 28)


class TestFilterConfigValidator(unittest.TestCase):
    """Test the FilterConfigValidator class."""

    def setUp(self):
        """Set up test imports."""
        from garmin.filter_config import FilterConfigValidator, FilterConfigError
        self.FilterConfigValidator = FilterConfigValidator
        self.FilterConfigError = FilterConfigError

    def test_valid_filter_config(self):
        """Test validation of a valid filter config."""
        config = {
            'enabled': True,
            'conditions': [
                {'field': 'Weight', 'operator': 'gt', 'value': 70}
            ],
            'logic': 'and'
        }
        # Should not raise
        self.FilterConfigValidator.validate(config)

    def test_none_config_is_valid(self):
        """Test that None config is valid (backward compatibility)."""
        # Should not raise
        self.FilterConfigValidator.validate(None)

    def test_disabled_filter_skips_validation(self):
        """Test that disabled filter doesn't validate conditions."""
        config = {
            'enabled': False,
            'conditions': []  # Empty conditions when disabled is OK
        }
        # Should not raise
        self.FilterConfigValidator.validate(config)

    def test_missing_conditions_when_enabled(self):
        """Test that missing conditions when enabled raises error."""
        config = {
            'enabled': True,
            'logic': 'and'
        }
        with self.assertRaises(self.FilterConfigError) as cm:
            self.FilterConfigValidator.validate(config)
        self.assertIn("'conditions'", str(cm.exception))

    def test_empty_conditions_when_enabled(self):
        """Test that empty conditions when enabled raises error."""
        config = {
            'enabled': True,
            'conditions': [],
            'logic': 'and'
        }
        with self.assertRaises(self.FilterConfigError) as cm:
            self.FilterConfigValidator.validate(config)
        self.assertIn("'conditions'", str(cm.exception))

    def test_invalid_logic(self):
        """Test that invalid logic raises error."""
        config = {
            'enabled': True,
            'conditions': [
                {'field': 'Weight', 'operator': 'gt', 'value': 70}
            ],
            'logic': 'invalid'
        }
        with self.assertRaises(self.FilterConfigError) as cm:
            self.FilterConfigValidator.validate(config)
        self.assertIn("'logic'", str(cm.exception))

    def test_invalid_field_name(self):
        """Test that invalid field name raises error."""
        config = {
            'enabled': True,
            'conditions': [
                {'field': 'InvalidField', 'operator': 'gt', 'value': 70}
            ],
            'logic': 'and'
        }
        with self.assertRaises(self.FilterConfigError) as cm:
            self.FilterConfigValidator.validate(config)
        self.assertIn("InvalidField", str(cm.exception))

    def test_invalid_operator(self):
        """Test that invalid operator raises error."""
        config = {
            'enabled': True,
            'conditions': [
                {'field': 'Weight', 'operator': 'invalid_op', 'value': 70}
            ],
            'logic': 'and'
        }
        with self.assertRaises(self.FilterConfigError) as cm:
            self.FilterConfigValidator.validate(config)
        self.assertIn("operator", str(cm.exception))

    def test_between_requires_list(self):
        """Test that between operator requires a list."""
        config = {
            'enabled': True,
            'conditions': [
                {'field': 'Weight', 'operator': 'between', 'value': 70}
            ],
            'logic': 'and'
        }
        with self.assertRaises(self.FilterConfigError) as cm:
            self.FilterConfigValidator.validate(config)
        self.assertIn("between", str(cm.exception))

    def test_between_requires_two_values(self):
        """Test that between operator requires exactly 2 values."""
        config = {
            'enabled': True,
            'conditions': [
                {'field': 'Weight', 'operator': 'between', 'value': [60]}
            ],
            'logic': 'and'
        }
        with self.assertRaises(self.FilterConfigError) as cm:
            self.FilterConfigValidator.validate(config)
        self.assertIn("between", str(cm.exception))

    def test_between_range_validation(self):
        """Test that between validates min <= max."""
        config = {
            'enabled': True,
            'conditions': [
                {'field': 'Weight', 'operator': 'between', 'value': [80, 60]}
            ],
            'logic': 'and'
        }
        with self.assertRaises(self.FilterConfigError) as cm:
            self.FilterConfigValidator.validate(config)
        self.assertIn("less than", str(cm.exception))

    def test_missing_required_field_in_condition(self):
        """Test that missing required field in condition raises error."""
        config = {
            'enabled': True,
            'conditions': [
                {'field': 'Weight', 'operator': 'gt'}  # Missing 'value'
            ],
            'logic': 'and'
        }
        with self.assertRaises(self.FilterConfigError) as cm:
            self.FilterConfigValidator.validate(config)
        self.assertIn("missing", str(cm.exception))


class TestSupportedFields(unittest.TestCase):
    """Test the SUPPORTED_FIELDS constant."""

    def test_expected_fields_are_supported(self):
        """Test that all expected fields are in SUPPORTED_FIELDS."""
        expected_fields = [
            'Weight', 'BMI', 'BodyFat', 'BodyWater',
            'BoneMass', 'MetabolicAge', 'MuscleMass',
            'VisceralFat', 'BasalMetabolism'
        ]
        for field in expected_fields:
            self.assertIn(field, SUPPORTED_FIELDS)


if __name__ == '__main__':
    unittest.main()
