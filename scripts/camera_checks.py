"""Web kamerası kontrolleri (#13, #32, #33, #34, H5). KAYIT ALINMAZ.

Kamera canlı izlenir; yalnız sayısal özetler (oranlar, açılar, FPS) yazdırılır ve
local_data/camera_checks/ altına CSV olarak kaydedilir. Hiçbir kare diske yazılmaz.

Kullanım (depo kökünden):
    $env:PYTHONPATH = "src"
    .\\.venv\\Scripts\\python.exe scripts\\camera_checks.py            # tüm kontroller
    .\\.venv\\Scripts\\python.exe scripts\\camera_checks.py --only pose hands

Kontroller:
    info     Kamera çözünürlüğü ve gerçek FPS
    framing  Kadraj: okuma, yazma, telefon, duvardaki işaret (yüz/el/telefon oranı)
    pose     Baş pozu yönü: aşağı, sağa, sağ omza
    hands    Kişinin sol/sağ eli ve görüntünün aynalanıp aynalanmadığı
    phone    Elde telefon: yok, masada, elde ekrana bakarken, elde yana bakarken
    fps      60 sn doğal çalışmada üç modelin işlem hızı (GPU kullanılmaz)

Her kontrolde pencere açılır; hazır olunca BOŞLUK tuşuna basın. q ile kontrol atlanır.
"""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from visual_attention.capture import FakeVideoSource, LiveVideoSource
from visual_attention.core import FaceStatus, FeatureRecord, HandStatus, PhoneStatus
from visual_attention.features import FeatureExtractor

WINDOW = "Kamera kontrolu (KAYIT YOK)"


@dataclass
class Phase:
    key: str
    instruction: str
    seconds: float = 8.0


@dataclass
class PhaseResult:
    key: str
    records: list[FeatureRecord] = field(default_factory=list)
    extract_ms: list[float] = field(default_factory=list)


CHECKS: dict[str, tuple[str, list[Phase]]] = {
    "framing": (
        "Kadraj: kamerayi kayittaki yerine koy; yuzun, ellerin ve kagit ayni anda gorunsun",
        [
            Phase("okuma", "KITABA/KAGIDA bakip OKU", 10),
            Phase("yazma", "DEFTERE YAZ (basin egik)", 10),
            Phase("telefon", "TELEFONU AL, ekrana bakip kaydir", 10),
            Phase("dis_yon", "DUVARDAKI ISARETE bak (yaklasik 45 derece yanda)", 10),
        ],
    ),
    "pose": (
        "Bas pozu yonu",
        [
            Phase("duz", "Kameraya DUZ bak"),
            Phase("asagi", "CENENI GOGSUNE indir (asagi bak)"),
            Phase("duz2", "Kameraya DUZ bak"),
            Phase("sag", "Basini KENDI SAGINA cevir"),
            Phase("duz3", "Kameraya DUZ bak"),
            Phase("sag_omuz", "KULAGINI SAG OMZUNA yaklastir"),
        ],
    ),
    "hands": (
        "Sol/sag el: elini yuzunun yaninda, avuc kameraya donuk tut",
        [
            Phase("sag_el", "Yalnizca KENDI SAG elini kaldir (sol el masanin altinda)"),
            Phase("sol_el", "Yalnizca KENDI SOL elini kaldir (sag el masanin altinda)"),
            Phase("iki_el", "IKI elini de kaldir"),
        ],
    ),
    "phone": (
        "Elde telefon (onunde kagit/defter olsun)",
        [
            Phase("yok", "Telefon KADRAJ DISINDA, kagida bak"),
            Phase("masada", "Telefonu MASAYA koy, dokunma, kagida bak"),
            Phase("elde_ekran", "Telefonu ELINE al, EKRANA bakip kaydir"),
            Phase("elde_yan", "Telefon elinde (ekran sana donuk), YANA bak"),
        ],
    ),
    "fps": (
        "Islem hizi: normal calis (oku, yaz, ara sira telefona bak)",
        [
            Phase("dogal", "NORMAL CALIS (60 sn)", 60),
        ],
    ),
}
SKIP_S = 2.5  # her adımın ilk 2,5 sn'si (tepki süresi) sayılmaz


