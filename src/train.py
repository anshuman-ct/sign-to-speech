"""
train.py — Full training pipeline for Sign Language CNN.

Usage:
    python src/train.py               # Full training run
    python src/train.py --dry-run     # Validate data loading only (no training)
    python src/train.py --epochs 10   # Override epoch count

Outputs:
    models/sign_language_cnn.h5      — Best weights (by val_accuracy)
    models/checkpoints/              — Epoch checkpoints
    results/training_history.png     — Accuracy + Loss curves
"""

import os
import sys
import argparse
import json

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")   # Headless rendering — no display required

# Ensure project root is on path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tensorflow.keras.callbacks import (
    EarlyStopping, ModelCheckpoint,
    ReduceLROnPlateau, TensorBoard,
)

from src.config import (
    MODEL_PATH, CHECKPOINTS_DIR, RESULTS_DIR,
    EPOCHS, BATCH_SIZE, LEARNING_RATE,
)
from src.data_loader import load_data, get_generators
from src.model import build_model


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _ensure_dirs():
    os.makedirs(CHECKPOINTS_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)


def _build_callbacks(epochs: int):
    """Return Keras callback list."""
    return [
        EarlyStopping(
            monitor="val_accuracy",
            patience=8,
            restore_best_weights=True,
            verbose=1,
        ),
        ModelCheckpoint(
            filepath=os.path.join(CHECKPOINTS_DIR, "epoch_{epoch:03d}_valacc_{val_accuracy:.4f}.h5"),
            monitor="val_accuracy",
            save_best_only=True,
            verbose=1,
        ),
        ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=4,
            min_lr=1e-6,
            verbose=1,
        ),
    ]


def _plot_history(history, save_path: str):
    """Save accuracy + loss curves as a single PNG."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Sign Language CNN — Training History", fontsize=14, fontweight="bold")

    # Accuracy
    axes[0].plot(history.history["accuracy"],     label="Train Acc", linewidth=2)
    axes[0].plot(history.history["val_accuracy"], label="Val Acc",   linewidth=2, linestyle="--")
    axes[0].set_title("Accuracy")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Accuracy")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    # Loss
    axes[1].plot(history.history["loss"],     label="Train Loss", linewidth=2)
    axes[1].plot(history.history["val_loss"], label="Val Loss",   linewidth=2, linestyle="--")
    axes[1].set_title("Loss")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Loss")
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"[Train] History plot saved → {save_path}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def train(epochs: int = EPOCHS, dry_run: bool = False):
    _ensure_dirs()

    print("=" * 60)
    print("  Sign Language CNN — Training Pipeline")
    print("=" * 60)

    # 1. Load data
    (X_train, y_train), (X_val, y_val), (X_test, y_test) = load_data()

    if dry_run:
        print("\n[Dry-Run] Data loaded successfully. Training skipped.")
        return

    # 2. Build generators
    train_gen, val_gen = get_generators(X_train, y_train, X_val, y_val)

    # 3. Build model
    model = build_model()
    model.summary()

    # 4. Train
    print(f"\n[Train] Starting training for up to {epochs} epochs …")
    steps_per_epoch  = len(X_train) // BATCH_SIZE
    validation_steps = len(X_val)   // BATCH_SIZE

    history = model.fit(
        train_gen,
        steps_per_epoch=steps_per_epoch,
        epochs=epochs,
        validation_data=val_gen,
        validation_steps=validation_steps,
        callbacks=_build_callbacks(epochs),
        verbose=1,
    )

    # 5. Save model
    model.save(MODEL_PATH)
    print(f"\n[Train] Model saved → {MODEL_PATH}")

    # 6. Save training history JSON
    history_path = os.path.join(RESULTS_DIR, "training_history.json")
    with open(history_path, "w") as f:
        # Convert numpy floats to Python floats for JSON
        hist_dict = {k: [float(v) for v in vals]
                     for k, vals in history.history.items()}
        json.dump(hist_dict, f, indent=2)

    # 7. Plot history
    plot_path = os.path.join(RESULTS_DIR, "training_history.png")
    _plot_history(history, plot_path)

    # 8. Quick test-set evaluation
    print("\n[Train] Evaluating on held-out test set …")
    test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
    print(f"[Train] Test Loss     : {test_loss:.4f}")
    print(f"[Train] Test Accuracy : {test_acc * 100:.2f}%")

    print("\n[Train] Done! Run `python src/evaluate.py` for detailed metrics.")
    return history


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train the Sign Language CNN")
    parser.add_argument("--epochs",   type=int,  default=EPOCHS,  help="Max training epochs")
    parser.add_argument("--dry-run",  action="store_true",        help="Validate pipeline, skip training")
    args = parser.parse_args()

    train(epochs=args.epochs, dry_run=args.dry_run)
