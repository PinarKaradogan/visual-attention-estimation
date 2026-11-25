import pytest

from visual_attention.core import Label, Prediction
from visual_attention.timeline import DecisionReason, resolve_timeline

M, T, D, B = Label.MATERYAL, Label.TELEFON, Label.DIS_YON, Label.BELIRSIZ


def windows(labels, session_id="S01", model_id="M0"):
    """i. eleman [i*1000, i*1000+2000) penceresinin tahmini."""
    return [
        Prediction(session_id, i, i * 1000, i * 1000 + 2000, model_id, lab)
        for i, lab in enumerate(labels)
    ]


def test_architecture_example():
    # docs/architecture.md §4.1 örneği
    out = resolve_timeline(windows([M, T, M]), session_duration_ms=4000)
    assert [d.label for d in out] == [M, M, T, M]
    assert out[0].reason == DecisionReason.BOOTSTRAP
    assert [d.second_start_ms for d in out] == [0, 1000, 2000, 3000]


def test_one_decision_per_second_and_no_double_counting():
    n = 1200
    out = resolve_timeline(windows([M] * (n - 1)), session_duration_ms=n * 1000)
    assert len(out) == n
    assert len({d.second_start_ms for d in out}) == n
    assert sum(d.label is M for d in out) == n  # 2 sn pencereler toplanmaz


def test_first_window_belirsiz_means_no_bootstrap():
    out = resolve_timeline(windows([B, M]), session_duration_ms=3000)
    assert [d.label for d in out] == [B, B, M]
    assert out[0].reason == DecisionReason.UNCOVERED
    assert out[1].reason == DecisionReason.WINDOW_BELIRSIZ


def test_missing_window_is_belirsiz_not_materyal():
    preds = [p for p in windows([M, M, M, M]) if p.window_index != 2]
    out = resolve_timeline(preds, session_duration_ms=5000)
    assert out[3].label is B
    assert out[3].reason == DecisionReason.UNCOVERED


def test_partial_last_second_is_uncovered():
    out = resolve_timeline(windows([M, M]), session_duration_ms=3500)
    assert len(out) == 4
    assert out[-1].label is B


def test_order_independent():
    preds = windows([M, T, D, M])
    assert resolve_timeline(preds, 5000) == resolve_timeline(list(reversed(preds)), 5000)


@pytest.mark.parametrize(
    "preds",
    [
        [Prediction("S01", 0, 0, 3000, "M0", M)],  # 3 sn pencere
        [Prediction("S01", 0, 500, 2500, "M0", M)],  # saniye sınırında değil
        windows([M]) + windows([T]),  # aynı saniyeye iki pencere
        windows([M]) + windows([M, M], session_id="S02"),  # oturum karışık
        windows([M]) + windows([M, M], model_id="M1"),  # model karışık
    ],
)
def test_invalid_inputs_raise(preds):
    with pytest.raises(ValueError):
        resolve_timeline(preds, session_duration_ms=10_000)


def test_window_beyond_session_raises():
    with pytest.raises(ValueError):
        resolve_timeline(windows([M, M, M]), session_duration_ms=3000)


def test_model_cannot_predict_gecis():
    with pytest.raises(ValueError):
        Prediction("S01", 0, 0, 2000, "M1", Label.GECIS)
