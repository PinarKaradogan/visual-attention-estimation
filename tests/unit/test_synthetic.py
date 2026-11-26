"""Sentetik veri üreticisi (#17) testleri. Sentetik veri sonuç olarak raporlanmaz."""

import os
import random
from statistics import mean

import pytest

from visual_attention.core import Label
from visual_attention.core.reference import HUMAN_INTERVAL_LABELS
from visual_attention.core.status import FaceStatus, PhoneStatus
from visual_attention.labeling import SessionType
from visual_attention.synthetic import (
    SOURCE_MODE,
    SYNTHETIC_FEATURE_VERSION,
    FeatureStreamConfig,
    SyntheticConfig,
    frame_timestamps,
    generate_synthetic_session,
    label_at,
    synthetic_participants,
)


@pytest.fixture(scope="module")
def scen():
    return generate_synthetic_session("P901", SessionType.SCENARIO)


@pytest.fixture(scope="module")
def free():
    return generate_synthetic_session("P901", SessionType.FREE)


# --- Güvenlik ve tekrarlanabilirlik -------------------------------------------


@pytest.mark.parametrize("pid", ["P01", "P10", "P1", "S901", "P801", ""])
def test_real_participant_codes_rejected(pid):
    with pytest.raises(ValueError, match="P9"):
        generate_synthetic_session(pid)


def test_synthetic_participants_reserved_prefix():
    assert synthetic_participants(3) == ["P901", "P902", "P903"]


def test_same_inputs_same_session(scen):
    again = generate_synthetic_session("P901", SessionType.SCENARIO)
    assert again.features == scen.features
    assert again.label_intervals == scen.label_intervals


def test_other_participant_or_seed_differs(scen):
    assert generate_synthetic_session("P902").features != scen.features
    assert generate_synthetic_session("P901", base_seed=7).features != scen.features


def test_marked_as_synthetic(scen):
    assert scen.source_mode == SOURCE_MODE == "SYNTHETIC"
    assert {r.feature_version for r in scen.features} == {SYNTHETIC_FEATURE_VERSION}
    assert SYNTHETIC_FEATURE_VERSION.startswith("syn-")
    assert scen.label_version.startswith("syn-")