# --- Ölçüm ------------------------------------------------------------------------------


def run_phases(source, extractor, title, phases, *, show=True):
    """Boşluk tuşuyla başlar; her adımın kayıtlarını ve kare başı işlem süresini toplar."""
    import cv2

    results = {p.key: PhaseResult(p.key) for p in phases}
    bounds, t = [], 0.0
    for p in phases:
        bounds.append((t, t + p.seconds, p))
        t += p.seconds
    start = None if show else time.monotonic()
    for frame in source:
        now = time.monotonic()
        if start is None:
            img = frame.frame.copy()
            _banner(img, [title, "Hazir olunca BOSLUK tusuna bas  (q: bu kontrolu atla)"])
            cv2.imshow(WINDOW, img)
            key = cv2.waitKey(1) & 0xFF
            if key == ord(" "):
                start = now
            elif key == ord("q"):
                return None
            continue
        elapsed = now - start
        current = next(((a, b, p) for a, b, p in bounds if a <= elapsed < b), None)
        if current is None:
            break
        a, b, phase = current
        t0 = time.perf_counter()
        record = extractor.extract(frame)
        took = (time.perf_counter() - t0) * 1000
        if record is not None and elapsed - a >= min(SKIP_S, phase.seconds / 3):
            results[phase.key].records.append(record)
            results[phase.key].extract_ms.append(took)
        if show:
            img = frame.frame.copy()
            _banner(img, [f"{phase.instruction}   ({b - elapsed:.0f})", _live_line(record)])
            cv2.imshow(WINDOW, img)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                return None
    return results


def _banner(img, lines):
    import cv2

    cv2.rectangle(img, (0, 0), (img.shape[1], 30 * len(lines) + 12), (0, 0, 0), -1)
    for i, text in enumerate(lines):
        color = (255, 255, 255) if i == 0 else (0, 255, 0)
        cv2.putText(img, text, (10, 30 + 30 * i), 0, 0.7, color, 2)


def _live_line(r: FeatureRecord | None) -> str:
    if r is None:
        return ""
    pose = (
        f"pitch {r.head_pitch_deg:+.0f} yaw {r.head_yaw_deg:+.0f} roll {r.head_roll_deg:+.0f}"
        if r.head_pitch_deg is not None
        else "yuz yok"
    )
    hands = f"el {r.hand_count}" if r.hand_count is not None else "el -"
    phone = f"telefon {r.phone_score:.2f}" if r.phone_score is not None else "telefon -"
    return f"{pose} | {hands} | {phone}"


# --- Özetler ----------------------------------------------------------------------------


def _ratio(records, pred):
    return round(100 * sum(pred(r) for r in records) / len(records), 1) if records else None


def _median(values):
    values = [v for v in values if v is not None]
    return round(statistics.median(values), 1) if values else None


def summarize(check: str, results: dict[str, PhaseResult]) -> list[dict]:
    rows = []
    for key, res in results.items():
        r = res.records
        rows.append(
            {
                "check": check,
                "phase": key,
                "n": len(r),
                "face_pct": _ratio(r, lambda x: x.face_status is FaceStatus.VALID),
                "hand_pct": _ratio(r, lambda x: x.hand_status is HandStatus.VALID),
                "two_hands_pct": _ratio(r, lambda x: x.hand_count == 2),
                "phone_visible_pct": _ratio(r, lambda x: x.phone_status is PhoneStatus.VISIBLE),
                "phone_score_median": _median([x.phone_score for x in r]),
                "phone_score_max": max((x.phone_score or 0 for x in r), default=None),
                "pitch_median": _median([x.head_pitch_deg for x in r]),
                "yaw_median": _median([x.head_yaw_deg for x in r]),
                "roll_median": _median([x.head_roll_deg for x in r]),
                "left_only_pct": _ratio(
                    r, lambda x: x.left_wrist_x is not None and x.right_wrist_x is None
                ),
                "right_only_pct": _ratio(
                    r, lambda x: x.right_wrist_x is not None and x.left_wrist_x is None
                ),
                "right_wrist_x_median": _median([x.right_wrist_x for x in r]),
                "left_wrist_x_median": _median([x.left_wrist_x for x in r]),
                "extract_ms_median": _median(res.extract_ms),
                "extract_ms_p95": round(
                    sorted(res.extract_ms)[int(0.95 * (len(res.extract_ms) - 1))], 1
                )
                if res.extract_ms
                else None,
            }
        )
    return rows


