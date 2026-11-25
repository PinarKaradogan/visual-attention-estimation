"""El ve bilek öznitelikleri testleri.

MediaPipe modeli gerektirmez: el ve telefon çıktıları sahte nesnelerle verilir. Model dosyası
varsa tek bir entegrasyon testi boş görüntüde "el yok" sonucunu doğrular (CI'da atlanır).
"""

import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from visual_attention.capture import FakeVideoSource, FrameRecord, SourceStatus
from visual_attention.core import FaceStatus, FeatureRecord, HandStatus, PhoneStatus
from visual_attention.features import (
    NO_HAND,
    HandFeatureExtractor,
    PhoneFeatures,
    assign_person_sides,
    features_from_hands,
    hand_phone_relation,
)


def hand_at(x, y, spread=0.02):
    """Bileği (x, y)'de, 21 noktası bileğin üstüne dizilmiş sahte el."""
    return [SimpleNamespace(x=x, y=y - i * spread / 20) for i in range(21)]


def side(name, score=0.9):
    return [SimpleNamespace(category_name=name, score=score)]


def hands_result(*hands):
    """hands: (noktalar, MediaPipe etiketi) çiftleri."""
    return SimpleNamespace(
        hand_landmarks=[h for h, _ in hands],
        handedness=[side(lbl) for _, lbl in hands],
    )


def phone(x, y, w, h, score=0.8):
    return PhoneFeatures(
        phone_status=PhoneStatus.VISIBLE if score >= 0.3 else PhoneStatus.NOT_VISIBLE,
        phone_score=score,
        phone_box_x=x,
        phone_box_y=y,
        phone_box_w=w,
        phone_box_h=h,
    )


def frame(ts, status=SourceStatus.OK, shape=(480, 640, 3)):
    pixels = None if status is SourceStatus.READ_ERROR else np.zeros(shape, np.uint8)
    return FrameRecord("S1", 0, ts, pixels, status)


# --- Kişinin sol/sağ eli -------------------------------------------------------------


def test_mediapipe_labels_are_flipped_for_unmirrored_images():
    # Aynalanmamış görüntüde MediaPipe "Left" dediği el kişinin sağ elidir.
    r = hands_result((hand_at(0.3, 0.7), "Left"), (hand_at(0.7, 0.7), "Right"))
    f = features_from_hands(r, 640, 480)
    assert (f.right_wrist_x, f.left_wrist_x) == pytest.approx((0.3, 0.7))


def test_mirrored_images_keep_mediapipe_labels():
    r = hands_result((hand_at(0.3, 0.7), "Left"), (hand_at(0.7, 0.7), "Right"))
    f = features_from_hands(r, 640, 480, mirrored=True)
    assert (f.left_wrist_x, f.right_wrist_x) == pytest.approx((0.3, 0.7))


def test_duplicate_labels_are_split_by_image_position():
    # İkisi de "Left" etiketli: aynalanmamış görüntüde soldaki el kişinin sağ eli.
    hands = [hand_at(0.7, 0.6), hand_at(0.2, 0.6)]
    sides = assign_person_sides(hands, [side("Left"), side("Left")])
    assert sides["right"][0].x == pytest.approx(0.2)
    assert sides["left"][0].x == pytest.approx(0.7)


def test_single_hand_fills_one_side_only():
    f = features_from_hands(hands_result((hand_at(0.4, 0.8), "Right")), 640, 480)
    assert f.hand_count == 1
    assert f.left_wrist_x == pytest.approx(0.4)
    assert f.right_wrist_x is None and f.right_wrist_y is None


def test_wrist_is_landmark_zero_and_clipped():
    points = hand_at(0.5, 0.5)
    points[0] = SimpleNamespace(x=1.04, y=-0.02)  # kadrajın hemen dışında
    f = features_from_hands(hands_result((points, "Left")), 640, 480)
    assert (f.right_wrist_x, f.right_wrist_y) == (1.0, 0.0)


# --- Durum ve el sayısı --------------------------------------------------------------


def test_no_hand_is_not_detected():
    f = features_from_hands(SimpleNamespace(hand_landmarks=[], handedness=[]), 640, 480)
    assert f is NO_HAND
    assert f.hand_status is HandStatus.NOT_DETECTED
    assert f.hand_count == 0
    assert f.hand_phone_distance_norm is None and f.hand_phone_overlap is None


def test_hand_count_and_status():
    r = hands_result((hand_at(0.3, 0.7), "Left"), (hand_at(0.7, 0.7), "Right"))
    f = features_from_hands(r, 640, 480)
    assert f.hand_status is HandStatus.VALID
    assert f.hand_count == 2


# --- Telefona uzanma ve telefonu tutma -----------------------------------------------


