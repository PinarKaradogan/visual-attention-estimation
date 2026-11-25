import dataclasses

import pytest

from visual_attention.core import (
    AgreementStatus,
    EventSource,
    FaceStatus,
    FeatureRecord,
    HandStatus,
    HumanLabelInterval,
    InterruptionEvent,
    Label,
    LabelRound,
    LabelValidity,
    PhoneStatus,
    SecondDecision,
    SecondReference,
    TrainLabel,
    ValidityFlags,
    WindowRecord,
)


def feature(**kw):
    base = dict(
        session_id="P01_SCENARIO",
        frame_index=0,
        timestamp_ms=0,
        feature_version="f-0.1.0",
        face_status=FaceStatus.VALID,
        hand_status=HandStatus.NOT_EVALUATED,
        phone_status=PhoneStatus.NOT_EVALUATED,
    )
    base.update(kw)
    return FeatureRecord(**base)


def window(**kw):
    base = dict(
        session_id="P01_SCENARIO",
        window_index=0,
        start_ms=0,
        end_ms=2000,
        feature_version="f-0.1.0",
        available_frame_count=30,
        is_valid=True,
    )
    base.update(kw)
    return WindowRecord(**base)


# --- FeatureRecord ---------------------------------------------------------


def test_feature_record_defaults_are_missing_not_zero():
    f = feature()
    assert f.head_yaw_deg is None
    assert f.phone_score is None
    assert f.validity_flags == ValidityFlags()


def test_feature_record_field_names_match_data_schema():
    names = {f.name for f in dataclasses.fields(FeatureRecord)}
    expected = {
        "session_id", "frame_index", "timestamp_ms", "feature_version",
        "head_yaw_deg", "head_pitch_deg", "head_roll_deg",
        "eye_aspect_ratio_left", "eye_aspect_ratio_right",
        "hand_count", "left_wrist_x", "left_wrist_y", "right_wrist_x", "right_wrist_y",
        "hand_phone_distance_norm", "hand_phone_overlap",
        "phone_score", "phone_box_x", "phone_box_y", "phone_box_w", "phone_box_h",
        "face_status", "phone_status", "hand_status", "validity_flags",
    }  # fmt: skip
    assert names == expected


def test_feature_record_accepts_status_strings():
    f = feature(face_status="NOT_DETECTED", hand_status="VALID", phone_status="VISIBLE")
    assert f.face_status is FaceStatus.NOT_DETECTED
    assert f.hand_status is HandStatus.VALID
    assert f.phone_status is PhoneStatus.VISIBLE


@pytest.mark.parametrize(
    "kw",
    [
        {"frame_index": -1},
        {"timestamp_ms": -5},
        {"feature_version": ""},
        {"hand_count": 3},
        {"left_wrist_x": 1.2},
        {"phone_score": -0.1},
        {"phone_box_w": 1.5},
        {"hand_phone_distance_norm": -0.01},
        {"face_status": "UNKNOWN"},
    ],
)
def test_feature_record_rejects_invalid_values(kw):
    with pytest.raises(ValueError):
        feature(**kw)


# --- WindowRecord ----------------------------------------------------------


def test_window_record_valid():
    w = window(
        aggregates={"head_pitch_deg_mean": -12.5, "hand_phone_overlap_ratio": None},
        face_detected_ratio=0.9,
        coverage_ratio=1.0,
        train_label="TELEFON",
    )
    assert w.train_label is TrainLabel.TELEFON
    assert w.train_label.is_trainable
    assert w.aggregates["hand_phone_overlap_ratio"] is None


def test_train_label_gecis_and_unused_are_not_trainable():
    assert not TrainLabel.GECIS.is_trainable
    assert not TrainLabel.UNUSED.is_trainable


