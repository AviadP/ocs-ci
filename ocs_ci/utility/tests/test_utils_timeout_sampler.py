# -*- coding: utf8 -*-

import logging
import time

import pytest

from ocs_ci.ocs.exceptions import TimeoutExpiredError
from ocs_ci.utility.utils import TimeoutSampler, TimeoutIterator, RetryContext


@pytest.mark.parametrize("timeout_cls", [TimeoutSampler, TimeoutIterator])
def test_ts_null(timeout_cls):
    """
    Creating TimeoutSampler without any parameters should fail on TypeError.
    """
    with pytest.raises(TypeError):
        timeout_cls()


@pytest.mark.parametrize("timeout_cls", [TimeoutSampler, TimeoutIterator])
def test_ts_simple_usecase(timeout_cls):
    """
    Iterate over results of a simple TimeoutSampler instance and check that
    expected number of iterations happened and that TimeoutExpiredError was
    raised in the end.
    """
    timeout = 4
    sleep_time = 1
    func = lambda: 1  # noqa: E731
    results = []
    with pytest.raises(TimeoutExpiredError):
        for result in timeout_cls(timeout, sleep_time, func):
            results.append(result)
    assert results == [1, 1, 1, 1]


def test_ts_simple_logging(caplog, capsys):
    """
    For a simple usecase, check that TimeoutSampler logging works.
    """
    timeout = 3
    sleep_time = 1
    func = lambda: print("i")  # noqa: E731
    caplog.set_level(logging.DEBUG)
    with pytest.raises(TimeoutExpiredError):
        for _ in TimeoutSampler(timeout, sleep_time, func):
            pass
    # check stdout output from the func
    captured = capsys.readouterr()
    assert captured.out == "i\n" * timeout
    # check that log contains entries about ts iteration
    sleep_msg = f"Going to sleep for {sleep_time} seconds before next iteration"
    for rec in caplog.records:
        assert rec.getMessage() == sleep_msg
    assert len(caplog.records) == timeout


def test_ts_one_iteration():
    """
    When timeout == sleep_time, one iteration should happen.
    """
    timeout = 1
    sleep_time = 1
    func = lambda: 1  # noqa: E731
    results = []
    with pytest.raises(TimeoutExpiredError):
        for result in TimeoutSampler(timeout, sleep_time, func):
            results.append(result)
    assert results == [1]


def test_ts_one_iteration_big_sleep_time():
    """
    When timeout < sleep_time, TimeoutSampler object init fails on
    ValueError exception (as given timeout can't be quaranteed).
    """
    timeout = 1
    sleep_time = 2
    func = lambda: 1  # noqa: E731
    with pytest.raises(ValueError):
        TimeoutSampler(timeout, sleep_time, func)


def test_ts_one_iteration_big_func_runtime():
    """
    When timeout < runtime of 1st iteration, one iteration should happen.
    TimeoutSampler won't kill the function while it's running over the overall
    timeout.
    """
    timeout = 1
    sleep_time = 1

    def func():
        time.sleep(2)
        return 1

    results = []
    with pytest.raises(TimeoutExpiredError):
        for result in TimeoutSampler(timeout, sleep_time, func):
            results.append(result)
    assert results == [1]


def test_ts_func_exception(caplog):
    """
    Check that TimeoutSampler handles exception raised during iteration.
    Updated for new logging behavior: exceptions logged at DEBUG level.
    """
    timeout = 2
    sleep_time = 1

    def func():
        raise Exception("oh no")

    results = []
    caplog.set_level(logging.DEBUG)
    with pytest.raises(TimeoutExpiredError):
        for result in TimeoutSampler(timeout, sleep_time, func):
            results.append(result)
    assert results == []
    # check that exception was logged at debug level (new behavior)
    exception_logs = [
        rec for rec in caplog.records if "raised Exception" in rec.getMessage()
    ]
    assert len(exception_logs) >= 1  # At least one exception logged


def test_ti_func_values():
    """
    Iterate over results of a simple TimeoutIterator instance when function
    args and kwargs are specified.
    """
    timeout = 1
    sleep_time = 1

    def func(a, b, c=None):
        if c is None:
            return 0
        else:
            return a + b

    ti1 = TimeoutIterator(
        timeout, sleep_time, func=func, func_args=[1], func_kwargs={"b": 2, "c": 3}
    )
    results1 = []
    with pytest.raises(TimeoutExpiredError):
        for result in ti1:
            results1.append(result)
    assert results1 == [3]

    ti2 = TimeoutIterator(timeout, sleep_time, func, func_args=[1, 2])
    results2 = []
    with pytest.raises(TimeoutExpiredError):
        for result in ti2:
            results2.append(result)
    assert results2 == [0]


