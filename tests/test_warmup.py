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
    assert result["final_window_stabilised"] is False
    assert result["stop_reason"] == "minimum_reached_no_extra_allowed"
