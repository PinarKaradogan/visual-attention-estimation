import pytest

from visual_attention.core import Label, Prediction
from visual_attention.metrics import (
    Interruption,
    compare_sessions,
    event_f1,
    extract_interruptions,
    labels_from_decisions,
    summarize_session,
)
from visual_attention.timeline import resolve_timeline

M, T, D, B, G = Label.MATERYAL, Label.TELEFON, Label.DIS_YON, Label.BELIRSIZ, Label.GECIS

# Rapor Ek-1: örnek senaryolu 20 dk oturum (saniye, durum)
EK1_BLOCKS = [
    (80, M), (25, T), (75, M), (10, D), (85, M), (8, T), (70, M), (2, D), (80, M),
    (30, T), (75, M), (20, D), (85, M), (12, T), (70, M), (6, D), (80, M), (20, T),
    (75, M), (15, D), (85, M), (5, T), (70, M), (4, D), (113, M),
]  # fmt: skip


def expand(blocks):
    return [lab for n, lab in blocks for _ in range(n)]


def test_ek1_scenario_matches_report():
    ref = expand(EK1_BLOCKS)
    assert len(ref) == 1200
    s = summarize_session(ref)
    assert s.total_seconds - s.focus_seconds == 157  # kesinti toplamı 157 sn
    # 2 sn'lik DIŞ_YÖN 3 sn eşiğinin altında kalır: 12 bloktan 11 kesinti
    assert s.interruption_count == 11


def test_always_materyal_baseline_matches_report_h4():
    ref = expand(EK1_BLOCKS)
    err = compare_sessions(ref, [M] * len(ref))
    assert err.focus_abs_error_s == 157  # rapor H4: taban hatası 157 sn
    assert err.events.f1 == 0  # rapor H4: taban olay F1 = 0


def test_interruption_threshold_boundary():
    assert extract_interruptions([M, T, T, M]) == []
    assert extract_interruptions([M, T, T, T, M]) == [Interruption(T, 1, 4)]


def test_interruption_at_session_edges():
    assert extract_interruptions([D, D, D, M, T, T, T]) == [
        Interruption(D, 0, 3),
        Interruption(T, 4, 7),
    ]


def test_belirsiz_breaks_run_and_class_change_splits():
    assert extract_interruptions([T, T, B, T, T]) == []
    assert extract_interruptions([T, T, D, D]) == []


def test_sensitivity_thresholds():
    labels = [M, D, D, M, T, T, T, T, T, M]
    assert len(extract_interruptions(labels, 2)) == 2
    assert len(extract_interruptions(labels, 5)) == 1


def test_focus_ratio_excludes_belirsiz():
    s = summarize_session([M, M, B, T])
    assert s.focus_seconds == 2
    assert s.valid_seconds == 3
    assert s.focus_ratio == pytest.approx(2 / 3)
    assert s.belirsiz_ratio == pytest.approx(1 / 4)


def test_event_f1_tolerance_and_class():
    ref = [Interruption(T, 10, 20), Interruption(D, 50, 55)]
    pred = [Interruption(T, 12, 20), Interruption(T, 50, 55), Interruption(D, 90, 95)]
    m = event_f1(ref, pred)
    assert (m.tp, m.fp, m.fn) == (1, 2, 1)
    assert m.f1 == pytest.approx(2 / 5)
    assert event_f1(ref, [Interruption(T, 13, 20)]).tp == 0  # 3 sn > ±2 sn


def test_event_f1_one_to_one():
    ref = [Interruption(T, 10, 15)]
    pred = [Interruption(T, 9, 15), Interruption(T, 11, 15)]
    m = event_f1(ref, pred)
    assert (m.tp, m.fp, m.fn) == (1, 1, 0)


def test_event_f1_undefined_when_no_events():
    m = event_f1([], [])
    assert m.f1 is None and m.precision is None and m.recall is None


def test_compare_requires_equal_length():
    with pytest.raises(ValueError):
        compare_sessions([M, M], [M])


def test_end_to_end_windows_to_metrics():
    window_labels = [M] * 9 + [T] * 5 + [M] * 10
    preds = [
        Prediction("S01", i, i * 1000, i * 1000 + 2000, "M1", lab)
        for i, lab in enumerate(window_labels)
    ]
    labels = labels_from_decisions(resolve_timeline(preds, 25_000))
    assert len(labels) == 25
    s = summarize_session(labels)
    assert s.interruptions == (Interruption(T, 10, 15),)
    assert s.focus_seconds == 20


def test_gecis_breaks_run_and_is_not_valid_time():
    assert extract_interruptions([T, T, G, T, T]) == []
    s = summarize_session([M, M, G, B, T])
    assert s.valid_seconds == 3
    assert s.gecis_seconds == 1
    assert s.focus_ratio == pytest.approx(2 / 3)
