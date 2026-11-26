"""Telefon tespiti (MediaPipe Object Detector, EfficientDet-Lite0, COCO "cell phone").

Kaynak: öneri v5 §2.4, data-schema §3.3. Telefonun yalnız görünmesi TELEFON sınıfını
kanıtlamaz; bu bileşen el göstergeleriyle (P4-03) birlikte yorumlanır.

Çıktılar:

- `phone_score`: karedeki en yüksek "cell phone" güveni. Dedektör çalıştı ama alt sınırın
  üstünde aday bulamadıysa **0.0** (gerçek ölçüm: telefon bulunmadı). `None` yalnız kare
  işlenmediğinde kullanılır.
- `phone_box_x/y/w/h`: en yüksek puanlı kutu, görüntü genişliği/yüksekliğine göre normalize
  ve [0, 1] aralığına kırpılmış. Telefon yoksa `None`.
- `phone_status`: `phone_score ≥ visible_threshold` ise VISIBLE, değilse NOT_VISIBLE.
  OCCLUDED dedektörden anlaşılamadığı için üretilmez; işlenmeyen kareler için NOT_EVALUATED
  birleştiricide (P4-05) yazılır.

Eşikler: Dedektör alt sınırı (`min_score`) düşük tutulur, böylece zayıf adaylar da
`phone_score`'a yansır. `visible_threshold` yalnız `phone_status`'u belirleyen açıklayıcı bir
varsayılandır. M0, telefon eşiğini `phone_score` üzerinde yalnız eğitim katılımcılarından
öğrenir (risk R18); M1 `phone_score`'u doğrudan kullanır.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from visual_attention.capture import FrameRecord, SourceStatus
from visual_attention.core import PhoneStatus

PHONE_FEATURE_VERSION = "phone-0.1.0"
DEFAULT_PHONE_MODEL = Path("models/efficientdet_lite0.tflite")
PHONE_CATEGORY = "cell phone"
DEFAULT_MIN_SCORE = 0.1
DEFAULT_VISIBLE_THRESHOLD = 0.3


@dataclass(frozen=True, slots=True)
class PhoneFeatures:
    """Bir karenin telefon bileşeni çıktısı."""

    phone_status: PhoneStatus
    phone_score: float
    phone_box_x: float | None = None
    phone_box_y: float | None = None
    phone_box_w: float | None = None
    phone_box_h: float | None = None

    def as_fields(self) -> dict[str, Any]:
        """FeatureRecord alan adlarıyla değerler; birleştirici (P4-05) kullanır."""
        return {
            "phone_status": self.phone_status,
            "phone_score": self.phone_score,
            "phone_box_x": self.phone_box_x,
            "phone_box_y": self.phone_box_y,
            "phone_box_w": self.phone_box_w,
            "phone_box_h": self.phone_box_h,
        }


def _clip(value: float) -> float:
    return min(1.0, max(0.0, value))


def _phone_score(detection: Any) -> float:
    scores = [c.score for c in detection.categories if c.category_name == PHONE_CATEGORY]
    return max(scores, default=0.0)


def features_from_detections(
    result: Any,
    width: int,
    height: int,
    visible_threshold: float = DEFAULT_VISIBLE_THRESHOLD,
) -> PhoneFeatures:
    """Object Detector sonucunu PhoneFeatures'a çevirir (MediaPipe'tan bağımsız sınanabilir)."""
    if width <= 0 or height <= 0:
        raise ValueError("Görüntü boyutu pozitif olmalı")
    candidates = [(d, _phone_score(d)) for d in (getattr(result, "detections", None) or [])]
    candidates = [(d, s) for d, s in candidates if s > 0]
    if not candidates:
        return PhoneFeatures(phone_status=PhoneStatus.NOT_VISIBLE, phone_score=0.0)

    best, score = max(candidates, key=lambda item: item[1])
    box = best.bounding_box
    x0, y0 = _clip(box.origin_x / width), _clip(box.origin_y / height)
    x1 = _clip((box.origin_x + box.width) / width)
    y1 = _clip((box.origin_y + box.height) / height)
    status = PhoneStatus.VISIBLE if score >= visible_threshold else PhoneStatus.NOT_VISIBLE
    return PhoneFeatures(
        phone_status=status,
        phone_score=float(score),
        phone_box_x=x0,
        phone_box_y=y0,
        phone_box_w=x1 - x0,
        phone_box_h=y1 - y0,
    )


class PhoneFeatureExtractor:
    """MediaPipe Object Detector'ı VIDEO modunda, yalnız "cell phone" sınıfıyla çalıştırır.

    Kullanım:

        with PhoneFeatureExtractor() as phone:
            for frame in source:
                features = phone.extract(frame)  # OK olmayan karede None
    """

    def __init__(
        self,
        model_path: str | Path = DEFAULT_PHONE_MODEL,
        *,
        min_score: float = DEFAULT_MIN_SCORE,
        visible_threshold: float = DEFAULT_VISIBLE_THRESHOLD,
        max_results: int = 3,
        detector: Any = None,
    ) -> None:
        """
        Args:
            model_path: `efficientdet_lite0.tflite` (Git dışında; indirme için README).
            min_score: Dedektörün aday döndürme alt sınırı.
            visible_threshold: `phone_status = VISIBLE` için eşik (açıklayıcı varsayılan).
            max_results: Karede en fazla kaç telefon adayı döndürüleceği.
            detector: Testler için `detect_for_video(image, timestamp_ms)` sağlayan nesne.
        """
        if not 0.0 <= min_score <= visible_threshold <= 1.0:
            raise ValueError("0 ≤ min_score ≤ visible_threshold ≤ 1 olmalı")
        self._model_path = Path(model_path)
        self._min_score = min_score
        self.visible_threshold = visible_threshold
        self._max_results = max_results
        self._detector = detector
        self._last_timestamp_ms: int | None = None

    def open(self) -> None:
        if self._detector is not None:
            return
        if not self._model_path.is_file():
            raise FileNotFoundError(
                f"Telefon modeli bulunamadı: {self._model_path} (indirme adımı README'de)"
            )
        from mediapipe.tasks.python import BaseOptions, vision

        options = vision.ObjectDetectorOptions(
            base_options=BaseOptions(model_asset_path=str(self._model_path)),
            running_mode=vision.RunningMode.VIDEO,
            category_allowlist=[PHONE_CATEGORY],
            score_threshold=self._min_score,
            max_results=self._max_results,
        )
        self._detector = vision.ObjectDetector.create_from_options(options)

    def close(self) -> None:
        if self._detector is not None and hasattr(self._detector, "close"):
            self._detector.close()
        self._detector = None
        self._last_timestamp_ms = None

    def __enter__(self) -> PhoneFeatureExtractor:
        self.open()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def extract(self, frame: FrameRecord) -> PhoneFeatures | None:
        """Bir kareyi işler. OK olmayan ya da zamanı ilerlemeyen karede None döner."""
        if frame.source_status is not SourceStatus.OK or frame.frame is None:
            return None
        if self._last_timestamp_ms is not None and frame.timestamp_ms <= self._last_timestamp_ms:
            return None  # VIDEO modu kesin artan zaman ister
        self.open()
        self._last_timestamp_ms = frame.timestamp_ms
        height, width = frame.frame.shape[:2]
        result = self._detector.detect_for_video(_to_mp_image(frame.frame), frame.timestamp_ms)
        return features_from_detections(result, width, height, self.visible_threshold)


def _to_mp_image(frame_bgr: Any) -> Any:
    import cv2
    import mediapipe as mp

    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    return mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
