"""Telefon tespiti testleri.

MediaPipe modeli gerektirmez: dedektör çıktısı sahte nesnelerle verilir. Model dosyası varsa
tek bir entegrasyon testi gürültü görüntüsünde "telefon yok" sonucunu doğrular (CI'da atlanır).
"""

from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from visual_attention.capture import FakeVideoSource, FrameRecord, SourceStatus
from visual_attention.core import FaceStatus, FeatureRecord, HandStatus, PhoneStatus
from visual_attention.features import (
    PhoneFeatureExtractor,
    features_from_detections,
)


def detection(x, y, w, h, score, name="cell phone"):
    return SimpleNamespace(
        bounding_box=SimpleNamespace(origin_x=x, origin_y=y, width=w, height=h),
        categories=[SimpleNamespace(category_name=name, score=score)],
    )


def result(*detections):
    return SimpleNamespace(detections=list(detections))


def frame(ts, status=SourceStatus.OK, shape=(480, 640, 3)):
    pixels = None if status is SourceStatus.READ_ERROR else np.zeros(shape, np.uint8)
    return FrameRecord("S1", 0, ts, pixels, status)


# --- Sonuçtan özniteliğe -------------------------------------------------------------


def test_no_detection_is_not_visible_with_zero_score():
    f = features_from_detections(result(), 640, 480)
    assert f.phone_status is PhoneStatus.NOT_VISIBLE
    assert f.phone_score == 0.0
    assert f.phone_box_x is None and f.phone_box_w is None


def test_visible_phone_box_is_normalized():
    f = features_from_detections(result(detection(320, 240, 64, 96, 0.8)), 640, 480)
    assert f.phone_status is PhoneStatus.VISIBLE
    assert f.phone_score == pytest.approx(0.8)
    assert (f.phone_box_x, f.phone_box_y) == pytest.approx((0.5, 0.5))
    assert (f.phone_box_w, f.phone_box_h) == pytest.approx((0.1, 0.2))


@pytest.mark.parametrize(
    ("score", "status"),
    [(0.29, PhoneStatus.NOT_VISIBLE), (0.3, PhoneStatus.VISIBLE), (0.31, PhoneStatus.VISIBLE)],
)
def test_visible_threshold_boundary(score, status):
    f = features_from_detections(result(detection(0, 0, 10, 10, score)), 640, 480)
    assert f.phone_status is status
    assert f.phone_score == pytest.approx(score)
    assert f.phone_box_x is not None  # eşik altında da kutu ve puan tutulur


def test_custom_visible_threshold():
    r = result(detection(0, 0, 10, 10, 0.4))
    assert features_from_detections(r, 640, 480, visible_threshold=0.5).phone_status is (
        PhoneStatus.NOT_VISIBLE
    )


def test_highest_scoring_phone_is_used():
    r = result(detection(0, 0, 64, 48, 0.4), detection(320, 240, 64, 48, 0.9))
    f = features_from_detections(r, 640, 480)
    assert f.phone_score == pytest.approx(0.9)
    assert f.phone_box_x == pytest.approx(0.5)


def test_box_outside_image_is_clipped():
    f = features_from_detections(result(detection(-32, 400, 96, 160, 0.7)), 640, 480)
    assert f.phone_box_x == 0.0
    assert f.phone_box_w == pytest.approx(64 / 640)
    assert f.phone_box_y + f.phone_box_h == pytest.approx(1.0)
    for v in (f.phone_box_x, f.phone_box_y, f.phone_box_w, f.phone_box_h):
        assert 0.0 <= v <= 1.0


def test_other_categories_are_ignored():
    f = features_from_detections(result(detection(0, 0, 10, 10, 0.9, name="book")), 640, 480)
    assert f.phone_status is PhoneStatus.NOT_VISIBLE
    assert f.phone_score == 0.0


def test_invalid_image_size_raises():
    with pytest.raises(ValueError):
        features_from_detections(result(), 0, 480)


def test_as_fields_fit_feature_record():
    fields = features_from_detections(
        result(detection(320, 240, 64, 96, 0.8)), 640, 480
    ).as_fields()
    record = FeatureRecord(
        session_id="S1",
        frame_index=0,
        timestamp_ms=0,
        feature_version="test",
        face_status=FaceStatus.NOT_DETECTED,
        hand_status=HandStatus.NOT_EVALUATED,
        **fields,
    )
    assert record.phone_status is PhoneStatus.VISIBLE
    assert record.phone_score == pytest.approx(0.8)


# --- Çıkarıcı akışı (sahte dedektör) -------------------------------------------------


class FakeDetector:
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
    fake = FakeDetector(result())
    with PhoneFeatureExtractor(detector=fake) as phone:
        out = [
            phone.extract(frame(0)),
            phone.extract(frame(33, status=SourceStatus.READ_ERROR)),
            phone.extract(frame(66)),
            phone.extract(frame(66)),
            phone.extract(frame(50, status=SourceStatus.TIMESTAMP_ERROR)),
            phone.extract(frame(100)),
        ]
    assert [o is None for o in out] == [False, True, False, True, True, False]
    assert fake.timestamps == [0, 66, 100]
    assert fake.closed


def test_extractor_uses_frame_size_and_threshold():
    fake = FakeDetector(result(detection(32, 24, 32, 24, 0.35)))
    with PhoneFeatureExtractor(detector=fake, visible_threshold=0.4) as phone:
        features = [phone.extract(f) for f in FakeVideoSource.regular("S1", 3, fps=10)]
    # FakeVideoSource varsayılan karesi 64×48
    assert all(f.phone_box_x == pytest.approx(0.5) for f in features)
    assert all(f.phone_status is PhoneStatus.NOT_VISIBLE for f in features)


@pytest.mark.parametrize(("min_score", "visible"), [(0.5, 0.3), (-0.1, 0.3), (0.1, 1.5)])
def test_invalid_thresholds_raise(min_score, visible):
    with pytest.raises(ValueError):
        PhoneFeatureExtractor(min_score=min_score, visible_threshold=visible)


def test_missing_model_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        PhoneFeatureExtractor(tmp_path / "yok.tflite").open()


MODEL = Path("models/efficientdet_lite0.tflite")


@pytest.mark.skipif(
    not MODEL.is_file(), reason="Model dosyası yok (CI); README'deki adımla indirilir"
)
def test_real_model_reports_no_phone_on_noise():
    noise = np.random.default_rng(0).integers(0, 255, (480, 640, 3), dtype=np.uint8)
    with PhoneFeatureExtractor(MODEL) as phone:
        features = phone.extract(FrameRecord("S1", 0, 0, noise))
    assert features.phone_status is PhoneStatus.NOT_VISIBLE
    assert features.phone_score < 0.3