def verdicts(check: str, rows: list[dict], wall_fps: float | None) -> list[str]:
    by = {row["phase"]: row for row in rows}
    out = []

    def delta(a, b, col):
        if by.get(a, {}).get(col) is None or by.get(b, {}).get(col) is None:
            return None
        return by[a][col] - by[b][col]

    if check == "pose":
        for phase, col, need, name in (
            ("asagi", "pitch_median", 10, "asagi -> pitch artar"),
            ("sag", "yaw_median", 10, "kendi sagina -> yaw artar"),
            ("sag_omuz", "roll_median", 5, "sag omza -> roll artar"),
        ):
            d = delta(phase, "duz", col)
            ok = d is not None and d >= need
            out.append(f"{'OK ' if ok else '?? '} {name}: fark {d}")
    elif check == "hands":
        right, left = by.get("sag_el", {}), by.get("sol_el", {})
        ok_r = (right.get("right_only_pct") or 0) >= 70
        ok_l = (left.get("left_only_pct") or 0) >= 70
        out.append(
            f"{'OK ' if ok_r else '?? '} sag el -> right_wrist: %{right.get('right_only_pct')}"
        )
        out.append(f"{'OK ' if ok_l else '?? '} sol el -> left_wrist: %{left.get('left_only_pct')}")
        x = right.get("right_wrist_x_median")
        if x is not None:
            mirrored = "AYNALANMAMIS (beklenen)" if x < 0.5 else "AYNALANMIS olabilir!"
            out.append(
                f"     goruntu: sag el goruntunun {'solunda' if x < 0.5 else 'saginda'}"
                f" -> {mirrored}"
            )
    elif check == "framing":
        for row in rows:
            ok = (row["face_pct"] or 0) >= 90
            out.append(
                f"{'OK ' if ok else '!! '} {row['phase']}: yuz %{row['face_pct']}"
                " (H5 hedefi >= %90)"
            )
    elif check == "phone":
        for row in rows:
            out.append(
                f"     {row['phase']}: gorulme %{row['phone_visible_pct']}, "
                f"ortanca puan {row['phone_score_median']}, en yuksek {row['phone_score_max']}"
            )
    elif check == "fps":
        ok = wall_fps is not None and wall_fps >= 10
        out.append(f"{'OK ' if ok else '!! '} islem hizi {wall_fps} FPS (H5 hedefi >= 10, GPU'suz)")
    return out


# --- Ana akış ---------------------------------------------------------------------------


def camera_info(source, seconds: float = 3.0) -> dict:
    start = time.monotonic()
    for _ in source:
        if time.monotonic() - start >= seconds:
            break
    s = source.stats
    return {
        "check": "info",
        "phase": "kamera",
        "width_px": s.width_px,
        "height_px": s.height_px,
        "nominal_fps": s.nominal_fps,
        "measured_fps": round(s.measured_fps, 1) if s.measured_fps else None,
        "frames_read": s.frames_read,
        "dropped_by_source": s.dropped_by_source,
    }


