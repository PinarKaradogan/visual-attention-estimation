"""M0, çoğunluk tabanı ve LOSO testleri (#29).

Sentetik verideki sayılar yalnızca kodun çalıştığını gösterir; sonuç olarak raporlanmaz.
"""

import pytest

from visual_attention.core import Label, TrainLabel
from visual_attention.core.records import WindowRecord
from visual_attention.labeling import SessionType
from visual_attention.methods import (
    M0RuleModel,
    M0Thresholds,
    MajorityBaseline,
    SessionData,
    check_no_leakage,
    coverage,
    inner_group_folds,
    loso_folds,
    macro_f1,
    participant_of,
    run_loso,
)
from visual_attention.synthetic import (
    FeatureStreamConfig,
    SyntheticConfig,
    generate_synthetic_session,
    synthetic_participants,
)

M, T, D, B, G = Label.MATERYAL, Label.TELEFON, Label.DIS_YON, Label.BELIRSIZ, Label.GECIS


def win(
    i=0,
    sid="P901_SCENARIO",
    *,
    valid=True,
    face=1.0,
    yaw=0.0,
    phone=0.0,
    overlap=0.0,
    label=TrainLabel.MATERYAL,
):
    return WindowRecord(
        session_id=sid,
        window_index=i,
        start_ms=i * 1000,
        end_ms=i * 1000 + 2000,
        feature_version="test",
        available_frame_count=30 if valid else 0,
        is_valid=valid,
        invalid_reason=None if valid else "NO_FRAMES",
        face_detected_ratio=face,
        aggregates={
            "head_yaw_deg_mean": yaw,
            "phone_score_mean": phone,
            "hand_phone_overlap_ratio": overlap,
        },
        train_label=label,
    )


# --- LOSO ---------------------------------------------------------------------


def test_participant_of():
    assert participant_of("P03_SCENARIO") == "P03"
    assert participant_of("P901_FREE") == "P901"
    with pytest.raises(ValueError):
        participant_of("P03")


def test_loso_each_person_tested_once_never_in_train():
    folds = loso_folds(["P03", "P01", "P02", "P01"])
    assert [f.test_participant for f in folds] == ["P01", "P02", "P03"]
    for f in folds:
        assert f.test_participant not in f.train_participants
        assert len(f.train_participants) == 2


def test_loso_needs_two_people():
    with pytest.raises(ValueError):
        loso_folds(["P01"])


def test_leakage_rejected():
    with pytest.raises(ValueError, match="Sızıntı"):
        check_no_leakage("P01", ["P02", "P01"])


def test_inner_folds_keep_people_together():
    groups = ["P1"] * 5 + ["P2"] * 3 + ["P3"] * 4 + ["P4"] * 2
    folds = inner_group_folds(groups, n_splits=5)
    assert len(folds) == 4  # kişi sayısını aşamaz
    seen = []
    for tr, va in folds:
        assert {groups[i] for i in tr}.isdisjoint({groups[i] for i in va})
        seen.extend({groups[i] for i in va})
    assert sorted(seen) == ["P1", "P2", "P3", "P4"]  # herkes bir kez doğrulamada


# --- Makro-F1 ve kapsama ----------------------------------------------------------


def test_macro_f1_only_classes_in_reference():
    ref = [M, M, M, T, T]
    pred = [M, M, M, T, T]
    assert macro_f1(ref, pred) == 1.0
    # DIS_YON referansta yok: ortalamaya girmez; yanlış DIS_YON tahmini yine de hata
    assert macro_f1([M, M, T, T], [M, D, T, T]) == pytest.approx((2 * 1 / 3 + 1.0) / 2)


def test_macro_f1_belirsiz_and_gecis_handling():
    ref = [M, M, T, T, G, B]
    pred = [M, B, T, T, M, M]
    # Rapor: BELIRSIZ tahmini F1 dışı; GECIS/BELIRSIZ referansı her zaman dışarıda
    assert macro_f1(ref, pred, covered_only=True) == 1.0
    assert coverage(ref, pred) == 0.75
    # Eşik seçimi: BELIRSIZ tahmini hata
    assert macro_f1(ref, pred, covered_only=False) < 1.0


def test_macro_f1_none_without_units():
    assert macro_f1([B, G], [M, M]) is None
    assert coverage([B, G], [M, M]) is None


# --- Çoğunluk tabanı ---------------------------------------------------------------


def test_majority_learns_most_frequent_trainable_class():
    ws = [win(i, label=TrainLabel.MATERYAL) for i in range(3)]
    ws += [win(i, label=TrainLabel.TELEFON) for i in range(3, 5)]
    ws += [win(i, label=TrainLabel.GECIS) for i in range(5, 15)]  # eğitime girmez
    m = MajorityBaseline()
    m.fit(ws)
    preds = m.predict([win(0, label=None), win(1, valid=False, label=None)])
    assert [p.label for p in preds] == [M, M]
    assert {p.model_id for p in preds} == {"MAJORITY"}


def test_majority_requires_training_windows():
    with pytest.raises(ValueError):
        MajorityBaseline().fit([win(label=TrainLabel.UNUSED)])


