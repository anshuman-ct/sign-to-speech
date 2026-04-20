"""
evaluate.py — Model evaluation: confusion matrix, classification report,
and per-class accuracy for the Sign Language CNN.

Usage:
    python src/evaluate.py
    python src/evaluate.py --model models/sign_language_cnn.h5

Outputs:
    results/confusion_matrix.png
    results/classification_report.txt
    results/sample_predictions.png
"""

import os
import sys
import argparse
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from sklearn.metrics import (
    confusion_matrix, classification_report, accuracy_score
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import tensorflow as tf
from src.config import (
    MODEL_PATH, RESULTS_DIR, NUM_CLASSES,
    CLASS_NAMES, LABEL_MAP, IMG_SHAPE,
)
from src.data_loader import load_data


# ─── Plotting helpers ─────────────────────────────────────────────────────────

def plot_confusion_matrix(cm: np.ndarray, class_names, save_path: str):
    fig, ax = plt.subplots(figsize=(14, 12))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names,
        linewidths=0.5, ax=ax,
    )
    ax.set_xlabel("Predicted Label", fontsize=12)
    ax.set_ylabel("True Label", fontsize=12)
    ax.set_title("Confusion Matrix — Sign Language CNN", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"[Evaluate] Confusion matrix saved → {save_path}")


def plot_sample_predictions(model, X_test, y_test_labels, save_path: str, n=24):
    """Plot a 4×6 grid of random test images with predicted vs true labels."""
    rng = np.random.default_rng(42)
    idxs = rng.choice(len(X_test), size=n, replace=False)

    X_sample = X_test[idxs]
    y_true   = y_test_labels[idxs]
    y_pred   = np.argmax(model.predict(X_sample, verbose=0), axis=1)

    fig, axes = plt.subplots(4, 6, figsize=(16, 11))
    fig.suptitle("Sample Predictions — Sign Language CNN", fontsize=14, fontweight="bold")

    for i, ax in enumerate(axes.flat):
        img = X_sample[i].squeeze()
        ax.imshow(img, cmap="gray")
        true_letter = LABEL_MAP[y_true[i]]
        pred_letter = LABEL_MAP[y_pred[i]]
        color = "green" if y_pred[i] == y_true[i] else "red"
        ax.set_title(f"T:{true_letter}  P:{pred_letter}", color=color, fontsize=9)
        ax.axis("off")

    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"[Evaluate] Sample predictions saved → {save_path}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def evaluate(model_path: str = MODEL_PATH):
    os.makedirs(RESULTS_DIR, exist_ok=True)

    print("=" * 60)
    print("  Sign Language CNN — Evaluation")
    print("=" * 60)

    # 1. Load data
    _, _, (X_test, y_test_onehot) = load_data()
    y_test_labels = np.argmax(y_test_onehot, axis=1)

    # 2. Load model
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model not found: {model_path}\n"
            "Run `python src/train.py` first to train and save the model."
        )
    print(f"\n[Evaluate] Loading model from: {model_path}")
    model = tf.keras.models.load_model(model_path)

    # 3. Predict
    print("[Evaluate] Running predictions on test set …")
    y_pred_probs  = model.predict(X_test, verbose=1)
    y_pred_labels = np.argmax(y_pred_probs, axis=1)

    # 4. Metrics
    acc = accuracy_score(y_test_labels, y_pred_labels)
    print(f"\n[Evaluate] Test Accuracy : {acc * 100:.2f}%")

    report = classification_report(
        y_test_labels, y_pred_labels,
        target_names=CLASS_NAMES,
        digits=4,
    )
    print("\n[Evaluate] Classification Report:\n")
    print(report)

    report_path = os.path.join(RESULTS_DIR, "classification_report.txt")
    with open(report_path, "w") as f:
        f.write(f"Test Accuracy: {acc * 100:.2f}%\n\n")
        f.write(report)
    print(f"[Evaluate] Report saved → {report_path}")

    # 5. Confusion matrix
    cm = confusion_matrix(y_test_labels, y_pred_labels)
    cm_path = os.path.join(RESULTS_DIR, "confusion_matrix.png")
    plot_confusion_matrix(cm, CLASS_NAMES, cm_path)

    # 6. Sample predictions
    sample_path = os.path.join(RESULTS_DIR, "sample_predictions.png")
    plot_sample_predictions(model, X_test, y_test_labels, sample_path)

    print("\n[Evaluate] Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate the Sign Language CNN")
    parser.add_argument(
        "--model", type=str, default=MODEL_PATH,
        help="Path to the trained .h5 model file"
    )
    args = parser.parse_args()
    evaluate(model_path=args.model)
