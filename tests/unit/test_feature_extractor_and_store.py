"""Öznitelik birleştirici, yerel depo ve komut satırı testleri.

Bileşenler sahte nesnelerdir; MediaPipe modeli gerekmez. Dosyalar geçici klasörde yazılır.
"""

import cv2
import numpy as np
import pytest

from visual_attention.capture import FakeVideoSource, FrameRecord, SourceStatus
from visual_attention.core import FaceStatus, HandStatus, PhoneStatus
from visual_attention.features import FaceFeatures, HandFeatures, PhoneFeatures
from visual_attention.features import __main__ as cli
from visual_attention.features.extractor import FeatureExtractor, build_feature_version
from visual_attention.storage import COLUMNS, FeatureStore

FACE = FaceFeatures(
    face_status=FaceStatus.VALID,
    head_yaw_deg=5.0,
    head_pitch_deg=20.0,
    head_roll_deg=-2.0,
    eye_aspect_ratio_left=0.3,
    eye_aspect_ratio_right=0.28,
)
PHONE = PhoneFeatures(
    phone_status=PhoneStatus.VISIBLE,
    phone_score=0.8,
    phone_box_x=0.4,
    phone_box_y=0.5,
    phone_box_w=0.1,
    phone_box_h=0.2,
)
HAND = HandFeatures(
    hand_status=HandStatus.VALID,
    hand_count=2,
    left_wrist_x=0.6,
    left_wrist_y=0.8,
    right_wrist_x=0.3,
    right_wrist_y=0.8,
    hand_phone_distance_norm=0.05,
    hand_phone_overlap=True,
)


class FakeComponent:
    def __init__(self, output, skip_ts=()):
        self.output = output
        self.skip_ts = set(skip_ts)
        self.calls = []
        self.opened = self.closed = False

    def open(self):
        self.opened = True

    def close(self):
        self.closed = True

    def extract(self, frame, *extra):
        self.calls.append((frame.timestamp_ms, *extra))
        return None if frame.timestamp_ms in self.skip_ts else self.output


def make_extractor(phone=True, hand=True, **skip_ts):
    """skip_ts: bileşen adı → atlanacak zaman damgaları (ör. phone=(100,))."""
    return FeatureExtractor(
        face=FakeComponent(FACE, skip_ts.get("face_skip", ())),
        phone=FakeComponent(PHONE, skip_ts.get("phone_skip", ())) if phone else None,
        hand=FakeComponent(HAND, skip_ts.get("hand_skip", ())) if hand else None,
    )


# --- Birleştirici --------------------------------------------------------------------


def test_merges_all_components_into_one_record():
    extractor = make_extractor()
    with extractor:
        records = list(extractor.process(FakeVideoSource.regular("S1", 3, fps=10)))
    assert [r.timestamp_ms for r in records] == [0, 100, 200]
    r = records[0]
    assert r.feature_version == build_feature_version(True, True)
    assert (r.face_status, r.phone_status, r.hand_status) == (
        FaceStatus.VALID,
        PhoneStatus.VISIBLE,
        HandStatus.VALID,
    )
    assert r.head_pitch_deg == 20.0 and r.phone_score == 0.8 and r.hand_count == 2
    assert r.hand_phone_overlap is True
    flags = r.validity_flags
    assert flags.head_pose_valid and flags.eye_features_valid
    assert flags.hand_features_valid and flags.phone_features_valid
    assert extractor.face.opened and extractor.face.closed


def test_hand_receives_phone_output_of_same_frame():
    extractor = make_extractor()
    extractor.extract(next(iter(FakeVideoSource.regular("S1", 1))))
    assert extractor.hand.calls == [(0, PHONE)]


def test_disabled_components_are_not_evaluated():
    extractor = make_extractor(phone=False, hand=False)
    r = extractor.extract(next(iter(FakeVideoSource.regular("S1", 1))))
    assert r.phone_status is PhoneStatus.NOT_EVALUATED
    assert r.hand_status is HandStatus.NOT_EVALUATED
    assert r.phone_score is None and r.hand_count is None
    assert not r.validity_flags.phone_features_valid
    assert not r.validity_flags.hand_features_valid
    assert r.feature_version.endswith("+phone-off+hand-off")


