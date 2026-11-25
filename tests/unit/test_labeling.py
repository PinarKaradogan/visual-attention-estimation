import csv

import pytest

from visual_attention.core import (
    HumanLabelInterval,
    Label,
    LabelRound,
    LabelValidity,
    TrainLabel,
)
from visual_attention.labeling import (
    SessionType,
    coverage,
    parse_elan_filename,
    read_elan_tsv,
    second_references,
    select_retest_segment,
    window_train_label,
    write_retest_plan,
)

M, T, D, B = "MATERYAL", "TELEFON", "DIS_YON", "BELIRSIZ"


def ivs(*spans, session="P01_SCENARIO"):
    """(start_ms, end_ms, label) üçlülerinden aralık listesi."""
    return [HumanLabelInterval(session, "A1", "r1", s, e, lab, "lp-0.2") for s, e, lab in spans]


def write_tsv(path, rows, header=("start_ms", "end_ms", "label")):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(header)
        w.writerows(rows)
    return path


# --- Dosya adı ve okuma -----------------------------------------------------


def test_parse_filename():
    info = parse_elan_filename("local_data/labels/P03_SCENARIO_r1_A1.tsv")
    assert info.participant_id == "P03"
    assert info.session_type is SessionType.SCENARIO
    assert info.label_round is LabelRound.R1
    assert info.annotator_id == "A1"
    assert info.session_id == "P03_SCENARIO"


@pytest.mark.parametrize(
    "name",
    ["P3_SCENARIO_r1_A1.tsv", "P03_scenario_r1_A1.tsv", "P03_FREE_r3_A1.tsv", "P03_FREE_r1.tsv",
     "Ayse_SCENARIO_r1_A1.tsv", "P03_FREE_r1_A1.csv"],
)  # fmt: skip
def test_parse_filename_rejects_nonconforming(name):
    with pytest.raises(ValueError):
        parse_elan_filename(name)


def test_read_elan_tsv_sorts_and_warns_short(tmp_path):
    path = write_tsv(
        tmp_path / "P01_FREE_r2_A2.tsv",
        [[3000, 3400, D], [0, 3000, M], [3400, 6000, T]],
    )
    f = read_elan_tsv(path, "lp-0.2")
    assert [iv.start_ms for iv in f.intervals] == [0, 3000, 3400]
    assert f.intervals[0].session_id == "P01_FREE"
    assert f.intervals[0].label_round is LabelRound.R2
    assert len(f.warnings) == 1 and "400 ms" in f.warnings[0]


@pytest.mark.parametrize(
    "rows,header",
    [
        ([[0, 1000, "PHONE"]], None),  # sözlük dışı
        ([[0, 1000, "GECIS"]], None),  # GECIS etiketlenmez
        ([[0, 2000, M], [1500, 3000, T]], None),  # çakışma
        ([["0.0", "1000", M]], None),  # ondalık ms
        ([[0, 1000]], None),  # eksik sütun
        ([[0, 1000, M]], ("Begin", "End", "Value")),  # yanlış başlık
    ],
)
def test_read_elan_tsv_rejects_invalid(tmp_path, rows, header):
    kwargs = {"header": header} if header else {}
    path = write_tsv(tmp_path / "P01_SCENARIO_r1_A1.tsv", rows, **kwargs)
    with pytest.raises(ValueError):
        read_elan_tsv(path, "lp-0.2")


# --- Kapsama ---------------------------------------------------------------


def test_coverage_counts_unlabeled_gap():
    cov = coverage(ivs((0, 400, M), (600, 1000, B)), 0, 1000)
    assert cov.by_label[Label.MATERYAL] == 400
    assert cov.uncertain_ms == 400
    assert cov.unlabeled_ms == 200
    assert cov.unknown_ms == 600


# --- 1 sn referans (§5.2) ----------------------------------------------------


@pytest.mark.parametrize(
    "spans,label,validity",
    [
        ([(0, 501, T), (501, 1000, M)], Label.TELEFON, LabelValidity.LABELED),  # 501 > 500
        ([(0, 500, T), (500, 1000, M)], Label.GECIS, LabelValidity.LABELED),  # 500/500
        ([(0, 400, M), (400, 1000, B)], Label.BELIRSIZ, LabelValidity.UNCERTAIN),
        ([(0, 400, M)], Label.BELIRSIZ, LabelValidity.UNLABELED),  # 600 ms boşluk
        ([(0, 500, M)], Label.BELIRSIZ, LabelValidity.UNLABELED),  # tam 500 ms boşluk
        ([(0, 499, M), (499, 600, T)], Label.GECIS, LabelValidity.LABELED),  # 400 ms boşluk
        ([(0, 300, M), (300, 600, T), (600, 1000, D)], Label.GECIS, LabelValidity.LABELED),
    ],
)
def test_second_reference_rules(spans, label, validity):
    ref = second_references(ivs(*spans), 1000)[0]
    assert (ref.label, ref.validity) == (label, validity)