@pytest.mark.parametrize(
    "kw",
    [
        {"end_ms": 0},
        {"window_index": -1},
        {"available_frame_count": -1},
        {"face_detected_ratio": 1.1},
        {"coverage_ratio": -0.2},
        {"is_valid": False},  # gerekçesiz geçersiz pencere
        {"train_label": "BELIRSIZ"},  # eğitim hedefi BELIRSIZ olamaz
    ],
)
def test_window_record_rejects_invalid_values(kw):
    with pytest.raises(ValueError):
        window(**kw)


def test_invalid_window_with_reason_is_allowed():
    w = window(is_valid=False, invalid_reason="EMPTY_WINDOW", available_frame_count=0)
    assert not w.is_valid


# --- HumanLabelInterval ----------------------------------------------------


def test_human_label_interval():
    h = HumanLabelInterval("P01_SCENARIO", "A1", "r1", 1000, 1500, "DIS_YON", "lp-0.2")
    assert h.label_round is LabelRound.R1
    assert h.label is Label.DIS_YON
    assert h.duration_ms == 500


@pytest.mark.parametrize(
    "args",
    [
        ("P01", "A1", "r1", 1000, 1000, "MATERYAL", "lp-0.2"),  # boş aralık
        ("P01", "", "r1", 0, 1000, "MATERYAL", "lp-0.2"),  # etiketleyici yok
        ("P01", "A1", "r1", 0, 1000, "GECIS", "lp-0.2"),  # GECIS etiketlenmez
        ("P01", "A1", "r3", 0, 1000, "MATERYAL", "lp-0.2"),  # bilinmeyen tur
    ],
)
def test_human_label_interval_rejects_invalid(args):
    with pytest.raises(ValueError):
        HumanLabelInterval(*args)


# --- SecondReference -------------------------------------------------------


def ref(label, validity, second_start_ms=3000):
    return SecondReference("P01", second_start_ms, label, validity, "A1", "final", "lp-0.2")


def test_second_reference_consistency():
    assert ref("MATERYAL", "LABELED").second_index == 3
    assert ref("GECIS", "LABELED").label is Label.GECIS
    assert ref("BELIRSIZ", "UNCERTAIN").validity is LabelValidity.UNCERTAIN
    assert ref("BELIRSIZ", "UNLABELED").agreement_status is AgreementStatus.NOT_IN_RETEST


@pytest.mark.parametrize(
    "label,validity,start",
    [
        ("MATERYAL", "UNCERTAIN", 0),  # ana sınıf ama belirsiz kaynak
        ("BELIRSIZ", "LABELED", 0),  # belirsiz ama etiketli
        ("TELEFON", "LABELED", 1500),  # saniye sınırında değil
    ],
)
def test_second_reference_rejects_inconsistent(label, validity, start):
    with pytest.raises(ValueError):
        ref(label, validity, start)


# --- InterruptionEvent -----------------------------------------------------


def test_interruption_event_model_and_reference():
    m = InterruptionEvent("P01", "TELEFON", 10_000, 13_000, "MODEL", model_id="M1")
    r = InterruptionEvent("P01", "DIS_YON", 0, 2_000, EventSource.REFERENCE, threshold_ms=2_000)
    assert m.duration_ms == 3_000
    assert r.model_id is None


@pytest.mark.parametrize(
    "kw",
    [
        {"label": "MATERYAL"},
        {"start_ms": 10_500},
        {"end_ms": 12_000},  # 2 sn < 3 sn eşik
        {"model_id": None},  # MODEL kaynağı model_id ister
        {"source": "REFERENCE"},  # REFERENCE kaynağında model_id olmaz
        {"threshold_ms": 0},
    ],
)
def test_interruption_event_rejects_invalid(kw):
    base = dict(
        session_id="P01",
        label="TELEFON",
        start_ms=10_000,
        end_ms=13_000,
        source="MODEL",
        model_id="M1",
    )
    base.update(kw)
    with pytest.raises(ValueError):
        InterruptionEvent(**base)


# --- SecondDecision --------------------------------------------------------


def test_second_decision_index_uses_second_ms():
    d = SecondDecision("P01", 7000, Label.MATERYAL, "trp-0.1.0")
    assert d.second_index == 7
