
import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import sklearn


def test_dependencies_import():
    """Temel bağımlılıkların içe aktarılabildiğini doğrular."""
    assert cv2.__version__
    assert mp.__version__
    assert np.__version__
    assert pd.__version__
    assert sklearn.__version__


def test_opencv_synthetic_image():
    """Gerçek kamera kullanmadan görüntü işlemeyi test eder."""
    image = np.zeros((480, 640, 3), dtype=np.uint8)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    assert gray.shape == (480, 640)
    assert gray.dtype == np.uint8


def test_numpy_synthetic_features():
    """Sentetik öznitelik dizisinin beklenen yapısını doğrular."""
    features = np.array(
        [[10.0, 5.0, 1.0], [15.0, 8.0, 0.0]],
        dtype=np.float32,
    )

    assert features.shape == (2, 3)
    assert np.isfinite(features).all()
