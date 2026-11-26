"""Sentetik kare öznitelik akışı (`FeatureRecord`).

SENTETİKTİR, GERÇEK VERİ DEĞİLDİR. Aşağıdaki değerler uydurmadır; yalnızca yazılımın
doğru çalıştığını sınamak için makul görünecek şekilde seçilmiştir. Gerçek ölçüm veya
literatür değeri değildir. M0 eşikleri, M1 eğitimi ve raporlanan hiçbir sonuç bu
değerlerden türetilmez (data-schema.md, LOSO değişmezi: eşikler yalnız eğitim
kişileriyle belirlenir).

İşaret yönleri data-schema.md §3.3 ile aynıdır: pitch > 0 baş aşağı, yaw > 0 kişinin sağı.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from visual_attention.core.labels import Label
from visual_attention.core.records import FeatureRecord, ValidityFlags
from visual_attention.core.status import FaceStatus, HandStatus, PhoneStatus
from visual_attention.synthetic.behavior import BehaviorSegment, label_at

SYNTHETIC_FEATURE_VERSION = "syn-0.1.0"
PHONE_BOX_W, PHONE_BOX_H = 0.08, 0.12
"""Uydurma telefon kutusu boyutu (normalize)."""


@dataclass(frozen=True, slots=True)
class ClassProfile:
    """Bir sınıf için uydurma ortalama ve yayılımlar."""

    pitch_deg: tuple[float, float]
    yaw_deg: tuple[float, float]
    ear: tuple[float, float]
    wrist_xy: tuple[float, float]
    wrist_motion: float  # yazma hareketinin genliği (normalize)
    phone_visible_p: float
    phone_score: tuple[float, float]
    hand_on_phone: bool


# Uydurma değerler (sentetik). Bkz. modül açıklaması.
CLASS_PROFILES: dict[Label, ClassProfile] = {
    Label.MATERYAL: ClassProfile(
        pitch_deg=(25.0, 4.0),
        yaw_deg=(0.0, 5.0),
        ear=(0.22, 0.03),
        wrist_xy=(0.55, 0.80),
        wrist_motion=0.02,
        phone_visible_p=0.0,
        phone_score=(0.0, 0.0),
        hand_on_phone=False,
    ),
    Label.TELEFON: ClassProfile(
        pitch_deg=(35.0, 5.0),
        yaw_deg=(0.0, 5.0),
        ear=(0.24, 0.03),
        wrist_xy=(0.50, 0.65),
        wrist_motion=0.005,
        phone_visible_p=0.8,
        phone_score=(0.75, 0.10),
        hand_on_phone=True,
    ),
    Label.DIS_YON: ClassProfile(
        pitch_deg=(0.0, 5.0),
        yaw_deg=(40.0, 6.0),
        ear=(0.30, 0.03),
        wrist_xy=(0.55, 0.82),
        wrist_motion=0.003,
        phone_visible_p=0.0,
        phone_score=(0.0, 0.0),
        hand_on_phone=False,
    ),
}


@dataclass(frozen=True, slots=True)
class ParticipantProfile:
    """Kişiye özgü sabit sapmalar; LOSO'nun "görülmemiş kişi" durumunu sınamak için."""

    participant_id: str
    pitch_offset_deg: float
    yaw_offset_deg: float
    roll_offset_deg: float
    ear_offset: float
    wrist_offset_x: float


def make_participant_profile(participant_id: str, rng: random.Random) -> ParticipantProfile:
    return ParticipantProfile(
        participant_id=participant_id,
        pitch_offset_deg=rng.gauss(0.0, 5.0),
        yaw_offset_deg=rng.gauss(0.0, 4.0),
        roll_offset_deg=rng.gauss(0.0, 3.0),
        ear_offset=rng.gauss(0.0, 0.02),
        wrist_offset_x=rng.gauss(0.0, 0.04),
    )


