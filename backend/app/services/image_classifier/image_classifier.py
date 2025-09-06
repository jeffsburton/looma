from io import BytesIO
from pathlib import Path

from PIL import Image

import torch
import torch.nn as nn

from torchvision import transforms
from torchvision.models import resnet18

def build_eval_transform(img_size: int = 224):
    mean = [0.485, 0.456, 0.406]
    std  = [0.229, 0.224, 0.225]
    return transforms.Compose([
        transforms.Resize(int(img_size * 1.14)),
        transforms.CenterCrop(img_size),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])


def build_model(model_name: str, num_classes: int = 2):
    model_name = model_name.lower()
    if model_name == "resnet18":
        model = resnet18(weights=None)
        in_features = model.fc.in_features
        model.fc = nn.Linear(in_features, num_classes)
        img_size = 224
    else:
        raise ValueError(f"Unsupported model: {model_name}")
    return model, img_size


def predict_photo_probability(image_bytes: bytes) -> float:
    """
    Self-contained single-image predictor. Builds model and transform, loads label_map and weights,
    performs inference, and returns P(photo) as a float.

    Assumptions:
    - Uses defaults: weights at ./output/best_model.pt, label_map at ./output/label_map.json,
      and model architecture 'resnet18' (same defaults as training).
    - Paths are resolved relative to this script if not absolute.
    """
    # Resolve resources relative to this script
    script_dir = Path(__file__).resolve().parent
    weights_path = (script_dir / "./best_model.pt").resolve()
    model_name = "resnet18"

    # Device selection (no external flags; fully self-contained)
    device = torch.device("cpu")

    # Load label map and identify photo index
    label_map = {0: "document", 1: "photo"}
    photo_idx = None
    for k, v in label_map.items():
        if str(v).lower() == "photo":
            photo_idx = k
            break
    if photo_idx is None:
        photo_idx = 1  # sensible fallback

    # Build model and load weights
    model, img_size = build_model(model_name, num_classes=len(label_map))
    state = torch.load(weights_path, map_location="cpu")
    model.load_state_dict(state, strict=True)
    model.to(device)
    model.eval()

    # Build transform
    transform = build_eval_transform(img_size)

    # Load image from bytes
    with Image.open(BytesIO(image_bytes)) as im:
        im = im.convert("RGB")
    tensor = transform(im).unsqueeze(0).to(device)

    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1).detach().cpu().numpy()[0]
        prob_photo = float(probs[int(photo_idx)])
    return prob_photo