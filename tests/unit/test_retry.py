"""Unit tests for retry decorator."""

import pytest
from src.utils.retry import with_retry, RetryError


def test_retry_success_first_attempt():
    """Test function succeeds on first attempt."""
    call_count = 0

    @with_retry(max_attempts=3)
    def successful_function():
        nonlocal call_count
        call_count += 1
        return "success"

    result = successful_function()
    assert result == "success"
    assert call_count == 1


def test_retry_success_after_failures():
    """Test function succeeds after some failures."""
    call_count = 0

    @with_retry(max_attempts=3, base_delay=0.01)
    def eventually_successful():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Temporary failure")
        return "success"

    result = eventually_successful()
    assert result == "success"
    assert call_count == 3


def test_retry_exhausted():
    """Test all retry attempts are exhausted."""
    call_count = 0

    @with_retry(max_attempts=3, base_delay=0.01)
    def always_fails():
        nonlocal call_count
        call_count += 1
        raise ConnectionError("Permanent failure")

    with pytest.raises(RetryError):
        always_fails()

    assert call_count == 3


def test_retry_specific_exceptions():
    """Test retry only catches specified exceptions."""
    @with_retry(max_attempts=3, base_delay=0.01, exceptions=(ConnectionError,))
    def raises_value_error():
        raise ValueError("Not retryable")

    # Should not retry ValueError
    with pytest.raises(ValueError):
        raises_value_error()


def test_retry_no_jitter():
    """Test retry without jitter."""
    call_count = 0

    @with_retry(max_attempts=2, base_delay=0.01, jitter=False)
    def fails_once():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ConnectionError("Temporary")
        return "success"

    result = fails_once()
    assert result == "success"
    assert call_count == 2
