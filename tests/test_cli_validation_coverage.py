"""
Tests for CLI validation functions in apgi_framework/cli.py.
"""

import argparse
import pytest
from apgi_framework.cli import (
    validate_trials_range,
    validate_participants_range,
    validate_threshold_range,
    validate_positive_int,
    validate_workers_range,
    validate_timeout_range,
    validate_days_range,
    validate_coverage_threshold_range,
    validate_precision_range,
    validate_steepness_range,
    validate_gain_range,
)


def test_validate_trials_range():
    assert validate_trials_range("100") == 100
    assert validate_trials_range("5000") == 5000
    assert validate_trials_range("10000") == 10000

    with pytest.raises(argparse.ArgumentTypeError, match="between 100 and 10000"):
        validate_trials_range("99")
    with pytest.raises(argparse.ArgumentTypeError, match="between 100 and 10000"):
        validate_trials_range("10001")
    with pytest.raises(argparse.ArgumentTypeError, match="Invalid integer value"):
        validate_trials_range("not-an-int")


def test_validate_participants_range():
    assert validate_participants_range("10") == 10
    assert validate_participants_range("1000") == 1000

    with pytest.raises(argparse.ArgumentTypeError, match="between 10 and 1000"):
        validate_participants_range("9")
    with pytest.raises(argparse.ArgumentTypeError, match="between 10 and 1000"):
        validate_participants_range("1001")
    with pytest.raises(argparse.ArgumentTypeError, match="Invalid integer value"):
        validate_participants_range("not-an-int")


def test_validate_threshold_range():
    assert validate_threshold_range("0.5") == 0.5
    assert validate_threshold_range("10.0") == 10.0

    with pytest.raises(argparse.ArgumentTypeError, match="between 0.5 and 10.0"):
        validate_threshold_range("0.4")
    with pytest.raises(argparse.ArgumentTypeError, match="between 0.5 and 10.0"):
        validate_threshold_range("10.1")
    with pytest.raises(argparse.ArgumentTypeError, match="Invalid float value"):
        validate_threshold_range("not-a-float")


def test_validate_positive_int():
    assert validate_positive_int("1") == 1

    with pytest.raises(argparse.ArgumentTypeError, match="positive integer"):
        validate_positive_int("0")
    with pytest.raises(argparse.ArgumentTypeError, match="positive integer"):
        validate_positive_int("-1")
    with pytest.raises(argparse.ArgumentTypeError, match="Invalid integer value"):
        validate_positive_int("not-an-int")


def test_validate_workers_range():
    assert validate_workers_range("1") == 1
    assert validate_workers_range("64") == 64

    with pytest.raises(argparse.ArgumentTypeError, match="between 1 and 64"):
        validate_workers_range("0")
    with pytest.raises(argparse.ArgumentTypeError, match="between 1 and 64"):
        validate_workers_range("65")
    with pytest.raises(argparse.ArgumentTypeError, match="Invalid integer value"):
        validate_workers_range("not-an-int")


def test_validate_timeout_range():
    assert validate_timeout_range("1") == 1
    assert validate_timeout_range("3600") == 3600

    with pytest.raises(argparse.ArgumentTypeError, match="between 1 and 3600"):
        validate_timeout_range("0")
    with pytest.raises(argparse.ArgumentTypeError, match="between 1 and 3600"):
        validate_timeout_range("3601")
    with pytest.raises(argparse.ArgumentTypeError, match="Invalid integer value"):
        validate_timeout_range("not-an-int")


def test_validate_days_range():
    assert validate_days_range("1") == 1
    assert validate_days_range("365") == 365

    with pytest.raises(argparse.ArgumentTypeError, match="between 1 and 365"):
        validate_days_range("0")
    with pytest.raises(argparse.ArgumentTypeError, match="between 1 and 365"):
        validate_days_range("366")
    with pytest.raises(argparse.ArgumentTypeError, match="Invalid integer value"):
        validate_days_range("not-an-int")


def test_validate_coverage_threshold_range():
    assert validate_coverage_threshold_range("0") == 0.0
    assert validate_coverage_threshold_range("100") == 100.0

    with pytest.raises(argparse.ArgumentTypeError, match="between 0 and 100"):
        validate_coverage_threshold_range("-0.1")
    with pytest.raises(argparse.ArgumentTypeError, match="between 0 and 100"):
        validate_coverage_threshold_range("100.1")
    with pytest.raises(argparse.ArgumentTypeError, match="Invalid float value"):
        validate_coverage_threshold_range("not-a-float")


def test_validate_precision_range():
    assert validate_precision_range("0.001") == 0.001
    assert validate_precision_range("1000") == 1000.0

    with pytest.raises(argparse.ArgumentTypeError, match="between 0.001 and 1000"):
        validate_precision_range("0.0009")
    with pytest.raises(argparse.ArgumentTypeError, match="between 0.001 and 1000"):
        validate_precision_range("1001")
    with pytest.raises(argparse.ArgumentTypeError, match="Invalid float value"):
        validate_precision_range("not-a-float")


def test_validate_steepness_range():
    assert validate_steepness_range("0.1") == 0.1
    assert validate_steepness_range("50") == 50.0

    with pytest.raises(argparse.ArgumentTypeError, match="between 0.1 and 50.0"):
        validate_steepness_range("0.09")
    with pytest.raises(argparse.ArgumentTypeError, match="between 0.1 and 50.0"):
        validate_steepness_range("50.1")
    with pytest.raises(argparse.ArgumentTypeError, match="Invalid float value"):
        validate_steepness_range("not-a-float")


def test_validate_gain_range():
    assert validate_gain_range("-10.0") == -10.0
    assert validate_gain_range("10.0") == 10.0

    with pytest.raises(argparse.ArgumentTypeError, match="between -10.0 and 10.0"):
        validate_gain_range("-10.1")
    with pytest.raises(argparse.ArgumentTypeError, match="between -10.0 and 10.0"):
        validate_gain_range("10.1")
    with pytest.raises(argparse.ArgumentTypeError, match="Invalid float value"):
        validate_gain_range("not-a-float")
