import pickle
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms
from PIL import Image


BASE_DIR = Path(__file__).resolve().parent
ARTIFACT_DIR = BASE_DIR / "artifacts"

MODEL_PATH = ARTIFACT_DIR / "best_skin_efficientnet_b0_multioutput_final.pth"
LABEL_ENCODER_PATH = ARTIFACT_DIR / "label_encoders.pkl"
MODEL_INFO_PATH = ARTIFACT_DIR / "model_info.pkl"


class EfficientNetB0MultiOutput(nn.Module):
    def __init__(self, num_classes_list):
        super().__init__()

        self.backbone = models.efficientnet_b0(weights=None)

        in_features = self.backbone.classifier[1].in_features
        self.backbone.classifier = nn.Identity()

        self.heads = nn.ModuleList([
            nn.Linear(in_features, num_classes)
            for num_classes in num_classes_list
        ])

    def forward(self, x):
        features = self.backbone(x)
        outputs = [head(features) for head in self.heads]
        return outputs


class SkinImagePredictor:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        with open(LABEL_ENCODER_PATH, "rb") as f:
            self.label_encoders = pickle.load(f)

        with open(MODEL_INFO_PATH, "rb") as f:
            self.model_info = pickle.load(f)

        self.label_cols = self.model_info["label_cols"]

        if "num_classes_list" in self.model_info:
            self.num_classes_list = self.model_info["num_classes_list"]
        else:
            self.num_classes_list = [
                len(self.label_encoders[col].classes_)
                for col in self.label_cols
            ]

        self.model = EfficientNetB0MultiOutput(self.num_classes_list)

        state_dict = torch.load(MODEL_PATH, map_location=self.device)
        self.model.load_state_dict(state_dict)

        self.model.to(self.device)
        self.model.eval()

        image_size = self.model_info.get("image_size", 224)

        self.transform = transforms.Compose([
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=self.model_info.get("mean", [0.485, 0.456, 0.406]),
                std=self.model_info.get("std", [0.229, 0.224, 0.225])
            )
        ])

    def predict(self, image: Image.Image):
        image = image.convert("RGB")
        x = self.transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            outputs = self.model(x)

        predictions = {}
        predicted_codes = []
        confidence_list = []

        for col, logits in zip(self.label_cols, outputs):
            probs = F.softmax(logits, dim=1)[0]

            pred_idx = int(torch.argmax(probs).item())
            confidence = float(probs[pred_idx].item())

            pred_label = self.label_encoders[col].inverse_transform([pred_idx])[0]

            predictions[col] = {
                "predicted_code": str(pred_label),
                "confidence": round(confidence, 4)
            }

            predicted_codes.append(str(pred_label))
            confidence_list.append(confidence)

        initial_skin_condition = "/".join(predicted_codes)

        return {
            "initial_skin_condition": initial_skin_condition,
            "mean_confidence": round(float(np.mean(confidence_list)), 4),
            "predictions": predictions
        }