def test_generator_writes_nothing_to_disk(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    generate_synthetic_session("P903")
    generate_synthetic_session("P903", SessionType.FREE)
    assert os.listdir(tmp_path) == []


# --- Davranış çizelgesi -------------------------------------------------------


def _contiguous(spans, duration_ms):
    spans = list(spans)
    assert spans[0].start_ms == 0
    assert spans[-1].end_ms == duration_ms
    for a, b in zip(spans, spans[1:], strict=False):
        assert a.end_ms == b.start_ms


def test_scenario_behavior_follows_scenario_order(scen):
    _contiguous(scen.behavior, scen.duration_ms)
    assert scen.duration_ms == 1_200_000
    assert [b.label for b in scen.behavior] == [b.label for b in scen.scenario.blocks]


def test_reaction_delay_within_bounds(scen):
    lo, hi = SyntheticConfig().reaction_delay_ms
    for seg, block in zip(scen.behavior[1:], scen.scenario.blocks[1:], strict=True):
        assert lo <= seg.start_ms - block.start_s * 1000 <= hi


def test_free_session(free):
    _contiguous(free.behavior, free.duration_ms)
    assert free.duration_ms == 600_000
    assert free.scenario is None
    labels = {b.label for b in free.behavior}
    assert Label.MATERYAL in labels and labels <= {Label.MATERYAL, Label.TELEFON, Label.DIS_YON}


def test_label_at_half_open(scen):
    seg = scen.behavior[1]
    assert label_at(scen.behavior, seg.start_ms) == seg.label
    assert label_at(scen.behavior, seg.start_ms - 1) == scen.behavior[0].label
    with pytest.raises(ValueError):
        label_at(scen.behavior, scen.duration_ms)


# --- Kare akışı ve zaman --------------------------------------------------------


@pytest.mark.parametrize("fps", [7.0, 15.0, 30.0])
def test_timestamps_monotonic_and_inside_session(fps):
    cfg = FeatureStreamConfig(fps=fps)
    frames = frame_timestamps(60_000, cfg, random.Random(1))
    idx = [i for i, _ in frames]
    ts = [t for _, t in frames]
    assert ts[0] == 0 and ts[-1] < 60_000
    assert all(a < b for a, b in zip(ts, ts[1:], strict=False))
    assert all(a < b for a, b in zip(idx, idx[1:], strict=False))
    expected = 60 * fps
    assert 0.95 * expected <= len(frames) <= expected


def test_dropped_frames_leave_index_gaps():
    cfg = FeatureStreamConfig(fps=15.0, frame_drop_p=0.2)
    frames = frame_timestamps(60_000, cfg, random.Random(2))
    idx = [i for i, _ in frames]
    assert max(idx) + 1 > len(idx)


@pytest.mark.parametrize("fps", [7.0, 15.0, 30.0])
def test_feature_stream_at_various_fps(fps):
    cfg = SyntheticConfig(stream=FeatureStreamConfig(fps=fps))
    s = generate_synthetic_session("P904", SessionType.FREE, config=cfg)
    ts = [r.timestamp_ms for r in s.features]
    assert all(a < b for a, b in zip(ts, ts[1:], strict=False))
    assert {r.session_id for r in s.features} == {"P904_FREE"}
    assert s.fps == fps


def test_face_dropout_frames_have_no_face_values(scen):
    assert scen.face_dropouts
    lost = [r for r in scen.features if any(s <= r.timestamp_ms < e for s, e in scen.face_dropouts)]
    assert lost
    for r in lost:
        assert r.face_status is FaceStatus.NOT_DETECTED
        assert r.head_pitch_deg is None and r.head_yaw_deg is None
        assert not r.validity_flags.head_pose_valid


def test_missing_values_are_none_not_zero(scen):
    for r in scen.features:
        if r.phone_status is not PhoneStatus.VISIBLE:
            assert r.phone_score is None and r.phone_box_x is None
        if r.face_status is not FaceStatus.VALID:
            assert r.eye_aspect_ratio_left is None


def test_class_dependent_values(scen):
    """Üreticinin sınıfları ayırt edilebilir ürettiğinin kontrolü (sonuç değildir)."""
    by = {lab: [] for lab in (Label.MATERYAL, Label.TELEFON, Label.DIS_YON)}
    for r in scen.features:
        by[label_at(scen.behavior, r.timestamp_ms)].append(r)

    def m(recs, attr):
        return mean(abs(getattr(r, attr)) for r in recs if getattr(r, attr) is not None)

    def visible(recs):
        return mean(r.phone_status is PhoneStatus.VISIBLE for r in recs)

    assert m(by[Label.DIS_YON], "head_yaw_deg") > m(by[Label.MATERYAL], "head_yaw_deg") + 20
    assert m(by[Label.MATERYAL], "head_pitch_deg") > m(by[Label.DIS_YON], "head_pitch_deg") + 10
    assert visible(by[Label.TELEFON]) > visible(by[Label.MATERYAL]) + 0.5


def test_participant_profiles_differ_but_shared_across_sessions():
    a = generate_synthetic_session("P905")
    b = generate_synthetic_session("P906")
    a_free = generate_synthetic_session("P905", SessionType.FREE)
    assert a.profile != b.profile
    assert a.profile == a_free.profile


# --- Sentetik etiketler ---------------------------------------------------------


def test_label_intervals_contiguous_and_in_vocabulary(scen):
    _contiguous(scen.label_intervals, scen.duration_ms)
    assert {iv.label for iv in scen.label_intervals} <= set(HUMAN_INTERVAL_LABELS)
    assert Label.GECIS not in {iv.label for iv in scen.label_intervals}
    assert {iv.session_id for iv in scen.label_intervals} == {scen.session_id}


def test_label_intervals_contain_belirsiz(scen):
    assert sum(iv.label is Label.BELIRSIZ for iv in scen.label_intervals) == 1


def test_label_boundaries_jittered_around_behavior(scen):
    jitter = SyntheticConfig().boundary_jitter_ms
    main = [iv for iv in scen.label_intervals if iv.label is not Label.BELIRSIZ]
    starts = {iv.start_ms for iv in main}
    for seg in scen.behavior[1:]:
        assert any(abs(s - seg.start_ms) <= jitter for s in starts)


def test_noiseless_labels_equal_scenario():
    s = generate_synthetic_session("P907", config=SyntheticConfig.noiseless())
    assert [(iv.start_ms, iv.end_ms, iv.label) for iv in s.label_intervals] == [
        (b.start_s * 1000, b.end_s * 1000, b.label) for b in s.scenario.blocks
    ]
    assert s.face_dropouts == ()
