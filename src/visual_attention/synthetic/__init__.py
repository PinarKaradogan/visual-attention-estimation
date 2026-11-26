"""Sentetik test verisi üreticisi (P3-03, #17).

SENTETİKTİR, GERÇEK VERİ DEĞİLDİR. Etik izin öncesinde yazılımın uçtan uca sınanması
içindir (v5 İP5: birim testler ve yeniden üretilebilirlik). Bu veriden hiçbir sonuç, eşik
veya model türetilmez ve raporlanmaz; çıktı Git'e ve local_data/'ya yazılmaz.
"""

from visual_attention.synthetic.behavior import (
    BehaviorSegment,
    FreeSessionConfig,
    free_behavior,
    label_at,
    scenario_behavior,
)
from visual_attention.synthetic.features import (
    CLASS_PROFILES,
    SYNTHETIC_FEATURE_VERSION,
    FeatureStreamConfig,
    ParticipantProfile,
    face_dropout_spans,
    frame_timestamps,
    make_participant_profile,
    synthetic_feature_stream,
)
from visual_attention.synthetic.labels import (
    elan_filename,
    synthetic_label_intervals,
    write_elan_tsv,
)
from visual_attention.synthetic.session import (
    SOURCE_MODE,
    SYNTHETIC_BASE_SEED,
    SYNTHETIC_LABEL_VERSION,
    SyntheticConfig,
    SyntheticSession,
    check_synthetic_participant,
    generate_synthetic_session,
    synthetic_participants,
)

__all__ = [
    "CLASS_PROFILES",
    "SOURCE_MODE",
    "SYNTHETIC_BASE_SEED",
    "SYNTHETIC_FEATURE_VERSION",
    "SYNTHETIC_LABEL_VERSION",
    "BehaviorSegment",
    "FeatureStreamConfig",
    "FreeSessionConfig",
    "ParticipantProfile",
    "SyntheticConfig",
    "SyntheticSession",
    "check_synthetic_participant",
    "elan_filename",
    "face_dropout_spans",
    "frame_timestamps",
    "free_behavior",
    "generate_synthetic_session",
    "label_at",
    "make_participant_profile",
    "scenario_behavior",
    "synthetic_feature_stream",
    "synthetic_label_intervals",
    "synthetic_participants",
    "write_elan_tsv",
]