def test_distance_to_phone_center_over_diagonal():
    # Telefon merkezi (0.5, 0.5) → piksel (320, 240); bilek (0.5, 0.75) → (320, 360).
    hand = [SimpleNamespace(x=0.5, y=0.75)] * 21
    distance, overlap = hand_phone_relation([hand], phone(0.45, 0.45, 0.1, 0.1), 640, 480)
    assert distance == pytest.approx(120 / math.hypot(640, 480))
    assert overlap is False


def test_hand_inside_phone_box_overlaps():
    r = hands_result((hand_at(0.5, 0.5), "Left"))
    f = features_from_hands(r, 640, 480, phone=phone(0.45, 0.45, 0.1, 0.1))
    assert f.hand_phone_overlap is True
    assert f.hand_phone_distance_norm == pytest.approx(0.0, abs=0.01)


def test_nearest_point_of_any_hand_is_used():
    far = hand_at(0.1, 0.9)
    near = hand_at(0.6, 0.5)
    r = hands_result((far, "Left"), (near, "Right"))
    f = features_from_hands(r, 640, 480, phone=phone(0.55, 0.45, 0.1, 0.1))
    _, near_only = hand_phone_relation([near], phone(0.55, 0.45, 0.1, 0.1), 640, 480)
    assert f.hand_phone_overlap is near_only is True


def test_phone_box_below_visible_threshold_is_still_used():
    r = hands_result((hand_at(0.5, 0.5), "Left"))
    f = features_from_hands(r, 640, 480, phone=phone(0.45, 0.45, 0.1, 0.1, score=0.15))
    assert f.hand_phone_overlap is True


def test_no_phone_box_gives_none():
    r = hands_result((hand_at(0.5, 0.5), "Left"))
    no_box = PhoneFeatures(phone_status=PhoneStatus.NOT_VISIBLE, phone_score=0.0)
    for p in (None, no_box):
        f = features_from_hands(r, 640, 480, phone=p)
        assert f.hand_phone_distance_norm is None and f.hand_phone_overlap is None


def test_invalid_image_size_raises():
    with pytest.raises(ValueError):
        features_from_hands(SimpleNamespace(hand_landmarks=[]), 640, 0)


def test_as_fields_fit_feature_record():
    r = hands_result((hand_at(0.3, 0.7), "Left"))
    fields = features_from_hands(r, 640, 480, phone=phone(0.2, 0.6, 0.2, 0.2)).as_fields()
    record = FeatureRecord(
        session_id="S1",
        frame_index=0,
        timestamp_ms=0,
        feature_version="test",
        face_status=FaceStatus.NOT_DETECTED,
        phone_status=PhoneStatus.VISIBLE,
        **fields,
    )
    assert record.hand_status is HandStatus.VALID
    assert record.right_wrist_x == pytest.approx(0.3)


# --- Çıkarıcı akışı (sahte landmarker) -----------------------------------------------


class FakeLandmarker:
    def __init__(self, res):
        self.res = res
        self.timestamps = []
        self.closed = False

    def detect_for_video(self, image, timestamp_ms):
        self.timestamps.append(timestamp_ms)
        return self.res

    def close(self):
        self.closed = True


def test_extractor_skips_bad_frames_and_keeps_video_time_order():
    fake = FakeLandmarker(SimpleNamespace(hand_landmarks=[], handedness=[]))
    with HandFeatureExtractor(landmarker=fake) as hand:
        out = [
            hand.extract(frame(0)),
            hand.extract(frame(33, status=SourceStatus.READ_ERROR)),
            hand.extract(frame(66)),
            hand.extract(frame(66)),
            hand.extract(frame(50, status=SourceStatus.TIMESTAMP_ERROR)),
            hand.extract(frame(100)),
        ]
    assert [o is None for o in out] == [False, True, False, True, True, False]
    assert fake.timestamps == [0, 66, 100]
    assert fake.closed


def test_extractor_passes_phone_and_mirroring():
    fake = FakeLandmarker(hands_result((hand_at(0.5, 0.5), "Left")))
    with HandFeatureExtractor(landmarker=fake, mirrored=True) as hand:
        features = [
            hand.extract(f, phone(0.45, 0.45, 0.1, 0.1))
            for f in FakeVideoSource.regular("S1", 3, fps=10)
        ]
    assert all(f.left_wrist_x == pytest.approx(0.5) for f in features)
    assert all(f.hand_phone_overlap is True for f in features)


def test_missing_model_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        HandFeatureExtractor(tmp_path / "yok.task").open()


MODEL = Path("models/hand_landmarker.task")


@pytest.mark.skipif(not MODEL.is_file(), reason="Model dosyası yok (CI); README'deki adımla")
def test_real_model_reports_no_hand_on_blank_image():
    with HandFeatureExtractor(MODEL) as hand:
        features = hand.extract(frame(0))
    assert features is NO_HAND