@dataclass(frozen=True)
class FeatureStreamConfig:
    """Kare akışı ayarları. Kare hızı ayarlanabilir; testler 7, 15 ve 30 FPS ile çalışır."""

    fps: float = 15.0
    timestamp_jitter: float = 0.15  # kare aralığının oranı
    frame_drop_p: float = 0.01
    face_dropouts: int = 3
    face_dropout_range_ms: tuple[int, int] = (1000, 4000)
    low_confidence_p: float = 0.02
    phone_false_positive_p: float = 0.05


def _clip01(x: float) -> float:
    return min(max(x, 0.0), 1.0)


def frame_timestamps(
    duration_ms: int, cfg: FeatureStreamConfig, rng: random.Random
) -> list[tuple[int, int]]:
    """(frame_index, timestamp_ms) çiftleri. Düşen kareler sırada boşluk bırakır.

    Zaman damgaları kesin artan ve [0, duration_ms) içindedir; sabit FPS varsayılmaz.
    """
    if cfg.fps <= 0:
        raise ValueError("fps pozitif olmalı")
    period = 1000.0 / cfg.fps
    out: list[tuple[int, int]] = []
    last = -1
    i = 0
    while True:
        nominal = i * period
        if nominal >= duration_ms:
            break
        jitter = rng.uniform(-cfg.timestamp_jitter, cfg.timestamp_jitter) * period if i else 0.0
        t = max(int(round(nominal + jitter)), last + 1)
        if t >= duration_ms:
            break
        if i == 0 or rng.random() >= cfg.frame_drop_p:
            out.append((i, t))
            last = t
        i += 1
    return out


def face_dropout_spans(
    duration_ms: int, cfg: FeatureStreamConfig, rng: random.Random
) -> tuple[tuple[int, int], ...]:
    """Yüzün bulunamadığı, birbiriyle çakışmayan [start, end) kesitleri."""
    spans: list[tuple[int, int]] = []
    lo, hi = cfg.face_dropout_range_ms
    for _ in range(cfg.face_dropouts * 20):
        if len(spans) == cfg.face_dropouts or duration_ms <= hi:
            break
        dur = rng.randint(lo, hi)
        start = rng.randint(0, duration_ms - dur)
        if all(start >= e or start + dur <= s for s, e in spans):
            spans.append((start, start + dur))
    return tuple(sorted(spans))


def _in_spans(t: int, spans: tuple[tuple[int, int], ...]) -> bool:
    return any(s <= t < e for s, e in spans)


def synthetic_feature_stream(
    behavior: tuple[BehaviorSegment, ...],
    session_id: str,
    profile: ParticipantProfile,
    rng: random.Random,
    cfg: FeatureStreamConfig | None = None,
    face_dropouts: tuple[tuple[int, int], ...] | None = None,
) -> tuple[FeatureRecord, ...]:
    """Davranış çizelgesinden kare kare `FeatureRecord` üretir."""
    cfg = cfg or FeatureStreamConfig()
    duration_ms = behavior[-1].end_ms
    if face_dropouts is None:
        face_dropouts = face_dropout_spans(duration_ms, cfg, rng)
    records: list[FeatureRecord] = []
    for frame_index, t in frame_timestamps(duration_ms, cfg, rng):
        label = label_at(behavior, t)
        records.append(
            _make_record(
                session_id,
                frame_index,
                t,
                label,
                profile,
                rng,
                cfg,
                face_lost=_in_spans(t, face_dropouts),
            )
        )
    return tuple(records)


