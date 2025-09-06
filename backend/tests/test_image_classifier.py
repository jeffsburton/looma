import unittest
from pathlib import Path

# Import the predictor
from app.services.image_classifier.image_classifier import predict_photo_probability


def _read_bytes(p: Path) -> bytes:
    with open(p, "rb") as f:
        return f.read()


class TestImageClassifier(unittest.TestCase):
    def test_predict_photo_probability_on_sample_images(self):
        """
        Opens two sample images from tests/test_images (document.jpg and photo.jpg),
        calls predict_photo_probability(bytes) for each, and prints the filename and
        resulting probability.

        This test will be skipped if either the sample images or the model weights
        are not present in the repository/environment.
        """
        here = Path(__file__).parent
        img_dir = here / "test_images"
        files = ["document.jpg", "photo.jpg"]

        # Ensure required sample images exist
        missing = [name for name in files if not (img_dir / name).exists()]
        if missing:
            self.skipTest(f"Missing test images: {missing}")

        # Ensure the model weights exist where predict_photo_probability expects them
        # predict_photo_probability resolves weights relative to its own module directory
        weights_dir = Path(__file__).parents[1] / "app" / "services" / "image_classifier"
        if not (weights_dir / "best_model.pt").exists():
            self.skipTest("best_model.pt not found; skipping inference test")

        # Run predictions and print results
        doc_path = img_dir / "document.jpg"
        photo_path = img_dir / "photo.jpg"

        doc_prob = predict_photo_probability(_read_bytes(doc_path))
        print(f"document.jpg: {doc_prob}")
        photo_prob = predict_photo_probability(_read_bytes(photo_path))
        print(f"photo.jpg: {photo_prob}")

        # Assertions per requirement
        self.assertLess(doc_prob, 0.5, msg=f"Expected document.jpg prob < 0.5, got {doc_prob}")
        self.assertGreater(photo_prob, 0.5, msg=f"Expected photo.jpg prob > 0.5, got {photo_prob}")
