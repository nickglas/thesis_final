from src.benchmark import warmup


def _perf_counter_for_durations_ms(durations_ms):
    current = 0.0
    values = []
    for duration_ms in durations_ms:
        values.append(current)
        current += duration_ms / 1000.0
        values.append(current)

    iterator = iter(values)
    return lambda: next(iterator)


def test_adaptive_warmup_requires_current_window_stability(monkeypatch):
    durations = [10, 10, 10, 10, 30, 30, 10, 10, 10]
    monkeypatch.setattr(warmup.time, "perf_counter", _perf_counter_for_durations_ms(durations))

    result = warmup.run_warmup_calibrated(
        infer_fn=lambda _tensor: None,
        input_tensor=None,
        n=5,
        window=3,
        cv_threshold=0.10,
        max_extra_iterations=5,
    )

    assert result["stabilised_once"] is True
    assert result["first_stabilised_at_iteration"] == 3
    assert result["total_iterations"] == 9
    assert result["extra_iterations_used"] == 4
    assert result["max_extra_iterations"] == 5
    assert result["requested_max_extra_iterations"] == 5
    assert result["effective_max_extra_iterations"] == 5
    assert result["adaptive_until_stable"] is True
    assert result["unbounded_extra_iterations"] is False
    assert result["final_window_stabilised"] is True
    assert result["stop_reason"] == "current_window_stabilised"


def test_fixed_warmup_budget_records_unstable_final_window(monkeypatch):
    durations = [10, 10, 10, 10, 30]
    monkeypatch.setattr(warmup.time, "perf_counter", _perf_counter_for_durations_ms(durations))

    result = warmup.run_warmup_calibrated(
        infer_fn=lambda _tensor: None,
        input_tensor=None,
        n=5,
        window=3,
        cv_threshold=0.10,
        max_extra_iterations=0,
    )

    assert result["stabilised_once"] is True
    assert result["total_iterations"] == 5
    assert result["extra_iterations_used"] == 0
    assert result["max_extra_iterations"] == 0
    assert result["requested_max_extra_iterations"] == 0
    assert result["effective_max_extra_iterations"] == 0
    assert result["adaptive_until_stable"] is False
    assert result["unbounded_extra_iterations"] is False
    assert result["final_window_stabilised"] is False
    assert result["stop_reason"] == "minimum_reached_no_extra_allowed"


def test_unbounded_adaptive_warmup_records_requested_sentinel(monkeypatch):
    durations = [10, 10, 10, 10, 30, 30, 10, 10, 10]
    monkeypatch.setattr(warmup.time, "perf_counter", _perf_counter_for_durations_ms(durations))

    result = warmup.run_warmup_calibrated(
        infer_fn=lambda _tensor: None,
        input_tensor=None,
        n=5,
        window=3,
        cv_threshold=0.10,
        max_extra_iterations=-1,
    )

    assert result["total_iterations"] == 9
    assert result["extra_iterations_used"] == 4
    assert result["max_extra_iterations"] == -1
    assert result["requested_max_extra_iterations"] == -1
    assert result["effective_max_extra_iterations"] == 10_000
    assert result["adaptive_until_stable"] is True
    assert result["unbounded_extra_iterations"] is True
    assert result["final_window_stabilised"] is True
    assert result["stop_reason"] == "current_window_stabilised"


def test_calibrated_warmup_defaults_to_adaptive_until_stable(monkeypatch):
    durations = [10, 10, 10, 10, 30, 30, 10, 10, 10]
    monkeypatch.setattr(warmup.time, "perf_counter", _perf_counter_for_durations_ms(durations))

    result = warmup.run_warmup_calibrated(
        infer_fn=lambda _tensor: None,
        input_tensor=None,
        n=5,
        window=3,
        cv_threshold=0.10,
    )

    assert result["total_iterations"] == 9
    assert result["max_extra_iterations"] == -1
    assert result["adaptive_until_stable"] is True
    assert result["final_window_stabilised"] is True
