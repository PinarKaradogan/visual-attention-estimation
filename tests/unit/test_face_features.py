"""Yüz ve baş pozu öznitelikleri testleri.

MediaPipe modeli gerektirmez: açılar bilinen döndürmelerden üretilen matrislerle, EAR bilinen
nokta konumlarıyla, akış ise sahte landmarker çıktısıyla sınanır. Model dosyası varsa tek bir
entegrasyon testi boş görüntüde "yüz yok" sonucunu doğrular (CI'da atlanır).
"""

import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from visual_attention.capture import FakeVideoSource, FrameRecord, SourceStatus
from visual_attention.core import FaceStatus, HandStatus, PhoneStatus
from visual_attention.features import (
    LEFT_EYE,
    NO_FACE,
    RIGHT_EYE,
    FaceFeatureExtractor,
    eye_aspect_ratio,
    features_from_result,
    head_pose_from_matrix,
)

# --- Yardımcılar ---------------------------------------------------------------------


def rot_x(deg):
    a = math.radians(deg)
    return np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])


def rot_y(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])


def rot_z(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])


def transform(rotation, scale=1.0, translation=(0.0, 0.0, -40.0)):
    m = np.eye(4)
    m[:3, :3] = rotation * scale
    m[:3, 3] = translation
    return m


def point(x, y):
    return SimpleNamespace(x=x, y=y)


