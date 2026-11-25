"""Yüz ve baş pozu öznitelikleri (MediaPipe Face Landmarker; v5 §2.4, data-schema §3.3).

Açı yönleri kişiye göre tanımlıdır (derece):

- `head_pitch_deg > 0`: baş aşağı eğik (kâğıda bakma yönü)
- `head_yaw_deg > 0`: baş kişinin sağına dönük
- `head_roll_deg > 0`: baş kişinin sağ omzuna yatık

Dayanak: MediaPipe standart yüz şablonunda x ekseni kişinin sol gözüne (aynalanmamış
görüntüde sağa), y ekseni alna, z ekseni burundan kameraya doğrudur. Yüz dönüşüm matrisi bu
şablonu kamera uzayına taşır. Pitch ve yaw burun yönünden (matrisin 3. sütunu), roll yüzün
"yukarı" yönünden (2. sütun) hesaplanır.

Göz açıklık oranı (EAR) 6 noktalı formülle (Soukupová ve Čech, 2016) ve görüntünün en-boy
oranını bozmamak için piksel koordinatlarıyla hesaplanır. Yardımcı göstergedir; bakış
noktası ölçülmez.

`face_status`: yüz bulunursa VALID, bulunmazsa NOT_DETECTED. Face Landmarker yüz başına güven
puanı vermediği için LOW_CONFIDENCE ve OCCLUDED bu sürümde üretilmez (eşik uydurulmaz).
Karede birden fazla yüz varsa en büyük yüz kullanılır.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from visual_attention.capture import FrameRecord, SourceStatus
from visual_attention.core import (
    FaceStatus,
    FeatureRecord,
    HandStatus,
    PhoneStatus,
    ValidityFlags,
)

FACE_FEATURE_VERSION = "face-0.1.0"
DEFAULT_FACE_MODEL = Path("models/face_landmarker.task")

# EAR noktaları (p1, p2, p3, p4, p5, p6): p1–p4 yatay köşeler, p2–p6 ve p3–p5 dikey çiftler.
RIGHT_EYE = (33, 160, 158, 133, 153, 144)
"""Kişinin sağ gözü (aynalanmamış görüntüde solda)."""
LEFT_EYE = (362, 385, 387, 263, 373, 380)
"""Kişinin sol gözü (aynalanmamış görüntüde sağda)."""
_MIN_LANDMARKS = max(*RIGHT_EYE, *LEFT_EYE) + 1


@dataclass(frozen=True, slots=True)
class HeadPose:
    yaw_deg: float
    pitch_deg: float
    roll_deg: float


@dataclass(frozen=True, slots=True)
class FaceFeatures:
    """Bir karenin yüz bileşeni çıktısı. Yüz yoksa sayısal alanlar None'dır."""

    face_status: FaceStatus
    head_yaw_deg: float | None = None
    head_pitch_deg: float | None = None
    head_roll_deg: float | None = None
    eye_aspect_ratio_left: float | None = None
    eye_aspect_ratio_right: float | None = None

    @property
    def head_pose_valid(self) -> bool:
        return self.head_pitch_deg is not None

    @property
    def eye_features_valid(self) -> bool:
        return self.eye_aspect_ratio_left is not None and self.eye_aspect_ratio_right is not None

    def to_feature_record(
        self, frame: FrameRecord, feature_version: str = FACE_FEATURE_VERSION
    ) -> FeatureRecord:
        """Yalnız yüz alanları dolu bir FeatureRecord üretir; el ve telefon NOT_EVALUATED."""
        return FeatureRecord(
            session_id=frame.session_id,
            frame_index=frame.frame_index,
            timestamp_ms=frame.timestamp_ms,
            feature_version=feature_version,
            face_status=self.face_status,
            hand_status=HandStatus.NOT_EVALUATED,
            phone_status=PhoneStatus.NOT_EVALUATED,
            validity_flags=ValidityFlags(
                head_pose_valid=self.head_pose_valid,
                eye_features_valid=self.eye_features_valid,
            ),
            head_yaw_deg=self.head_yaw_deg,
            head_pitch_deg=self.head_pitch_deg,
            head_roll_deg=self.head_roll_deg,
            eye_aspect_ratio_left=self.eye_aspect_ratio_left,
            eye_aspect_ratio_right=self.eye_aspect_ratio_right,
        )


NO_FACE = FaceFeatures(face_status=FaceStatus.NOT_DETECTED)


def head_pose_from_matrix(matrix: Any) -> HeadPose:
    """4×4 yüz dönüşüm matrisinden kişiye göre baş açıları (derece)."""
    rotation = np.asarray(matrix, dtype=float).reshape(4, 4)[:3, :3]
    nose = rotation[:, 2] / np.linalg.norm(rotation[:, 2])
    up = rotation[:, 1] / np.linalg.norm(rotation[:, 1])
    pitch = math.degrees(math.atan2(-nose[1], nose[2]))
    yaw = math.degrees(math.atan2(-nose[0], math.hypot(nose[1], nose[2])))
    roll = math.degrees(math.atan2(-up[0], up[1]))
    return HeadPose(yaw_deg=yaw, pitch_deg=pitch, roll_deg=roll)