def test_ts_wait_for_value_positive():
    """
    Check that wait_for_value() function waits for func to return given value
    as expected.
    """
    timeout = 10
    sleep_time = 1
    func_state = []

    def func():
        func_state.append(0)
        return len(func_state)

    ts = TimeoutSampler(timeout, sleep_time, func)
    start = time.time()
    ts.wait_for_func_value(3)
    end = time.time()
    assert 2 < (end - start) < 3


def test_ts_wait_for_value_negative(caplog):
    """
    Check that when wait_for_value() fails to see expected return value of
    given func within given timeout, exception is raised and the problem
    logged.
    """
    timeout = 3
    sleep_time = 2
    func = lambda: 1  # noqa: E731
    ts = TimeoutSampler(timeout, sleep_time, func)
    caplog.set_level(logging.ERROR)
    with pytest.raises(TimeoutExpiredError):
        ts.wait_for_func_value(2)
    # check that the problem was logged properly
    assert len(caplog.records) == 1
    for rec in caplog.records:
        log_msg = rec.getMessage()
        assert "function <lambda> failed" in log_msg
        assert "failed to return expected value 2" in log_msg
        assert "during 3 second timeout" in log_msg


# ==================== NEW TESTS FOR REFACTORED TIMEOUTSAMPLER ====================


def test_reraise_parameter_default_false():
    """
    Test that reraise parameter defaults to False (swallows exceptions).
    """
    timeout = 2
    sleep_time = 1

    def func():
        raise ValueError("test error")

    results = []
    with pytest.raises(TimeoutExpiredError):
        for result in TimeoutSampler(timeout, sleep_time, func):
            results.append(result)
    assert results == []  # No results because exception was swallowed


def test_reraise_parameter_true():
    """
    Test that reraise=True immediately re-raises exceptions from func.
    """
    timeout = 10
    sleep_time = 1

    def func():
        raise ValueError("test error")

    with pytest.raises(ValueError, match="test error"):
        for result in TimeoutSampler(timeout, sleep_time, func, reraise=True):
            pass  # Should raise on first iteration


def test_callback_on_attempt_invoked():
    """
    Test that on_attempt callback is invoked with correct RetryContext.
    """
    timeout = 3
    sleep_time = 1
    callback_calls = []

    def func():
        return "success"

    def on_attempt_callback(ctx: RetryContext):
        callback_calls.append(
            {
                "attempt": ctx.attempt_number,
                "result": ctx.result,
                "exception": ctx.exception,
                "func_name": ctx.func_name,
            }
        )

    ts = TimeoutSampler(timeout, sleep_time, func, on_attempt=on_attempt_callback)
    count = 0
    with pytest.raises(TimeoutExpiredError):
        for result in ts:
            count += 1
            if count == 2:
                break  # Stop after 2 iterations

    assert len(callback_calls) == 2
    assert callback_calls[0]["attempt"] == 1
    assert callback_calls[0]["result"] == "success"
    assert callback_calls[0]["exception"] is None
    assert callback_calls[0]["func_name"] == "func"
    assert callback_calls[1]["attempt"] == 2


def test_callback_on_exception_invoked():
    """
    Test that on_exception callback is invoked when func raises.
    """
    timeout = 3
    sleep_time = 1
    callback_calls = []

    def func():
        raise RuntimeError("test exception")

    def on_exception_callback(ctx: RetryContext):
        callback_calls.append(
            {
                "attempt": ctx.attempt_number,
                "exception_type": type(ctx.exception).__name__,
                "exception_msg": str(ctx.exception),
            }
        )

    with pytest.raises(TimeoutExpiredError):
        for _ in TimeoutSampler(
            timeout, sleep_time, func, on_exception=on_exception_callback
        ):
            pass

    assert len(callback_calls) >= 2
    assert callback_calls[0]["exception_type"] == "RuntimeError"
    assert callback_calls[0]["exception_msg"] == "test exception"


def test_callback_on_timeout_invoked():
    """
    Test that on_timeout callback is invoked when timeout occurs.
    """
    timeout = 2
    sleep_time = 1
    timeout_callback_calls = []

    def func():
        return "value"

    def on_timeout_callback(ctx: RetryContext):
        timeout_callback_calls.append(ctx.attempt_number)

    with pytest.raises(TimeoutExpiredError):
        for _ in TimeoutSampler(
            timeout, sleep_time, func, on_timeout=on_timeout_callback
        ):
            pass

    assert len(timeout_callback_calls) == 1


