"""Komut satırı: kayıtlı bir video dosyasından öznitelik çıkarıp yerel depoya yazar.

Örnek:
    python -m visual_attention.features --video local_data/raw_video/P01_SCENARIO.mp4 ^
        --session-id P01_SCENARIO

Çıktı: local_data/derived_features/<feature_version>/<session_id>.csv ve .meta.json.
Gerçek gönüllü videoları ancak etik izin belgesinden sonra işlenir; ham kare yazılmaz.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from visual_attention.capture import FileVideoSource
from visual_attention.core import FaceStatus, HandStatus, PhoneStatus
from visual_attention.features.extractor import FeatureExtractor
from visual_attention.storage import DEFAULT_ROOT, FeatureStore


def build_extractor(args: argparse.Namespace) -> FeatureExtractor:
    return FeatureExtractor.from_models(
        args.models, phone=not args.no_phone, hand=not args.no_hand, mirrored=args.mirrored
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--video", type=Path, required=True, help="Yerel video dosyası")
    ap.add_argument("--session-id", required=True, help="Örn. P01_SCENARIO")
    ap.add_argument("--models", type=Path, default=Path("models"))
    ap.add_argument("--out", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--no-phone", action="store_true", help="Telefon bileşenini kapat")
    ap.add_argument("--no-hand", action="store_true", help="El bileşenini kapat")
    ap.add_argument("--mirrored", action="store_true", help="Görüntü aynalanmışsa")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args(argv)

    store = FeatureStore(args.out)
    started = time.monotonic()
    with FileVideoSource(args.video, session_id=args.session_id) as source:
        with build_extractor(args) as extractor:
            records = list(extractor.process(source))
        stats = source.stats
    elapsed = time.monotonic() - started
    if not records:
        print("Hiç kare işlenemedi; dosya yazılmadı.")
        return 1

    meta = {
        "source_mode": str(stats.source_mode),
        "source_id": stats.source_id,
        "width_px": stats.width_px,
        "height_px": stats.height_px,
        "nominal_fps": stats.nominal_fps,
        "measured_fps": stats.measured_fps,
        "frames_read": stats.frames_read,
        "dropped_by_source": stats.dropped_by_source,
        "skipped_by_pipeline": stats.skipped_by_pipeline,
        "read_errors": stats.read_errors,
        "timestamp_errors": stats.timestamp_errors,
        "processing_fps": round(len(records) / elapsed, 2) if elapsed > 0 else None,
    }
    path = store.write(records, meta=meta, overwrite=args.overwrite)

    n = len(records)
    face = sum(r.face_status is FaceStatus.VALID for r in records) / n
    phone = sum(r.phone_status is PhoneStatus.VISIBLE for r in records) / n
    hand = sum(r.hand_status is HandStatus.VALID for r in records) / n
    print(
        f"{args.session_id}: {n} kare, yüz %{100 * face:.1f}, telefon %{100 * phone:.1f}, "
        f"el %{100 * hand:.1f}, işlem hızı {meta['processing_fps']} FPS\nDosya: {path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