def test_second_references_cover_session_and_never_default_to_materyal():
    refs = second_references(ivs((0, 3000, M)), 5500)
    assert len(refs) == 6  # ceil(5,5 sn)
    assert [r.label for r in refs[:3]] == [Label.MATERYAL] * 3
    # Etiketsiz kayıt sonu MATERYAL sayılmaz
    assert all(r.label is Label.BELIRSIZ for r in refs[3:])
    assert all(r.validity is LabelValidity.UNLABELED for r in refs[3:])


def test_second_references_reject_mixed_or_out_of_range():
    with pytest.raises(ValueError):
        second_references(ivs((0, 1000, M)) + ivs((1000, 2000, M), session="P02_FREE"), 2000)
    with pytest.raises(ValueError):
        second_references(ivs((0, 3000, M)), 2000)
    with pytest.raises(ValueError):
        second_references([], 2000)


# --- Pencere eğitim hedefi (§5.3) -------------------------------------------


@pytest.mark.parametrize(
    "spans,expected",
    [
        ([(0, 1001, T), (1001, 2000, M)], TrainLabel.TELEFON),  # 1001 > 1000
        ([(0, 999, T), (999, 2000, M)], TrainLabel.MATERYAL),  # MATERYAL 1001
        ([(0, 1000, T), (1000, 2000, M)], TrainLabel.GECIS),  # 1000/1000
        ([(0, 700, T), (700, 1400, D), (1400, 2000, M)], TrainLabel.GECIS),  # üç sınıf
        ([(0, 1000, B), (1000, 2000, M)], TrainLabel.UNUSED),  # bilinmeyen = yarı
        ([(0, 900, B), (1100, 2000, M)], TrainLabel.UNUSED),  # 900 B + 200 boş
        ([(0, 999, B), (999, 2000, D)], TrainLabel.DIS_YON),  # bilinmeyen < yarı
    ],
)
def test_window_train_label_rules(spans, expected):
    assert window_train_label(ivs(*spans), 0, 2000) is expected


def test_window_train_label_works_for_shifted_and_3s_windows():
    labels = ivs((0, 2500, M), (2500, 6000, T))
    assert window_train_label(labels, 1000, 3000) is TrainLabel.MATERYAL
    assert window_train_label(labels, 2000, 4000) is TrainLabel.TELEFON
    assert window_train_label(labels, 1000, 4000) is TrainLabel.GECIS  # 1500/1500, 3 sn


# --- Tekrar seti (§7.1) ------------------------------------------------------


def scenario_labels(session="P01_SCENARIO"):
    # 20 dk; TELEFON ve DIS_YON yalnız 900–960 sn arasında
    return ivs((0, 900_000, M), (900_000, 930_000, T), (930_000, 960_000, D),
               (960_000, 1_200_000, M), session=session)  # fmt: skip


def test_retest_segment_is_quarter_and_deterministic():
    a = select_retest_segment("P01_SCENARIO", 1_200_000, scenario_labels())
    b = select_retest_segment("P01_SCENARIO", 1_200_000, scenario_labels())
    assert a == b
    assert a.duration_ms == 300_000  # 5 dk
    assert 0 <= a.start_ms and a.end_ms <= 1_200_000
    assert a.start_ms % 1000 == 0


def test_retest_segment_contains_both_classes():
    seg = select_retest_segment("P01_SCENARIO", 1_200_000, scenario_labels())
    assert seg.classes_found
    assert seg.start_ms < 930_000 and seg.end_ms > 930_000  # iki sınıfı da kesiyor


def test_retest_segment_free_session_without_phone_is_noted():
    labels = ivs((0, 300_000, M), (300_000, 310_000, D), (310_000, 600_000, M),
                 session="P01_FREE")  # fmt: skip
    seg = select_retest_segment("P01_FREE", 600_000, labels)
    assert seg.duration_ms == 150_000  # 2,5 dk
    assert not seg.classes_found
    assert seg.shifts == 0


def test_retest_segment_differs_between_sessions_and_ignores_other_sessions():
    a = select_retest_segment("P01_SCENARIO", 1_200_000, scenario_labels())
    b = select_retest_segment("P02_SCENARIO", 1_200_000, scenario_labels("P02_SCENARIO"))
    assert a.seed != b.seed
    # Başka oturumun etiketleri dikkate alınmaz
    other = select_retest_segment("P03_SCENARIO", 1_200_000, scenario_labels("P01_SCENARIO"))
    assert not other.classes_found


def test_write_retest_plan(tmp_path):
    seg = select_retest_segment("P01_SCENARIO", 1_200_000, scenario_labels())
    path = tmp_path / "retest_plan.csv"
    write_retest_plan([seg], path)
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    assert rows[0]["session_id"] == "P01_SCENARIO"
    assert rows[0]["base_seed"] == "2209"
    assert rows[0]["duration_ms"] == "300000"
