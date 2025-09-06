from dataclasses import dataclass
from io import BytesIO
import math
from typing import Any, Dict

import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile

# Optional imports: we want this endpoint to work even if OCR is unavailable.
try:
    import cv2  # type: ignore
    _HAS_CV2 = True
except Exception:
    cv2 = None  # type: ignore
    _HAS_CV2 = False

try:
    from PIL import Image
    _HAS_PIL = True
except Exception:
    Image = None  # type: ignore
    _HAS_PIL = False

try:
    import pytesseract  # type: ignore
    _HAS_TESSERACT = True
except Exception:
    pytesseract = None  # type: ignore
    _HAS_TESSERACT = False


router = APIRouter()


@dataclass
class Features:
    text_area_ratio: float
    laplacian_var: float
    edge_density: float
    rectangularity: float
    saturation_mean: float
    entropy_gray: float


def _ensure_libs_available() -> None:
    if not _HAS_PIL:
        raise HTTPException(status_code=500, detail="Pillow is required on the server")
    if not _HAS_CV2:
        # Stay explicit to help operators install dependencies
        raise HTTPException(status_code=500, detail="OpenCV (opencv-python) is required on the server")


def load_image_from_bytes(data: bytes, max_side: int = 1600) -> np.ndarray:
    """Load image via Pillow from bytes, convert to RGB ndarray. Optionally resize for speed."""
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    try:
        img = Image.open(BytesIO(data)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or unsupported image file")

    w, h = img.size
    if max(w, h) > max_side:
        scale = max_side / float(max(w, h))
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    return np.array(img)


def grayscale_entropy(gray: np.ndarray) -> float:
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
    p = hist / (hist.sum() + 1e-9)
    ent = -np.sum(p * np.log2(p + 1e-12))
    return float(ent)


def largest_contour_rectangularity(gray: np.ndarray) -> float:
    edges = cv2.Canny(gray, 100, 200)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0.0
    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)
    x, y, w, h = cv2.boundingRect(largest)
    rect_area = float(max(w * h, 1))
    return float(np.clip(area / rect_area, 0.0, 1.0))


def ocr_text_area_ratio(rgb: np.ndarray) -> float:
    if not _HAS_TESSERACT:
        return 0.0
    try:
        data = pytesseract.image_to_data(rgb, output_type=pytesseract.Output.DICT)
        n = len(data.get("level", []))
        if n == 0:
            return 0.0
        H, W = rgb.shape[:2]
        total = 0.0
        for i in range(n):
            conf = data["conf"][i]
            try:
                conf = float(conf)
            except Exception:
                conf = -1.0
            if conf < 40:
                continue
            w = data["width"][i]
            h = data["height"][i]
            total += float(w * h)
        ratio = total / float(W * H)
        return float(np.clip(ratio, 0.0, 1.0))
    except Exception:
        return 0.0


def compute_features_from_rgb(rgb: np.ndarray) -> Features:
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    # Texture / sharpness
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    # Edge density
    edges = cv2.Canny(gray, 100, 200)
    edge_density = float(edges.mean() / 255.0)

    # Rectangularity
    rectangularity = largest_contour_rectangularity(gray)

    # Colorfulness (HSV saturation mean)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    saturation_mean = float(hsv[..., 1].mean() / 255.0)

    # Entropy
    entropy = grayscale_entropy(gray)

    # OCR text area ratio (optional)
    text_ratio = ocr_text_area_ratio(rgb)

    return Features(
        text_area_ratio=text_ratio,
        laplacian_var=lap_var,
        edge_density=edge_density,
        rectangularity=rectangularity,
        saturation_mean=saturation_mean,
        entropy_gray=entropy,
    )


def logistic(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def rule_based_score(feat: Features) -> float:
    # Normalize rough ranges (heuristic)
    lap_norm = -min(feat.laplacian_var / 500.0, 2.0)
    edge_norm = -min(feat.edge_density / 0.15, 2.0)
    sat_norm = -min(feat.saturation_mean / 0.5, 2.0)
    ent_norm = -min(feat.entropy_gray / 7.5, 2.0)
    rect_norm = min(feat.rectangularity / 0.8, 2.0)
    text_norm = min(feat.text_area_ratio / 0.15, 2.0)

    score = (
        2.5 * text_norm
        + 1.6 * rect_norm
        + 1.2 * ent_norm
        + 1.0 * sat_norm
        + 0.8 * edge_norm
        + 0.8 * lap_norm
    )
    return score


def classify(feat: Features):
    score = rule_based_score(feat)
    prob_doc = logistic(score)
    label = "document" if prob_doc >= 0.5 else "photo"
    return label, prob_doc, score


@router.post("/is_document", summary="Classify an uploaded image as document vs photo")
async def is_document(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Accepts an uploaded image and returns classification JSON (document vs photo)."""
    _ensure_libs_available()

    # Basic size/type check up-front using header filename and a small sniff on content
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    # Optional: quick magic number sniff to fail fast on obvious non-images
    is_image = (
        content.startswith(b"\x89PNG\r\n\x1a\n")
        or content.startswith(b"\xff\xd8\xff")
        or content.startswith(b"GIF8")
        or (content[:4] == b"RIFF" and b"WEBP" in content[:32])
    )
    if not is_image:
        # Still attempt to load via PIL to be tolerant of other formats (e.g., BMP, TIFF)
        try:
            _ = Image.open(BytesIO(content))  # type: ignore
        except Exception:
            raise HTTPException(status_code=400, detail="Unsupported image format")

    rgb = load_image_from_bytes(content)
    feat = compute_features_from_rgb(rgb)
    label, prob_doc, score = classify(feat)

    out = {
        "image": file.filename or "uploaded_image",
        "prediction": label,
        "prob_document": round(prob_doc, 4),
        "score": round(score, 4),
        "features": {
            "text_area_ratio": round(feat.text_area_ratio, 6),
            "laplacian_var": round(feat.laplacian_var, 3),
            "edge_density": round(feat.edge_density, 6),
            "rectangularity": round(feat.rectangularity, 6),
            "saturation_mean": round(feat.saturation_mean, 6),
            "entropy_gray": round(feat.entropy_gray, 6),
        },
        "notes": (
            "If prob_document >= 0.5 we predict 'document'. "
            "OCR features require pytesseract + Tesseract; if absent, text_area_ratio=0."
        ),
    }
    return out