# --- M0 kuralları ---------------------------------------------------------------------


T0 = M0Thresholds(yaw_deg=20.0, phone_score=0.5, overlap_ratio=0.3)


@pytest.mark.parametrize(
    ("kwargs", "label", "reason"),
    [
        ({}, M, "RULE"),
        ({"phone": 0.8, "overlap": 0.6}, T, "RULE"),
        ({"phone": 0.8, "overlap": 0.1}, M, "RULE"),  # telefon görünür ama elde değil
        ({"yaw": -35.0}, D, "RULE"),  # sola dönüş de dış yön
        ({"yaw": 35.0, "phone": 0.8, "overlap": 0.6}, B, "RULE_CONFLICT"),
        ({"face": 0.49}, B, "LOW_FACE_RATIO"),
        ({"face": 0.5}, M, "RULE"),  # sınır: %50 yeterli
        ({"face": None}, B, "LOW_FACE_RATIO"),
        ({"valid": False, "face": None}, B, "INVALID_WINDOW"),
        ({"yaw": None}, M, "RULE"),  # eksik açı dış yön kanıtı değildir
    ],
)
def test_m0_rules(kwargs, label, reason):
    (p,) = M0RuleModel(thresholds=T0).predict([win(**kwargs)])
    assert (p.label, p.reason) == (label, reason)
    assert p.model_id == "M0"


def test_m0_never_outputs_gecis():
    preds = M0RuleModel(thresholds=T0).predict([win(i, yaw=i * 5.0) for i in range(10)])
    assert G not in {p.label for p in preds}


def test_m0_fit_finds_separating_thresholds():
    ws = []
    for p_i, pid in enumerate(["P901", "P902", "P903"]):
        sid = f"{pid}_SCENARIO"
        off = p_i * 2.0
        ws += [win(i, sid, yaw=3.0 + off, label=TrainLabel.MATERYAL) for i in range(20)]
        ws += [win(i, sid, yaw=40.0 + off, label=TrainLabel.DIS_YON) for i in range(20, 30)]
        ws += [win(i, sid, phone=0.8, overlap=0.9, label=TrainLabel.TELEFON) for i in range(30, 40)]
    m = M0RuleModel()
    m.fit(ws)
    assert m.selection_score == pytest.approx(1.0)
    assert 7.0 <= m.thresholds.yaw_deg <= 40.0
    assert [p.label for p in m.predict(ws)] == ([M] * 20 + [D] * 10 + [T] * 10) * 3
    assert set(m.params) >= {"yaw_deg", "phone_score", "overlap_ratio", "face_ratio_min"}


def test_m0_fit_ignores_test_person_by_construction():
    """fit yalnız verilen pencereleri görür; run_loso test kişisini vermez (aşağıda)."""
    with pytest.raises(ValueError):
        M0RuleModel().fit([win(label=TrainLabel.GECIS)])


def test_unfitted_models_raise():
    with pytest.raises(RuntimeError):
        M0RuleModel().predict([win()])
    with pytest.raises(RuntimeError):
        MajorityBaseline().predict([win()])


# --- Uçtan uca LOSO (sentetik; sonuç değildir) -----------------------------------------


@pytest.fixture(scope="module")
def synthetic_sessions(make_session_data):
    cfg = SyntheticConfig(stream=FeatureStreamConfig(fps=7.0))
    pids = synthetic_participants(4)
    return [
        make_session_data(generate_synthetic_session(p, st, config=cfg))
        for p in pids
        for st in (SessionType.SCENARIO, SessionType.FREE)
    ]


def test_session_data_rejects_foreign_windows():
    with pytest.raises(ValueError):
        SessionData("P901_SCENARIO", 4000, (win(0, "P902_SCENARIO"),), (M,) * 4)


def test_loso_end_to_end(synthetic_sessions):
    seen_train = []

    class Spy(M0RuleModel):
        def fit(self, windows):
            seen_train.append({participant_of(w.session_id) for w in windows})
            super().fit(windows)

    m0 = run_loso(synthetic_sessions, Spy)
    maj = run_loso(synthetic_sessions, MajorityBaseline)

    # Her kişinin iki oturumu da test edilir; eğitimde test kişisi yok
    assert len(m0) == len(maj) == 8
    for r, train in zip(m0[::2], seen_train, strict=True):
        assert r.test_participant not in train and len(train) == 3
    assert {r.session_type for r in m0} == {"SCENARIO", "FREE"}

    # Çoğunluk tabanı: hep MATERYAL; senaryoda hiçbir kesinti olayını bulamaz
    for r in maj:
        assert set(r.predicted) <= {M, B}
        if r.session_type == "SCENARIO":
            assert r.errors.events.f1 == 0.0

    # Kodun doğru bağlandığının kontrolü: ayrılabilir sentetik veride M0 tabanı geçer
    def mean_f1(rs):
        return sum(r.macro_f1 for r in rs) / len(rs)

    assert mean_f1(m0) > mean_f1(maj) + 0.3
    for r in m0:
        assert 0.0 <= r.coverage <= 1.0
        assert r.params["face_ratio_min"] == 0.5