class _ThrottledFake(FakeVideoSource):
    """Kuru çalıştırma: sahte kareleri kamera gibi saniyede ~30 kare hızında verir."""

    def frames(self):
        for frame in super().frames():
            time.sleep(1 / 30)
            yield frame


def make_source(args):
    if args.dry_run:
        return _ThrottledFake.regular("CAMERA_CHECK", n_frames=900, fps=30)
    return LiveVideoSource(args.camera, "CAMERA_CHECK", width=args.width, height=args.height)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Kamera numarası (dahili kamera 0 ise web kamerası çoğunlukla 1)",
    )
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--models", type=Path, default=Path("models"))
    ap.add_argument("--only", nargs="+", choices=["info", *CHECKS], default=None)
    ap.add_argument("--out", type=Path, default=Path("local_data/camera_checks"))
    ap.add_argument(
        "--dry-run", action="store_true", help="Kamerasız kuru çalıştırma (geliştirici testi)"
    )
    args = ap.parse_args(argv)

    selected = args.only or ["info", *CHECKS]
    all_rows: list[dict] = []
    report: list[str] = []

    if "info" in selected:
        with make_source(args) as source:
            info = camera_info(source)
        all_rows.append(info)
        report.append(
            f"KAMERA: {info['width_px']}x{info['height_px']}, nominal {info['nominal_fps']} FPS, "
            f"olculen {info['measured_fps']} FPS, dusen kare {info['dropped_by_source']}"
        )

    for check in [c for c in selected if c in CHECKS]:
        title, phases = CHECKS[check]
        if args.dry_run:
            phases = [Phase(p.key, p.instruction, 0.3) for p in phases]
        extractor = _fake_extractor() if args.dry_run else FeatureExtractor.from_models(args.models)
        with make_source(args) as source, extractor:
            results = run_phases(source, extractor, title, phases, show=not args.dry_run)
        if results is None:
            report.append(f"{check.upper()}: atlandi")
            continue
        rows = summarize(check, results)
        n = sum(len(r.records) for r in results.values())
        counted_s = sum(max(0.0, p.seconds - min(SKIP_S, p.seconds / 3)) for p in phases)
        wall_fps = round(n / counted_s, 1) if check == "fps" and counted_s else None
        all_rows.extend(rows)
        report.append(f"{check.upper()}:")
        report.extend(f"  {line}" for line in verdicts(check, rows, wall_fps))
        if check == "fps":
            report.append(
                f"  kare basi islem suresi ortanca {rows[0]['extract_ms_median']} ms, "
                f"p95 {rows[0]['extract_ms_p95']} ms"
            )

    if not args.dry_run:
        import cv2

        cv2.destroyAllWindows()

    args.out.mkdir(parents=True, exist_ok=True)
    path = args.out / f"camera_checks_{datetime.now():%Y%m%d_%H%M%S}.csv"
    columns = sorted(
        {k for row in all_rows for k in row}, key=lambda k: (k not in ("check", "phase"), k)
    )
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(all_rows)

    print("\n===== OZET (bunu kopyalayip Bahar'a gonder) =====")
    print("\n".join(report))
    print(f"Ayrintili sayilar: {path}")
    return 0


def _fake_extractor():
    """Kuru çalıştırma için sahte bileşenler (kamera ve model gerekmez)."""
    from visual_attention.features import FaceFeatures, HandFeatures, PhoneFeatures

    class Fixed:
        def __init__(self, out):
            self.out = out

        def extract(self, frame, *extra):
            return self.out

    face = FaceFeatures(FaceStatus.VALID, 0.0, 10.0, 0.0, 0.3, 0.3)
    phone = PhoneFeatures(PhoneStatus.NOT_VISIBLE, 0.0)
    hand = HandFeatures(HandStatus.VALID, 1, right_wrist_x=0.3, right_wrist_y=0.6)
    return FeatureExtractor(face=Fixed(face), phone=Fixed(phone), hand=Fixed(hand))


if __name__ == "__main__":
    sys.exit(main())