def eye_aspect_ratio(points_px: Sequence[tuple[float, float]]) -> float | None:
    """6 noktadan EAR = (|p2−p6| + |p3−p5|) / (2·|p1−p4|). Göz genişliği 0 ise None."""
    p1, p2, p3, p4, p5, p6 = (np.asarray(p, dtype=float) for p in points_px)
    width = float(np.linalg.norm(p1 - p4))
    if width <= 0:
        return None
    vertical = float(np.linalg.norm(p2 - p6) + np.linalg.norm(p3 - p5))
    return vertical / (2.0 * width)


def _eye_points(landmarks: Sequence[Any], indices: Sequence[int], width: int, height: int):
    return [(landmarks[i].x * width, landmarks[i].y * height) for i in indices]


def _face_area(landmarks: Sequence[Any]) -> float:
    xs = [p.x for p in landmarks]
    ys = [p.y for p in landmarks]
    return (max(xs) - min(xs)) * (max(ys) - min(ys))


def features_from_result(result: Any, width: int, height: int) -> FaceFeatures:
    """Face Landmarker sonucunu FaceFeatures'a çevirir (MediaPipe'tan bağımsız sınanabilir)."""
    faces = list(getattr(result, "face_landmarks", None) or [])
    if not faces:
        return NO_FACE
    index = max(range(len(faces)), key=lambda i: _face_area(faces[i]))
    landmarks = faces[index]

    pose: HeadPose | None = None
    matrices = list(getattr(result, "facial_transformation_matrixes", None) or [])
    if index < len(matrices):
        pose = head_pose_from_matrix(matrices[index])

    ear_left = ear_right = None
    if len(landmarks) >= _MIN_LANDMARKS:
        ear_left = eye_aspect_ratio(_eye_points(landmarks, LEFT_EYE, width, height))
        ear_right = eye_aspect_ratio(_eye_points(landmarks, RIGHT_EYE, width, height))

    return FaceFeatures(
        face_status=FaceStatus.VALID,
        head_yaw_deg=pose.yaw_deg if pose else None,
        head_pitch_deg=pose.pitch_deg if pose else None,
        head_roll_deg=pose.roll_deg if pose else None,
        eye_aspect_ratio_left=ear_left,
        eye_aspect_ratio_right=ear_right,
    )


class FaceFeatureExtractor:
    """MediaPipe Face Landmarker'ı VIDEO modunda çalıştırır.

    Kullanım:

        with FaceFeatureExtractor() as face:
            for frame in source:
                features = face.extract(frame)  # OK olmayan karede None
    """

    def __init__(
        self,
        model_path: str | Path = DEFAULT_FACE_MODEL,
        *,
        num_faces: int = 2,
        landmarker: Any = None,
    ) -> None:
        """
        Args:
            model_path: `face_landmarker.task` dosyası (Git dışında; indirme için README).
            num_faces: En büyüğü seçilmek üzere aranacak en fazla yüz sayısı.
            landmarker: Testler için `detect_for_video(image, timestamp_ms)` sağlayan nesne.
        """
        self._model_path = Path(model_path)
        self._num_faces = num_faces
        self._landmarker = landmarker
        self._last_timestamp_ms: int | None = None

    def open(self) -> None:
        if self._landmarker is not None:
            return
        if not self._model_path.is_file():
            raise FileNotFoundError(
                f"Yüz modeli bulunamadı: {self._model_path} (indirme adımı README'de)"
            )
        from mediapipe.tasks.python import BaseOptions, vision

        options = vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(self._model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_faces=self._num_faces,
            output_facial_transformation_matrixes=True,
        )
        self._landmarker = vision.FaceLandmarker.create_from_options(options)

    def close(self) -> None:
        if self._landmarker is not None and hasattr(self._landmarker, "close"):
            self._landmarker.close()
        self._landmarker = None
        self._last_timestamp_ms = None

    def __enter__(self) -> FaceFeatureExtractor:
        self.open()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def extract(self, frame: FrameRecord) -> FaceFeatures | None:
        """Bir kareyi işler. OK olmayan ya da zamanı ilerlemeyen karede None döner."""
        if frame.source_status is not SourceStatus.OK or frame.frame is None:
            return None
        if self._last_timestamp_ms is not None and frame.timestamp_ms <= self._last_timestamp_ms:
            return None  # VIDEO modu kesin artan zaman ister
        self.open()
        self._last_timestamp_ms = frame.timestamp_ms
        height, width = frame.frame.shape[:2]
        result = self._landmarker.detect_for_video(_to_mp_image(frame.frame), frame.timestamp_ms)
        return features_from_result(result, width, height)


def _to_mp_image(frame_bgr: np.ndarray) -> Any:
    import cv2
    import mediapipe as mp

    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    return mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