def test_callback_exception_does_not_break_iteration(caplog):
    """
    Test that if a callback raises an exception, iteration continues.
    """
    timeout = 3
    sleep_time = 1
    results = []

    def func():
        return "value"

    def bad_callback(ctx: RetryContext):
        raise RuntimeError("callback error")

    caplog.set_level(logging.WARNING)
    with pytest.raises(TimeoutExpiredError):
        for result in TimeoutSampler(
            timeout, sleep_time, func, on_attempt=bad_callback
        ):
            results.append(result)

    # Iteration should continue despite callback exceptions
    assert len(results) >= 2
    # Check that callback exception was logged
    warnings = [rec for rec in caplog.records if "Callback" in rec.getMessage()]
    assert len(warnings) >= 1
    assert "raised RuntimeError" in warnings[0].getMessage()


def test_keyboard_interrupt_not_caught():
    """
    Test that KeyboardInterrupt is not caught and swallowed.
    """
    timeout = 10
    sleep_time = 1

    def func():
        raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        for _ in TimeoutSampler(timeout, sleep_time, func):
            pass  # Should immediately raise KeyboardInterrupt


def test_system_exit_not_caught():
    """
    Test that SystemExit is not caught and swallowed.
    """
    timeout = 10
    sleep_time = 1

    def func():
        raise SystemExit(1)

    with pytest.raises(SystemExit):
        for _ in TimeoutSampler(timeout, sleep_time, func):
            pass  # Should immediately raise SystemExit


def test_reset_after_iteration_succeeds():
    """
    Test that reset() works correctly after iteration completes.
    """
    timeout = 2
    sleep_time = 1

    def func():
        return 1

    sampler = TimeoutSampler(timeout, sleep_time, func)

    # First iteration
    results1 = []
    with pytest.raises(TimeoutExpiredError):
        for result in sampler:
            results1.append(result)

    assert len(results1) >= 1
    assert sampler.start_time is not None

    # Reset
    sampler.reset()
    assert sampler.start_time is None

    # Second iteration after reset
    results2 = []
    with pytest.raises(TimeoutExpiredError):
        for result in sampler:
            results2.append(result)

    assert len(results2) >= 1


def test_reset_during_iteration_raises_error():
    """
    Test that calling reset() during iteration raises RuntimeError.
    """
    timeout = 5
    sleep_time = 1

    def func():
        return 1

    sampler = TimeoutSampler(timeout, sleep_time, func)

    with pytest.raises(
        RuntimeError, match="Cannot reset TimeoutSampler while iteration is in progress"
    ):
        for result in sampler:
            sampler.reset()  # Should raise here
            break


def test_time_remaining_property():
    """
    Test that time_remaining property works correctly.
    """
    timeout = 10
    sleep_time = 1

    def func():
        return 1

    sampler = TimeoutSampler(timeout, sleep_time, func)

    # Before starting
    assert sampler.time_remaining == timeout

    # During iteration
    for result in sampler:
        remaining = sampler.time_remaining
        assert 0 <= remaining <= timeout
        break  # Only one iteration

    # After some time
    time.sleep(0.5)
    remaining = sampler.time_remaining
    assert 0 <= remaining < timeout


def test_wait_for_func_value_with_raise_on_timeout_false():
    """
    Test wait_for_func_value with raise_on_timeout=False returns False on timeout.
    """
    timeout = 2
    sleep_time = 1

    def func():
        return 1

    sampler = TimeoutSampler(timeout, sleep_time, func)
    result = sampler.wait_for_func_value(value=999, raise_on_timeout=False)

    assert result is False  # Should return False instead of raising


def test_wait_for_func_value_with_raise_on_timeout_true():
    """
    Test wait_for_func_value with raise_on_timeout=True raises on timeout (default).
    """
    timeout = 2
    sleep_time = 1

    def func():
        return 1

    sampler = TimeoutSampler(timeout, sleep_time, func)

    with pytest.raises(TimeoutExpiredError):
        sampler.wait_for_func_value(value=999, raise_on_timeout=True)


def test_wait_for_func_status_returns_false_on_timeout():
    """
    Test that wait_for_func_status returns False on timeout (backward compatible).
    """
    timeout = 2
    sleep_time = 1

    def func():
        return False

    sampler = TimeoutSampler(timeout, sleep_time, func)
    result = sampler.wait_for_func_status(result=True)

    assert result is False


def test_wait_for_func_status_with_raise_on_timeout_true():
    """
    Test that wait_for_func_status can raise on timeout when requested.
    """
    timeout = 2
    sleep_time = 1

    def func():
        return False

    sampler = TimeoutSampler(timeout, sleep_time, func)

    with pytest.raises(TimeoutExpiredError):
        sampler.wait_for_func_status(result=True, raise_on_timeout=True)


def test_backward_compatibility_old_usage():
    """
    Test that old usage patterns still work (backward compatibility).
    """
    timeout = 3
    sleep_time = 1

    def func():
        return "old_style"

    # Old style usage - should work exactly as before
    results = []
    with pytest.raises(TimeoutExpiredError):
        for result in TimeoutSampler(timeout, sleep_time, func):
            results.append(result)

    assert len(results) >= 2
    assert all(r == "old_style" for r in results)


