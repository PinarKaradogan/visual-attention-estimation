"""El ve bilek öznitelikleri (MediaPipe Hand Landmarker; öneri v5 §2.4, data-schema §3.3).

Göstergeler:

- `hand_count`: algılanan el sayısı (0–2).
- `left_wrist_x/y`, `right_wrist_x/y`: **kişinin kendi** sol/sağ bileği, normalize [0, 1].
  Yazma hareketi pencere düzeyinde bu konumların değişkenliğinden hesaplanır (P4-06).
- `hand_phone_distance_norm`: ellere ait en yakın işaret noktası ile telefon kutusu merkezi
  arasındaki uzaklık / görüntü köşegeni (telefona uzanma göstergesi).
- `hand_phone_overlap`: en az bir el işaret noktası telefon kutusunun içinde mi (telefonu
  tutma göstergesi).

Sol/sağ: MediaPipe el etiketini aynalanmış (selfie) görüntüye göre verir. Aynalanmamış
kamera/video görüntüsünde "Left" etiketi kişinin **sağ** elidir; bu yüzden `mirrored=False`
iken etiket çevrilir. İki el aynı etiketi alırsa görüntüdeki konuma göre ayrılır
(aynalanmamış görüntüde kişinin sağ eli solda görünür).

Telefon kutusu: Telefon bileşeni (P4-04) bir kutu döndürdüyse, puanı `visible_threshold`
altında olsa bile kullanılır; böylece sabit bir telefon eşiği el özniteliklerine gömülmez.
El veya kutu yoksa uzaklık ve örtüşme `None`'dır.

`hand_status`: el varsa VALID, yoksa NOT_DETECTED. OCCLUDED bu sürümde üretilmez; işlenmeyen
kareler için NOT_EVALUATED birleştiricide (P4-05) yazılır.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from visual_attention.capture import FrameRecord, SourceStatus
from visual_attention.core import HandStatus
from visual_attention.features.phone import PhoneFeatures

HAND_FEATURE_VERSION = "hand-0.1.0"
DEFAULT_HAND_MODEL = Path("models/hand_landmarker.task")
WRIST = 0
"""MediaPipe el işaret noktalarında bilek indeksi."""


@dataclass(frozen=True, slots=True)
class HandFeatures:
    """Bir karenin el bileşeni çıktısı."""

    hand_status: HandStatus
    hand_count: int
    left_wrist_x: float | None = None
    left_wrist_y: float | None = None
    right_wrist_x: float | None = None
    right_wrist_y: float | None = None
    hand_phone_distance_norm: float | None = None
    hand_phone_overlap: bool | None = None

    def as_fields(self) -> dict[str, Any]:
        """FeatureRecord alan adlarıyla değerler; birleştirici (P4-05) kullanır."""
        return {
            "hand_status": self.hand_status,
            "hand_count": self.hand_count,
            "left_wrist_x": self.left_wrist_x,
            "left_wrist_y": self.left_wrist_y,
            "right_wrist_x": self.right_wrist_x,
            "right_wrist_y": self.right_wrist_y,
            "hand_phone_distance_norm": self.hand_phone_distance_norm,
            "hand_phone_overlap": self.hand_phone_overlap,
        }


NO_HAND = HandFeatures(hand_status=HandStatus.NOT_DETECTED, hand_count=0)


def _clip(value: float) -> float:
    return min(1.0, max(0.0, value))


def _label(handedness: Sequence[Any]) -> tuple[str, float]:
    best = max(handedness, key=lambda c: c.score)
    return best.category_name, best.score


def assign_person_sides(
    hands: Sequence[Sequence[Any]],
    handedness: Sequence[Sequence[Any]],
    mirrored: bool = False,
) -> dict[str, Sequence[Any]]:
    """Elleri kişinin kendi sol/sağ eline atar: {"left": noktalar, "right": noktalar}.

    Etiket aynalanmış görüntüye göre olduğundan `mirrored=False` iken çevrilir. Aynı tarafa
    iki el düşerse görüntüdeki bilek konumuna göre ayrılır.
    """
    flip = (
        {"Left": "right", "Right": "left"} if not mirrored else {"Left": "left", "Right": "right"}
    )
    labelled = []
    for points, cats in zip(hands, handedness, strict=False):
        name, score = _label(cats) if cats else ("", 0.0)
        labelled.append((flip.get(name), score, points))

    sides = [side for side, _, _ in labelled]
    if len(labelled) == 2 and (sides[0] == sides[1] or None in sides):
        # Aynalanmamış görüntüde kişinin sağ eli görüntünün solunda (küçük x) görünür.
        by_x = sorted(labelled, key=lambda item: item[2][WRIST].x)
        image_left, image_right = by_x[0][2], by_x[1][2]
        if mirrored:
            return {"left": image_left, "right": image_right}
        return {"right": image_left, "left": image_right}

    result: dict[str, Sequence[Any]] = {}
    for side, _score, points in sorted(labelled, key=lambda item: -item[1]):
        if side is not None and side not in result:
            result[side] = points
    return result


def hand_phone_relation(
    hands: Sequence[Sequence[Any]],
    phone: PhoneFeatures | None,
    width: int,
    height: int,
) -> tuple[float | None, bool | None]:
    """(telefona en yakın el noktasının uzaklığı / köşegen, el noktası kutuda mı)."""
    if not hands or phone is None or phone.phone_box_x is None:
        return None, None
    x0, y0 = phone.phone_box_x, phone.phone_box_y
    x1, y1 = x0 + phone.phone_box_w, y0 + phone.phone_box_h
    cx, cy = (x0 + x1) / 2 * width, (y0 + y1) / 2 * height
    diagonal = math.hypot(width, height)
    points = [p for hand in hands for p in hand]
    distance = min(math.hypot(p.x * width - cx, p.y * height - cy) for p in points) / diagonal
    overlap = any(x0 <= p.x <= x1 and y0 <= p.y <= y1 for p in points)
    return distance, overlap


def features_from_hands(
    result: Any,
    width: int,
    height: int,
    phone: PhoneFeatures | None = None,
    mirrored: bool = False,
) -> HandFeatures:
    """Hand Landmarker sonucunu HandFeatures'a çevirir (MediaPipe'tan bağımsız sınanabilir)."""
    if width <= 0 or height <= 0:
        raise ValueError("Görüntü boyutu pozitif olmalı")
    hands = list(getattr(result, "hand_landmarks", None) or [])[:2]
    if not hands:
        return NO_HAND
    handedness = list(getattr(result, "handedness", None) or [])
    sides = assign_person_sides(hands, handedness, mirrored)
    distance, overlap = hand_phone_relation(hands, phone, width, height)

    def wrist(side: str) -> tuple[float | None, float | None]:
        points = sides.get(side)
        if points is None:
            return None, None
        return _clip(points[WRIST].x), _clip(points[WRIST].y)

    lx, ly = wrist("left")
    rx, ry = wrist("right")
    return HandFeatures(
        hand_status=HandStatus.VALID,
        hand_count=len(hands),
        left_wrist_x=lx,
        left_wrist_y=ly,
        right_wrist_x=rx,
        right_wrist_y=ry,
        hand_phone_distance_norm=distance,
        hand_phone_overlap=overlap,
    )


class HandFeatureExtractor:
    """MediaPipe Hand Landmarker'ı VIDEO modunda çalıştırır (en fazla 2 el).

    Kullanım:

        with HandFeatureExtractor() as hand:
            for frame in source:
                phone_features = phone.extract(frame)
                features = hand.extract(frame, phone_features)  # OK olmayan karede None
    """

    def __init__(
        self,
        model_path: str | Path = DEFAULT_HAND_MODEL,
        *,
        mirrored: bool = False,
        landmarker: Any = None,
    ) -> None:
        """
        Args:
            model_path: `hand_landmarker.task` (Git dışında; indirme için README).
            mirrored: Görüntü aynalanmışsa (selfie) True. Kamera/video görüntüsü için False.
            landmarker: Testler için `detect_for_video(image, timestamp_ms)` sağlayan nesne.
        """
        self._model_path = Path(model_path)
        self.mirrored = mirrored
        self._landmarker = landmarker
        self._last_timestamp_ms: int | None = None

    def open(self) -> None:
        if self._landmarker is not None:
            return
        if not self._model_path.is_file():
            raise FileNotFoundError(
                f"El modeli bulunamadı: {self._model_path} (indirme adımı README'de)"
            )
        from mediapipe.tasks.python import BaseOptions, vision

        options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(self._model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2,
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)

    def close(self) -> None:
        if self._landmarker is not None and hasattr(self._landmarker, "close"):
            self._landmarker.close()
        self._landmarker = None
        self._last_timestamp_ms = None

    def __enter__(self) -> HandFeatureExtractor:
        self.open()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def extract(
        self, frame: FrameRecord, phone: PhoneFeatures | None = None
    ) -> HandFeatures | None:
        """Bir kareyi işler. OK olmayan ya da zamanı ilerlemeyen karede None döner."""
        if frame.source_status is not SourceStatus.OK or frame.frame is None:
            return None
        if self._last_timestamp_ms is not None and frame.timestamp_ms <= self._last_timestamp_ms:
            return None  # VIDEO modu kesin artan zaman ister
        self.open()
        self._last_timestamp_ms = frame.timestamp_ms
        height, width = frame.frame.shape[:2]
        result = self._landmarker.detect_for_video(_to_mp_image(frame.frame), frame.timestamp_ms)
        return features_from_hands(result, width, height, phone, self.mirrored)


def _to_mp_image(frame_bgr: Any) -> Any:
    import cv2
    import mediapipe as mp

    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    return mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
