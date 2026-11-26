"""Şema ve zaman sözleşmesinin modüller arası uçtan uca doğrulaması (#17, data-schema §5).

Sentetik veriyle yalnızca yazılımın doğruluğu sınanır; bu testlerin sayıları sonuç değildir.
"""

import pytest

from visual_attention.core import Label, LabelValidity, TrainLabel
from visual_attention.core.constants import SECOND_MS, WINDOW_MS, WINDOW_STEP_MS
from visual_attention.core.records import Prediction
from visual_attention.labeling import (
    parse_elan_filename,
    read_elan_tsv,
    second_references,
    window_train_label,
)
from visual_attention.labeling.elan import SessionType
from visual_attention.metrics.session import compare_sessions, extract_interruptions
from visual_attention.synthetic import (
    SyntheticConfig,
    elan_filename,
    generate_synthetic_session,
    write_elan_tsv,
)
from visual_attention.timeline.resolver import resolve_timeline


@pytest.fixture(scope="module")
def noisy():
    return generate_synthetic_session("P911")


@pytest.fixture(scope="module")
def clean():
    return generate_synthetic_session("P912", config=SyntheticConfig.noiseless())


def windows(duration_ms):
    """[t-2000, t) pencereleri, 1 sn adımla."""
    return [(end - WINDOW_MS, end) for end in range(WINDOW_MS, duration_ms + 1, WINDOW_STEP_MS)]


def oracle_predictions(session, ref_labels):
    """Her pencere için hedef saniyesinin referans etiketini veren kusursuz tahmin.

    GECIS model çıktısı olamadığından GECIS saniyeleri BELIRSIZ tahmin edilir.
    """
    preds = []
    for i, (start, end) in enumerate(windows(session.duration_ms)):
        target = ref_labels[(end - SECOND_MS) // SECOND_MS]
        label = Label.BELIRSIZ if target is Label.GECIS else target
        preds.append(Prediction(session.session_id, i, start, end, "ORACLE", label))
    # İlk saniye bootstrap ile ilk pencereden doldurulur; ilk pencere [0, 2000)'nin
    # hedefi 1. saniyedir. İlk iki saniye senaryoda her zaman MATERYAL'dir.
    return preds


# --- ELAN gidiş-dönüş -------------------------------------------------------------


@pytest.mark.parametrize("stype", [SessionType.SCENARIO, SessionType.FREE])
def test_elan_roundtrip(tmp_path, stype):
    s = generate_synthetic_session("P913", stype)
    name = elan_filename(s.session_id, "r1", "A1")
    path = write_elan_tsv(s.label_intervals, tmp_path / name)
    info = parse_elan_filename(path)
    assert info.session_id == s.session_id
    assert info.participant_id == "P913"
    back = read_elan_tsv(path, s.label_version)
    assert back.intervals == s.label_intervals


# --- 1 sn referans ve tekil saniye ----------------------------------------------


def test_one_reference_per_second(noisy):
    refs = second_references(noisy.label_intervals, noisy.duration_ms)
    starts = [r.second_start_ms for r in refs]
    assert len(refs) == noisy.duration_ms // SECOND_MS
    assert starts == list(range(0, noisy.duration_ms, SECOND_MS))
    assert len(set(starts)) == len(starts)


def test_belirsiz_span_reaches_reference(noisy):
    refs = second_references(noisy.label_intervals, noisy.duration_ms)
    assert any(r.validity is LabelValidity.UNCERTAIN for r in refs)


def test_one_decision_per_second(noisy):
    refs = [r.label for r in second_references(noisy.label_intervals, noisy.duration_ms)]
    decisions = resolve_timeline(oracle_predictions(noisy, refs), noisy.duration_ms)
    starts = [d.second_start_ms for d in decisions]
    assert starts == list(range(0, noisy.duration_ms, SECOND_MS))


# --- Yarı açık aralıklar ------------------------------------------------------------


def test_each_frame_in_at_most_two_windows(noisy):
    wins = windows(noisy.duration_ms)
    for r in noisy.features[::50]:
        t = r.timestamp_ms
        n = sum(s <= t < e for s, e in wins)
        assert n <= 2
        if SECOND_MS <= t < noisy.duration_ms - SECOND_MS:
            assert n == 2


def test_frame_on_window_boundary_belongs_to_later_window():
    t = 2000
    assert not (0 <= t < 2000)
    assert 2000 <= t < 4000 and 1000 <= t < 3000


# --- Pencere eğitim hedefi ------------------------------------------------------------


def test_train_labels_on_noiseless_session(clean):
    labels = [
        window_train_label(clean.label_intervals, s, e) for s, e in windows(clean.duration_ms)
    ]
    assert TrainLabel.UNUSED not in labels
    # Senaryodaki her sınır, tam ortasından geçtiği pencerede 1000/1000 eşitlik → GECIS
    n_boundaries = len(clean.scenario.blocks) - 1
    assert labels.count(TrainLabel.GECIS) == n_boundaries


# --- Kusursuz tahmin → sıfır hata --------------------------------------------------


def test_perfect_prediction_zero_error_noiseless(clean):
    ref = [r.label for r in second_references(clean.label_intervals, clean.duration_ms)]
    assert ref == clean.scenario.to_labels()
    decisions = resolve_timeline(oracle_predictions(clean, ref), clean.duration_ms)
    pred = [d.label for d in decisions]
    assert pred == ref
    err = compare_sessions(ref, pred)
    assert err.focus_abs_error_s == 0
    assert err.interruption_count_abs_error == 0
    assert err.events.f1 == 1.0
    expected = [b for b in clean.scenario.interruptions if b.duration_s >= 3]
    assert len(extract_interruptions(ref)) == len(expected)


def test_perfect_prediction_on_noisy_session(noisy):
    ref = [r.label for r in second_references(noisy.label_intervals, noisy.duration_ms)]
    pred = [d.label for d in resolve_timeline(oracle_predictions(noisy, ref), noisy.duration_ms)]
    # GECIS saniyeleri dışında birebir aynı; odak süresi aynı kalır.
    assert all(p == r or r is Label.GECIS for p, r in zip(pred, ref, strict=True))
    assert compare_sessions(ref, pred).focus_abs_error_s == 0


def test_always_material_baseline_misses_all_events(clean):
    ref = [r.label for r in second_references(clean.label_intervals, clean.duration_ms)]
    err = compare_sessions(ref, [Label.MATERYAL] * len(ref))
    non_material = sum(lab is not Label.MATERYAL for lab in ref)
    assert err.focus_abs_error_s == non_material
    assert err.events.f1 == 0.0


# --- LOSO hazırlığı ------------------------------------------------------------------------


def test_sessions_group_by_participant():
    from visual_attention.synthetic import synthetic_participants

    pids = synthetic_participants(3, start=921)
    sessions = [
        generate_synthetic_session(p, st) for p in pids for st in (SessionType.SCENARIO, "FREE")
    ]
    groups = {s.session_id: s.participant_id for s in sessions}
    assert len(groups) == 6
    assert set(groups.values()) == set(pids)
    for s in sessions:
        assert s.session_id.startswith(s.participant_id + "_")
