"""Tek çağrıda sentetik oturum: davranış + insan etiketi + kare öznitelikleri.

SENTETİKTİR, GERÇEK VERİ DEĞİLDİR.

Güvenlik kuralları:
- Sentetik katılımcı kodları P9 ile başlar (P901, P902, ...). Gerçek gönüllü kodlarıyla
  (P01–P10) karışmaması için başka kod reddedilir.
- Bu modül diske hiçbir şey yazmaz. Testler veriyi bellekte üretir; ELAN dosyası gerekirse
  test geçici klasörüne `write_elan_tsv` ile yazılır. Sentetik çıktı Git'e ve
  local_data/'ya konmaz, sonuç olarak raporlanmaz.
- Aynı (katılımcı, oturum türü, ana tohum) her makinede aynı oturumu verir.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field

from visual_attention.core.records import FeatureRecord
from visual_attention.core.reference import HumanLabelInterval
from visual_attention.core.status import LabelRound
from visual_attention.labeling.elan import SessionType
from visual_attention.scenario.generator import (
    Scenario,
    ScenarioConfig,
    generate_scenario,
    participant_seed,
)
from visual_attention.synthetic.behavior import (
    BehaviorSegment,
    FreeSessionConfig,
    free_behavior,
    scenario_behavior,
)
from visual_attention.synthetic.features import (
    SYNTHETIC_FEATURE_VERSION,
    FeatureStreamConfig,
    ParticipantProfile,
    face_dropout_spans,
    make_participant_profile,
    synthetic_feature_stream,
)
from visual_attention.synthetic.labels import synthetic_label_intervals

SOURCE_MODE = "SYNTHETIC"
SYNTHETIC_LABEL_VERSION = "syn-label-0.1.0"
SYNTHETIC_BASE_SEED = 2026
_SYNTHETIC_PID = re.compile(r"^P9\d{2,}$")


def check_synthetic_participant(participant_id: str) -> None:
    if not _SYNTHETIC_PID.match(participant_id):
        raise ValueError(
            f"Sentetik katılımcı kodu P9 ile başlamalı (ör. P901): {participant_id!r}. "
            "Gerçek gönüllü kodları sentetik veri için kullanılmaz."
        )


@dataclass(frozen=True)
class SyntheticConfig:
    """Bir sentetik oturumun bütün ayarları. Varsayılanlar gerçekçi gürültü içerir."""

    stream: FeatureStreamConfig = field(default_factory=FeatureStreamConfig)
    scenario: ScenarioConfig = field(default_factory=ScenarioConfig)
    free: FreeSessionConfig = field(default_factory=FreeSessionConfig)
    reaction_delay_ms: tuple[int, int] = (200, 1200)
    boundary_jitter_ms: int = 300
    belirsiz_spans: int = 1
    annotator_id: str = "A1"
    label_round: LabelRound = LabelRound.R1

    @classmethod
    def noiseless(cls, fps: float = 15.0) -> SyntheticConfig:
        """Gecikme, kaydırma, BELIRSIZ, yüz kaybı ve kare düşmesi olmayan oturum.

        Etiketler tam saniye sınırlarına oturur; "kusursuz tahmin → sıfır hata" gibi
        uçtan uca testler için.
        """
        return cls(
            stream=FeatureStreamConfig(
                fps=fps,
                timestamp_jitter=0.0,
                frame_drop_p=0.0,
                face_dropouts=0,
                low_confidence_p=0.0,
                phone_false_positive_p=0.0,
            ),
            reaction_delay_ms=(0, 0),
            boundary_jitter_ms=0,
            belirsiz_spans=0,
        )


@dataclass(frozen=True)
class SyntheticSession:
    participant_id: str
    session_type: SessionType
    base_seed: int
    duration_ms: int
    profile: ParticipantProfile
    behavior: tuple[BehaviorSegment, ...]
    label_intervals: tuple[HumanLabelInterval, ...]
    features: tuple[FeatureRecord, ...]
    face_dropouts: tuple[tuple[int, int], ...]
    scenario: Scenario | None
    fps: float
    source_mode: str = SOURCE_MODE
    feature_version: str = SYNTHETIC_FEATURE_VERSION
    label_version: str = SYNTHETIC_LABEL_VERSION

    @property
    def session_id(self) -> str:
        return f"{self.participant_id}_{self.session_type}"


def generate_synthetic_session(
    participant_id: str,
    session_type: SessionType | str = SessionType.SCENARIO,
    base_seed: int = SYNTHETIC_BASE_SEED,
    config: SyntheticConfig | None = None,
) -> SyntheticSession:
    """Sentetik bir oturum üretir (yalnızca bellekte)."""
    check_synthetic_participant(participant_id)
    cfg = config or SyntheticConfig()
    stype = SessionType(session_type)
    session_id = f"{participant_id}_{stype}"

    # Kişi profili oturumdan bağımsızdır: aynı kişinin iki oturumu aynı sapmaları taşır.
    profile = make_participant_profile(
        participant_id, random.Random(participant_seed(base_seed, f"{participant_id}:profile"))
    )
    rng = random.Random(participant_seed(base_seed, f"{session_id}:synthetic"))

    scenario: Scenario | None = None
    if stype is SessionType.SCENARIO:
        scenario = generate_scenario(participant_id, base_seed, cfg.scenario)
        behavior = scenario_behavior(scenario, rng, cfg.reaction_delay_ms)
    else:
        behavior = free_behavior(rng, cfg.free)
    duration_ms = behavior[-1].end_ms

    labels = synthetic_label_intervals(
        behavior,
        session_id,
        rng,
        annotator_id=cfg.annotator_id,
        label_round=cfg.label_round,
        label_version=SYNTHETIC_LABEL_VERSION,
        boundary_jitter_ms=cfg.boundary_jitter_ms,
        belirsiz_spans=cfg.belirsiz_spans,
    )
    dropouts = face_dropout_spans(duration_ms, cfg.stream, rng)
    features = synthetic_feature_stream(
        behavior, session_id, profile, rng, cfg.stream, face_dropouts=dropouts
    )
    return SyntheticSession(
        participant_id=participant_id,
        session_type=stype,
        base_seed=base_seed,
        duration_ms=duration_ms,
        profile=profile,
        behavior=behavior,
        label_intervals=labels,
        features=features,
        face_dropouts=dropouts,
        scenario=scenario,
        fps=cfg.stream.fps,
    )


def synthetic_participants(n: int, start: int = 901) -> list[str]:
    """P901, P902, ... biçiminde n sentetik katılımcı kodu."""
    if n <= 0:
        raise ValueError("n pozitif olmalı")
    ids = [f"P{start + i}" for i in range(n)]
    for pid in ids:
        check_synthetic_participant(pid)
    return ids
