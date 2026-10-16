import numpy as np

from pdf_ocr_extractor.preprocess import OpenCvPreprocessor


def test_color_image_becomes_binary_single_channel():
    rng = np.random.default_rng(0)
    img = rng.integers(0, 256, size=(40, 60, 3), dtype=np.uint8)
    out = OpenCvPreprocessor().process(img)
    assert out.shape == (40, 60)
    assert set(np.unique(out)) <= {0, 255}


def test_grayscale_input_is_accepted():
    img = np.full((10, 10), 200, dtype=np.uint8)
    img[3:6, 3:6] = 10
    out = OpenCvPreprocessor().process(img)
    assert out.shape == (10, 10)
    assert set(np.unique(out)) <= {0, 255}
