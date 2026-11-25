"""FileVideoSource ve FakeVideoSource testleri.

Video, geçici klasörde OpenCV ile üretilen sentetik renk karelerinden oluşur; gerçek kişi
görüntüsü yoktur ve test bitince silinir.
"""

import cv2
import numpy as np
import pytest

from visual_attention.capture import (
    FakeVideoSource,
    FileVideoSource,
    SourceMode,
    SourceStatus,
)


@pytest.fixture
def synthetic_video(tmp_path):
    path = tmp_path / "synthetic.avi"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 10.0, (64, 48))
    assert writer.isOpened()
    for i in range(15):
        writer.write(np.full((48, 64, 3), i * 15, dtype=np.uint8))
    writer.release()
    return path


def test_file_source_reads_all_frames_with_video_time(synthetic_video):
    with FileVideoSource(synthetic_video, session_id="S1") as source:
        records = list(source)

    assert [r.frame_index for r in records] == list(range(15))
    timestamps = [r.timestamp_ms for r in records]
    assert timestamps == sorted(set(timestamps))  # kesin artan
    assert timestamps[0] == 0
    assert timestamps == pytest.approx([i * 100 for i in range(15)], abs=1)
    assert all(r.source_status is SourceStatus.OK for r in records)
    assert records[0].frame.shape == (48, 64, 3)

    stats = source.stats
    assert stats.source_mode is SourceMode.FILE
    assert stats.source_id == "file"
    assert (stats.width_px, stats.height_px) == (64, 48)
    assert stats.nominal_fps == pytest.approx(10.0)
    assert stats.measured_fps == pytest.approx(10.0, rel=0.01)
    assert stats.frames_read == 15
    assert stats.dropped_by_source == 0
    assert stats.skipped_by_pipeline == 0


def test_file_source_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        FileVideoSource(tmp_path / "yok.avi", session_id="S1").open()


def test_file_source_unreadable_file_raises(tmp_path):
    bad = tmp_path / "bozuk.avi"
    bad.write_bytes(b"video degil")
    with pytest.raises(OSError):
        FileVideoSource(bad, session_id="S1").open()


def test_empty_session_id_is_rejected(synthetic_video):
    with pytest.raises(ValueError):
        FileVideoSource(synthetic_video, session_id="")


def test_fake_regular_source():
    source = FakeVideoSource.regular("S1", n_frames=31, fps=30)
    records = list(source)
    assert len(records) == 31
    assert records[-1].timestamp_ms == 1000
    assert source.stats.dropped_by_source == 0
    assert source.stats.measured_fps == pytest.approx(30.0)
    assert source.stats.source_mode is SourceMode.SYNTHETIC


def test_fake_source_gaps_count_as_dropped_frames():
    source = FakeVideoSource(
        "S1",
        timestamps_ms=[0, 100, 400, 500],
        frame_indices=[0, 1, 4, 5],
        nominal_fps=10,
    )
    records = list(source)
    assert [r.frame_index for r in records] == [0, 1, 4, 5]
    assert source.stats.dropped_by_source == 2


def test_fake_source_read_error_and_bad_timestamp():
    source = FakeVideoSource(
        "S1",
        timestamps_ms=[0, 100, 100, 300],
        read_error_indices=[3],
        nominal_fps=10,
    )
    statuses = [r.source_status for r in source]
    assert statuses == [
        SourceStatus.OK,
        SourceStatus.OK,
        SourceStatus.TIMESTAMP_ERROR,
        SourceStatus.READ_ERROR,
    ]
    assert source.stats.timestamp_errors == 1
    assert source.stats.read_errors == 1
    assert source.stats.frames_read == 3


def test_fake_source_frames_are_read_only():
    record = next(iter(FakeVideoSource.regular("S1", n_frames=1)))
    with pytest.raises(ValueError):
        record.frame[0, 0, 0] = 255
