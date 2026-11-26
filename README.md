# visual-attention-estimation

[![CI](https://github.com/PinarKaradogan/visual-attention-estimation/actions/workflows/ci.yml/badge.svg)](https://github.com/PinarKaradogan/visual-attention-estimation/actions/workflows/ci.yml)

## Development Setup (Windows)

### Requirements
- Python 3.11.9
- Git

### Installation
```powershell
git clone https://github.com/PinarKaradogan/visual-attention-estimation.git
cd visual-attention-estimation
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

### Validation
```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest tests/test_environment.py -v
.\.venv\Scripts\python.exe -m ruff check tests/test_environment.py
```

Expected result: 3 tests passed and Ruff checks passed.

### Model files (not in Git)
MediaPipe model files are downloaded separately into `models/` (ignored by Git).

| File | Used by | Source | License |
| --- | --- | --- | --- |
| `models/face_landmarker.task` | `features/face.py` (P4-02) | https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task ([model card](https://huggingface.co/litert-community/MediaPipe-FaceLandmarker)) | Apache 2.0 |
| `models/efficientdet_lite0.tflite` | `features/phone.py` (P4-04) | https://storage.googleapis.com/mediapipe-models/object_detector/efficientdet_lite0/int8/latest/efficientdet_lite0.tflite ([model card](https://huggingface.co/litert-community/MediaPipe-ObjectDetector-EfficientDet-Lite0), int8, SHA-256 `0720bf24…c723bb`) | Apache 2.0 |
| `models/hand_landmarker.task` | `features/hand.py` (P4-03) | https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task ([model card](https://huggingface.co/litert-community/MediaPipe-HandLandmarker-Full)) | Apache 2.0 |

```powershell
New-Item -ItemType Directory -Force models
Invoke-WebRequest https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task -OutFile models/face_landmarker.task
Invoke-WebRequest https://storage.googleapis.com/mediapipe-models/object_detector/efficientdet_lite0/int8/latest/efficientdet_lite0.tflite -OutFile models/efficientdet_lite0.tflite
Invoke-WebRequest https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task -OutFile models/hand_landmarker.task
```

Tests that need a model file are skipped when it is missing (as in CI).

Do not commit `.venv/`, real participant data or secrets.