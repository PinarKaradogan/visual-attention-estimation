import csv
import dataclasses

import pytest

from visual_attention.core import Label
from visual_attention.scenario import (
    ScenarioBlock,
    ScenarioConfig,
    generate_scenario,
    validate_scenario,
    write_scenario_csv,
)
from visual_attention.scenario.__main__ import main, parse_participants

PIDS = [f"P{i:02d}" for i in range(1, 11)]


@pytest.mark.parametrize("pid", PIDS)
def test_generated_scenarios_follow_report_rules(pid):
    s = generate_scenario(pid, base_seed=2026)
    validate_scenario(s)  # ayrıca generate içinde de çağrılır
    labels = s.to_labels()
    assert len(labels) == 1200
    assert sum(lab is Label.TELEFON for lab in labels) > 0
    durations = [b.duration_s for b in s.interruptions]
    assert len(durations) == 12
    assert sum(d < 3 for d in durations) == 1  # tam bir kısa kesinti
    assert sum(3 <= d < 5 for d in durations) >= 1  # 3–4 sn örneği
    # v5 süre aralıkları korunuyor
    for b in s.interruptions:
        lo, hi = (5, 30) if b.label is Label.TELEFON else (2, 20)
        assert lo <= b.duration_s <= hi


def test_deterministic_and_participant_specific():
    a1 = generate_scenario("P01", 2026)
    a2 = generate_scenario("P01", 2026)
    b = generate_scenario("P02", 2026)
    c = generate_scenario("P01", 2027)
    assert a1 == a2
    assert a1.blocks != b.blocks
    assert a1.blocks != c.blocks


@pytest.mark.parametrize("pid", PIDS)
def test_plan_b_feasible_for_all_participants(pid):
    # v5 risk B planı: 8 + 8 kesinti, oturum 1200 sn, v5 süre aralıkları değişmeden
    cfg = ScenarioConfig(events_per_class=8)
    s = generate_scenario(pid, 2026, cfg)
    assert len(s.interruptions) == 16
    assert len(s.to_labels()) == 1200
    assert s.config.phone_range_s == (5, 30) and s.config.away_range_s == (2, 20)


def test_at_least_five_countable_away_events_per_person():
    # Tam bir kısa kesinti kuralı: kişi başı >= 5 DIS_YON kesintisi >= 3 sn
    for pid in PIDS:
        s = generate_scenario(pid, 2026)
        away = [b for b in s.interruptions if b.label is Label.DIS_YON]
        assert sum(b.duration_s >= 3 for b in away) >= 5


def test_infeasible_config_raises():
    cfg = ScenarioConfig(events_per_class=20, max_attempts=20)
    with pytest.raises(ValueError):
        generate_scenario("P01", 2026, cfg)


def test_validate_rejects_short_material_block():
    s = generate_scenario("P01", 2026)
    blocks = list(s.blocks)
    first, second = blocks[0], blocks[1]
    # İlk MATERYAL bloğunu 59 sn'ye indir, kesintiyi öne kaydır
    shift = first.duration_s - 59
    blocks[0] = ScenarioBlock(0, 59, Label.MATERYAL)
    blocks[1] = ScenarioBlock(59, second.end_s - shift, second.label)
    blocks[2] = ScenarioBlock(second.end_s - shift, blocks[2].end_s, Label.MATERYAL)
    with pytest.raises(ValueError):
        validate_scenario(dataclasses.replace(s, blocks=tuple(blocks)))


def test_csv_export(tmp_path):
    s = generate_scenario("P03", 2026)
    path = tmp_path / "P03_scenario.csv"
    write_scenario_csv(s, path)
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    assert len(rows) == len(s.blocks)
    assert rows[0]["start"] == "00.00"
    assert rows[0]["block_no"] == "1"
    assert rows[0]["command"] == "Çalışmaya başla"
    assert rows[0]["base_seed"] == "2026"
    assert {r["actual_note"] for r in rows} == {""}
    commands = {r["label"]: r["command"] for r in rows[1:]}
    assert commands["TELEFON"] == "Telefonu al ve ekranı kaydır"
    assert commands["DIŞ_YÖN"] == "Duvardaki işarete bak"
    assert commands["MATERYAL"] == "Kâğıda dön"
    assert rows[-1]["end"] == "20.00"
    assert {r["label"] for r in rows} == {"MATERYAL", "TELEFON", "DIŞ_YÖN"}


def test_parse_participants():
    assert parse_participants("P01-P03") == ["P01", "P02", "P03"]
    assert parse_participants("P01, P05") == ["P01", "P05"]


def test_cli(tmp_path, capsys):
    assert main(["--participants", "P01-P02", "--seed", "2026", "--out", str(tmp_path)]) == 0
    assert (tmp_path / "P01_scenario.csv").exists()
    assert "P02:" in capsys.readouterr().out