def face_landmarks(center=(0.5, 0.5), size=0.2, n=478):
    """Yüz kutusu `size` olan sahte yüz; göz noktaları 6 noktalı EAR düzeninde yerleşik."""
    cx, cy = center
    pts = [
        point(cx + size * ((i % 20) / 19 - 0.5), cy + size * ((i // 20) / 23 - 0.5))
        for i in range(n)
    ]
    if n <= max(*RIGHT_EYE, *LEFT_EYE):
        return pts  # göz noktası taşımayan eksik sonuç
    for eye, ex in ((RIGHT_EYE, cx - size / 4), (LEFT_EYE, cx + size / 4)):
        # Normalize koordinatta göz genişliği w, dikey açıklıklar w/3.
        w = size / 8
        p1, p2, p3, p4, p5, p6 = eye
        pts[p1] = point(ex - w / 2, cy)
        pts[p4] = point(ex + w / 2, cy)
        pts[p2] = point(ex - w / 6, cy - w / 6)
        pts[p3] = point(ex + w / 6, cy - w / 6)
        pts[p6] = point(ex - w / 6, cy + w / 6)
        pts[p5] = point(ex + w / 6, cy + w / 6)
    return pts


def frame(ts, index=0, status=SourceStatus.OK, shape=(100, 200, 3)):
    pixels = None if status is SourceStatus.READ_ERROR else np.zeros(shape, np.uint8)
    return FrameRecord("S1", index, ts, pixels, status)


# --- Baş pozu: işaret yönü -----------------------------------------------------------


def test_identity_is_frontal():
    pose = head_pose_from_matrix(np.eye(4))
    assert (pose.yaw_deg, pose.pitch_deg, pose.roll_deg) == pytest.approx((0, 0, 0), abs=1e-9)


def test_head_down_gives_positive_pitch():
    # x ekseni etrafında +20°: burun (0,0,1) aşağıya (−y) döner.
    pose = head_pose_from_matrix(transform(rot_x(20)))
    assert pose.pitch_deg == pytest.approx(20)
    assert pose.yaw_deg == pytest.approx(0, abs=1e-9)
    assert pose.roll_deg == pytest.approx(0, abs=1e-9)


def test_turn_to_persons_right_gives_positive_yaw():
    # Kişinin sağı aynalanmamış görüntüde solda (−x): y etrafında −30° burnu −x'e çevirir.
    pose = head_pose_from_matrix(transform(rot_y(-30)))
    assert pose.yaw_deg == pytest.approx(30)
    assert pose.pitch_deg == pytest.approx(0, abs=1e-9)


def test_tilt_to_persons_right_shoulder_gives_positive_roll():
    # z etrafında +15°: "yukarı" vektörü (0,1,0) −x'e, yani kişinin sağ omzuna yatar.
    pose = head_pose_from_matrix(transform(rot_z(15)))
    assert pose.roll_deg == pytest.approx(15)
    assert pose.yaw_deg == pytest.approx(0, abs=1e-9)


def test_pose_ignores_scale_and_translation():
    a = head_pose_from_matrix(transform(rot_x(-10) @ rot_y(25), scale=1.7, translation=(3, 2, -55)))
    b = head_pose_from_matrix(transform(rot_x(-10) @ rot_y(25)))
    assert (a.yaw_deg, a.pitch_deg, a.roll_deg) == pytest.approx(
        (b.yaw_deg, b.pitch_deg, b.roll_deg)
    )
    assert b.pitch_deg < 0  # baş yukarı
    assert b.yaw_deg < 0  # kişinin soluna


def test_pose_accepts_flat_16_values():
    flat = transform(rot_x(20)).flatten().tolist()
    assert head_pose_from_matrix(flat).pitch_deg == pytest.approx(20)


# --- EAR ----------------------------------------------------------------------------


def test_eye_aspect_ratio_known_value():
    points = [(0, 0), (10, -5), (20, -5), (30, 0), (20, 5), (10, 5)]
    assert eye_aspect_ratio(points) == pytest.approx(20 / 60)


def test_eye_aspect_ratio_closed_eye_and_zero_width():
    assert eye_aspect_ratio([(0, 0), (10, 0), (20, 0), (30, 0), (20, 0), (10, 0)]) == 0
    assert eye_aspect_ratio([(5, 5)] * 6) is None


def test_ear_uses_pixel_coordinates():
    """Aynı normalize noktalar, 2:1 görüntüde gerçek (piksel) oranla daha kısık göz verir.

    Kare görüntüde EAR = (w/3 + w/3) / (2w) = 1/3; 200×100'de yatay mesafe iki kat
    büyüdüğü için 1/6 olur. Normalize koordinatla hesaplansaydı ikisi de 1/3 çıkardı.
    """
    result = SimpleNamespace(face_landmarks=[face_landmarks()], facial_transformation_matrixes=[])
    wide = features_from_result(result, width=200, height=100)
    square = features_from_result(result, width=100, height=100)
    assert square.eye_aspect_ratio_left == pytest.approx(1 / 3)
    assert wide.eye_aspect_ratio_left == pytest.approx(1 / 6)
    assert wide.eye_aspect_ratio_left == pytest.approx(wide.eye_aspect_ratio_right)


# --- Sonuçtan özniteliğe -------------------------------------------------------------


def test_no_face_is_not_detected_with_empty_fields():
    features = features_from_result(SimpleNamespace(face_landmarks=[]), 200, 100)
    assert features is NO_FACE
    assert features.face_status is FaceStatus.NOT_DETECTED
    assert not features.head_pose_valid and not features.eye_features_valid
    assert features.head_pitch_deg is None and features.eye_aspect_ratio_left is None


def test_largest_face_is_used():
    small = face_landmarks(center=(0.2, 0.5), size=0.1)
    large = face_landmarks(center=(0.6, 0.5), size=0.3)
    result = SimpleNamespace(
        face_landmarks=[small, large],
        facial_transformation_matrixes=[transform(rot_x(-30)), transform(rot_x(25))],
    )
    features = features_from_result(result, 200, 100)
    assert features.face_status is FaceStatus.VALID
    assert features.head_pitch_deg == pytest.approx(25)


def test_missing_matrix_keeps_ear_but_not_pose():
    result = SimpleNamespace(face_landmarks=[face_landmarks()], facial_transformation_matrixes=[])
    features = features_from_result(result, 200, 100)
    assert features.face_status is FaceStatus.VALID
    assert not features.head_pose_valid
    assert features.eye_features_valid


def test_too_few_landmarks_gives_no_ear():
    result = SimpleNamespace(
        face_landmarks=[face_landmarks(n=200)], facial_transformation_matrixes=[np.eye(4)]
    )
    features = features_from_result(result, 200, 100)
    assert features.head_pose_valid
    assert not features.eye_features_valid


def test_to_feature_record_fills_face_fields_only():
    result = SimpleNamespace(
        face_landmarks=[face_landmarks()], facial_transformation_matrixes=[transform(rot_x(20))]
    )
    record = features_from_result(result, 200, 100).to_feature_record(frame(1234, index=7))
    assert (record.session_id, record.frame_index, record.timestamp_ms) == ("S1", 7, 1234)
    assert record.feature_version == "face-0.1.0"
    assert record.face_status is FaceStatus.VALID
    assert record.hand_status is HandStatus.NOT_EVALUATED
    assert record.phone_status is PhoneStatus.NOT_EVALUATED
    assert record.head_pitch_deg == pytest.approx(20)
    assert record.validity_flags.head_pose_valid and record.validity_flags.eye_features_valid
    assert not record.validity_flags.hand_features_valid
    assert record.hand_count is None and record.phone_score is None


# --- Çıkarıcı akışı (sahte landmarker) -----------------------------------------------


class FakeLandmarker:
    def __init__(self, result):
        self.result = result
        self.timestamps = []
        self.closed = False

    def detect_for_video(self, image, timestamp_ms):
        self.timestamps.append(timestamp_ms)
        return self.result

    def close(self):
        self.closed = True


def test_extractor_skips_bad_frames_and_keeps_video_time_order():
    fake = FakeLandmarker(SimpleNamespace(face_landmarks=[]))
    with FaceFeatureExtractor(landmarker=fake) as extractor:
        out = [
            extractor.extract(frame(0)),
            extractor.extract(frame(33, status=SourceStatus.READ_ERROR)),
            extractor.extract(frame(66)),
            extractor.extract(frame(66)),  # zaman ilerlemedi
            extractor.extract(frame(50, status=SourceStatus.TIMESTAMP_ERROR)),
            extractor.extract(frame(100)),
        ]
    assert [o is None for o in out] == [False, True, False, True, True, False]
    assert fake.timestamps == [0, 66, 100]
    assert fake.closed


def test_extractor_works_with_fake_video_source():
    fake = FakeLandmarker(
        SimpleNamespace(
            face_landmarks=[face_landmarks()], facial_transformation_matrixes=[np.eye(4)]
        )
    )
    with FaceFeatureExtractor(landmarker=fake) as extractor:
        records = [
            extractor.extract(f).to_feature_record(f)
            for f in FakeVideoSource.regular("S1", n_frames=5, fps=10)
        ]
    assert [r.timestamp_ms for r in records] == [0, 100, 200, 300, 400]
    assert all(r.face_status is FaceStatus.VALID for r in records)


def test_default_searches_a_single_face():
    """num_faces=2 VIDEO modunda baş eğikken takibi kaybettiriyor (#45); varsayılan 1 kalmalı."""
    assert FaceFeatureExtractor()._num_faces == 1


def test_missing_model_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        FaceFeatureExtractor(tmp_path / "yok.task").open()


MODEL = Path("models/face_landmarker.task")


@pytest.mark.skipif(
    not MODEL.is_file(), reason="Model dosyası yok (CI); README'deki adımla indirilir"
)
def test_real_model_reports_no_face_on_blank_image():
    with FaceFeatureExtractor(MODEL) as extractor:
        features = extractor.extract(frame(0, shape=(240, 320, 3)))
    assert features is NO_FACE