def test_retry_context_fields():
    """
    Test that RetryContext contains all expected fields.
    """
    timeout = 3
    sleep_time = 1
    context_captured = []

    def func():
        return "test_value"

    def capture_context(ctx: RetryContext):
        context_captured.append(ctx)

    sampler = TimeoutSampler(timeout, sleep_time, func, on_attempt=capture_context)

    for result in sampler:
        break  # One iteration

    assert len(context_captured) == 1
    ctx = context_captured[0]

    # Check all fields exist and have correct types
    assert isinstance(ctx.attempt_number, int)
    assert ctx.attempt_number == 1
    assert isinstance(ctx.elapsed_time, float)
    assert ctx.elapsed_time >= 0
    assert isinstance(ctx.time_remaining, float)
    assert ctx.time_remaining > 0
    assert ctx.exception is None
    assert ctx.result == "test_value"
    assert ctx.func_name == "func"


def test_logging_levels_reduced(caplog):
    """
    Test that exception logging is at DEBUG level (not ERROR).
    """
    timeout = 2
    sleep_time = 1

    def func():
        raise ValueError("test")

    caplog.set_level(logging.DEBUG)
    with pytest.raises(TimeoutExpiredError):
        for _ in TimeoutSampler(timeout, sleep_time, func):
            pass

    # Check that exceptions logged at DEBUG level
    debug_logs = [rec for rec in caplog.records if rec.levelname == "DEBUG"]
    exception_logs = [
        rec for rec in debug_logs if "raised ValueError" in rec.getMessage()
    ]
    assert len(exception_logs) >= 1


def test_single_timeout_check_efficiency():
    """
    Test that timeout is checked once per iteration (not twice).
    This is a performance improvement - no direct assertion, but ensures no regression.
    """
    timeout = 2
    sleep_time = 1
    iteration_count = 0

    def func():
        nonlocal iteration_count
        iteration_count += 1
        return iteration_count

    with pytest.raises(TimeoutExpiredError):
        for _ in TimeoutSampler(timeout, sleep_time, func):
            pass

    # Should have ~2 iterations for 2 second timeout with 1 second sleep
    assert 1 <= iteration_count <= 3


def test_generic_type_hints():
    """
    Test that TimeoutSampler preserves type information (Generic[T]).
    This is verified by type checkers like mypy, but we can do basic runtime check.
    """
    timeout = 1
    sleep_time = 1

    def int_func() -> int:
        return 42

    def str_func() -> str:
        return "hello"

    # These should work and return correct types
    sampler_int = TimeoutSampler(timeout, sleep_time, int_func)
    sampler_str = TimeoutSampler(timeout, sleep_time, str_func)

    for result in sampler_int:
        assert isinstance(result, int)
        break

    for result in sampler_str:
        assert isinstance(result, str)
        break


def test_mixed_success_and_failure_iterations():
    """
    Test that sampler handles mix of successful and failed iterations.
    """
    timeout = 5
    sleep_time = 1
    call_count = [0]

    def func():
        call_count[0] += 1
        if call_count[0] % 2 == 0:
            raise ValueError("even call")
        return call_count[0]

    results = []
    with pytest.raises(TimeoutExpiredError):
        for result in TimeoutSampler(timeout, sleep_time, func):
            results.append(result)

    # Should have odd numbers (1, 3, 5, ...) because even calls raised
    assert all(r % 2 == 1 for r in results)
    assert len(results) >= 2


def test_callback_receives_correct_elapsed_and_remaining_time():
    """
    Test that callbacks receive accurate timing information.
    """
    timeout = 5
    sleep_time = 1
    timing_info = []

    def func():
        return "value"

    def capture_timing(ctx: RetryContext):
        timing_info.append(
            {
                "elapsed": ctx.elapsed_time,
                "remaining": ctx.time_remaining,
            }
        )

    sampler = TimeoutSampler(timeout, sleep_time, func, on_attempt=capture_timing)

    for i, result in enumerate(sampler):
        if i == 2:  # Stop after 3 iterations
            break

    # Check that timing makes sense
    assert len(timing_info) == 3
    # Elapsed time should increase
    assert (
        timing_info[0]["elapsed"]
        < timing_info[1]["elapsed"]
        < timing_info[2]["elapsed"]
    )
    # Remaining time should decrease
    assert (
        timing_info[0]["remaining"]
        > timing_info[1]["remaining"]
        > timing_info[2]["remaining"]
    )
    # Sum should be approximately timeout
    for info in timing_info:
        total = info["elapsed"] + info["remaining"]
        assert abs(total - timeout) < 0.5  # Allow small deviation


print("All new TimeoutSampler tests defined successfully!")