def test_face_component_is_required():
    with pytest.raises(ValueError):
        FeatureExtractor(face=None)


def test_frame_skipped_by_any_component_yields_no_record():
    extractor = make_extractor(phone_skip=(100,))
    records = list(extractor.process(FakeVideoSource.regular("S1", 3, fps=10)))
    assert [r.timestamp_ms for r in records] == [0, 200]


def test_non_ok_frames_are_not_processed():
    extractor = make_extractor()
    bad = FrameRecord("S1", 0, 0, None, SourceStatus.READ_ERROR)
    assert extractor.extract(bad) is None
    assert extractor.face.calls == []


# --- Yerel depo ----------------------------------------------------------------------


def records_for(session="P01_SCENARIO", n=3):
    extractor = make_extractor(phone=True, hand=False)
    frames = FakeVideoSource.regular(session, n, fps=10)
    return list(extractor.process(frames))


def test_store_round_trip(tmp_path):
    store = FeatureStore(tmp_path / "local_data" / "derived_features")
    records = records_for()
    path = store.write(records, meta={"source_id": "fake"})
    assert path.parent.name == records[0].feature_version
    assert path.name == "P01_SCENARIO.csv"
    back = store.read(records[0].feature_version, "P01_SCENARIO")
    assert back == records
    meta = store.read_meta(records[0].feature_version, "P01_SCENARIO")
    assert meta["n_records"] == 3 and meta["source_id"] == "fake"
    assert meta["schema_version"] == "0.2.0"


def test_store_writes_only_feature_columns(tmp_path):
    store = FeatureStore(tmp_path / "local_data")
    path = store.write(records_for())
    header = path.read_text(encoding="utf-8").splitlines()[0].split(",")
    assert header == COLUMNS
    assert "frame" not in header


def test_store_refuses_overwrite_without_flag(tmp_path):
    store = FeatureStore(tmp_path / "local_data")
    store.write(records_for())
    with pytest.raises(FileExistsError):
        store.write(records_for())
    store.write(records_for(), overwrite=True)


def test_store_must_live_under_local_data(tmp_path):
    with pytest.raises(ValueError):
        FeatureStore(tmp_path / "somewhere_else")
    FeatureStore(tmp_path / "somewhere_else", allow_outside_local_data=True)


def test_store_rejects_mixed_sessions_and_unsafe_names(tmp_path):
    store = FeatureStore(tmp_path / "local_data")
    with pytest.raises(ValueError):
        store.write(records_for("A") + records_for("B"))
    with pytest.raises(ValueError):
        store.path_for("v1", "../disari")
    with pytest.raises(ValueError):
        store.write([])


# --- Komut satırı --------------------------------------------------------------------


def test_cli_extracts_features_from_video(tmp_path, monkeypatch, capsys):
    video = tmp_path / "synthetic.avi"
    writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"MJPG"), 10.0, (64, 48))
    for i in range(5):
        writer.write(np.full((48, 64, 3), i * 40, dtype=np.uint8))
    writer.release()
    monkeypatch.setattr(cli, "build_extractor", lambda args: make_extractor())
    out = tmp_path / "local_data" / "derived_features"

    assert cli.main(["--video", str(video), "--session-id", "P01_SCENARIO", "--out", str(out)]) == 0
    assert "5 kare" in capsys.readouterr().out
    store = FeatureStore(out)
    version = build_feature_version(True, True)
    assert len(store.read(version, "P01_SCENARIO")) == 5
    meta = store.read_meta(version, "P01_SCENARIO")
    assert meta["frames_read"] == 5 and meta["nominal_fps"] == pytest.approx(10.0)


def test_from_models_builds_real_components(tmp_path):
    extractor = FeatureExtractor.from_models(tmp_path, phone=False, hand=True, mirrored=True)
    assert extractor.phone is None
    assert extractor.hand.mirrored is True