def _make_record(
    session_id: str,
    frame_index: int,
    t: int,
    label: Label,
    profile: ParticipantProfile,
    rng: random.Random,
    cfg: FeatureStreamConfig,
    *,
    face_lost: bool,
) -> FeatureRecord:
    cp = CLASS_PROFILES[label]

    # Yüz ve baş pozu
    if face_lost:
        face_status = FaceStatus.NOT_DETECTED
    elif rng.random() < cfg.low_confidence_p:
        face_status = FaceStatus.LOW_CONFIDENCE
    else:
        face_status = FaceStatus.VALID
    face_ok = face_status is FaceStatus.VALID
    pitch = rng.gauss(*cp.pitch_deg) + profile.pitch_offset_deg if face_ok else None
    yaw = rng.gauss(*cp.yaw_deg) + profile.yaw_offset_deg if face_ok else None
    roll = rng.gauss(0.0, 3.0) + profile.roll_offset_deg if face_ok else None
    ear_mean = cp.ear[0] + profile.ear_offset
    ear_l = max(rng.gauss(ear_mean, cp.ear[1]), 0.0) if face_ok else None
    ear_r = max(rng.gauss(ear_mean, cp.ear[1]), 0.0) if face_ok else None

    # El / bilek (yazma hareketi: küçük periyodik salınım)
    phase = 2 * math.pi * t / 700.0
    rx = _clip01(
        cp.wrist_xy[0]
        + profile.wrist_offset_x
        + cp.wrist_motion * math.sin(phase)
        + rng.gauss(0, 0.005)
    )
    ry = _clip01(cp.wrist_xy[1] + cp.wrist_motion * math.cos(phase) + rng.gauss(0, 0.005))
    lx = _clip01(rx - 0.15 + rng.gauss(0, 0.005))
    ly = _clip01(ry + 0.02 + rng.gauss(0, 0.005))

    # Telefon
    false_positive = (not cp.hand_on_phone) and rng.random() < cfg.phone_false_positive_p
    visible = rng.random() < cp.phone_visible_p or false_positive
    if visible:
        phone_status = PhoneStatus.VISIBLE
        if false_positive:
            score = rng.uniform(0.3, 0.5)
            cx, cy = rng.uniform(0.1, 0.9), rng.uniform(0.6, 0.95)
        else:
            score = _clip01(rng.gauss(*cp.phone_score))
            cx, cy = rx + rng.gauss(0, 0.01), ry - 0.05 + rng.gauss(0, 0.01)
        # Kutu, features/phone.py ile aynı biçimde: sol üst köşe (x, y) + genişlik/yükseklik.
        bw, bh = PHONE_BOX_W, PHONE_BOX_H
        box = (_clip01(cx - bw / 2), _clip01(cy - bh / 2))
        dist = math.hypot(cx - rx, cy - ry) / math.sqrt(2)
        overlap = box[0] <= rx <= box[0] + bw and box[1] <= ry <= box[1] + bh
    elif cp.hand_on_phone:
        phone_status = PhoneStatus.OCCLUDED  # telefon elin arkasında kaldı
        score = box = dist = overlap = None
    else:
        phone_status = PhoneStatus.NOT_VISIBLE
        score = box = dist = overlap = None

    return FeatureRecord(
        session_id=session_id,
        frame_index=frame_index,
        timestamp_ms=t,
        feature_version=SYNTHETIC_FEATURE_VERSION,
        face_status=face_status,
        hand_status=HandStatus.VALID,
        phone_status=phone_status,
        validity_flags=ValidityFlags(
            head_pose_valid=face_ok,
            eye_features_valid=face_ok,
            hand_features_valid=True,
            phone_features_valid=visible,
        ),
        head_yaw_deg=yaw,
        head_pitch_deg=pitch,
        head_roll_deg=roll,
        eye_aspect_ratio_left=ear_l,
        eye_aspect_ratio_right=ear_r,
        hand_count=2,
        left_wrist_x=lx,
        left_wrist_y=ly,
        right_wrist_x=rx,
        right_wrist_y=ry,
        hand_phone_distance_norm=dist,
        hand_phone_overlap=overlap,
        phone_score=score,
        phone_box_x=box[0] if box else None,
        phone_box_y=box[1] if box else None,
        phone_box_w=PHONE_BOX_W if box else None,
        phone_box_h=PHONE_BOX_H if box else None,
    )
