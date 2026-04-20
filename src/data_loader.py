"""
data_loader.py — Dataset loading, preprocessing, and augmentation pipeline
for the Sign Language MNIST dataset (CSV format from Kaggle).

Download from:
    https://www.kaggle.com/datasets/datamunge/sign-language-mnist
Place the CSVs at:
    data/raw/sign_mnist_train.csv
    data/raw/sign_mnist_test.csv
"""

import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.utils import to_categorical

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import (
    TRAIN_CSV, TEST_CSV,
    IMG_SIZE, CHANNELS, NUM_CLASSES,
    VAL_SPLIT, RANDOM_SEED,
    BATCH_SIZE,
    AUGMENT,
    ROTATION_RANGE, WIDTH_SHIFT_RANGE,
    HEIGHT_SHIFT_RANGE, ZOOM_RANGE, HORIZONTAL_FLIP,
)


# ─── Raw Loading ──────────────────────────────────────────────────────────────

def _load_csv(csv_path: str):
    """Read CSV and return (X, y) as numpy arrays."""
    df = pd.read_csv(csv_path)
    labels = df["label"].values
    # Kaggle dataset skips J (9) and Z (25). Labels are 0-8 and 10-24. 
    # Map 10-24 down to 9-23 so they are contiguous.
    labels[labels >= 10] -= 1
    
    pixels = df.drop("label", axis=1).values  # shape: (N, 784)
    return pixels, labels


def _preprocess(pixels: np.ndarray, labels: np.ndarray):
    """
    Reshape flat 784-pixel rows to (IMG_SIZE × IMG_SIZE × CHANNELS),
    normalise to [0, 1], and one-hot encode labels.
    """
    # Reshape: (N, 784) → (N, 28, 28) then resize to IMG_SIZE
    N = pixels.shape[0]
    X = pixels.reshape(N, 28, 28).astype("float32")

    # Resize from 28×28 → IMG_SIZE×IMG_SIZE using nearest-neighbour zoom
    if IMG_SIZE != 28:
        import cv2
        X = np.array([
            cv2.resize(img, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_LINEAR)
            for img in X
        ])

    # Add channel dim
    if CHANNELS == 1:
        X = X[..., np.newaxis]          # (N, H, W, 1)
    else:
        X = np.stack([X, X, X], axis=-1)  # Replicate to 3-channel (N, H, W, 3)

    X /= 255.0                           # Normalise
    y = to_categorical(labels, NUM_CLASSES)
    return X, y


# ─── Public API ───────────────────────────────────────────────────────────────

def load_data():
    """
    Load Sign Language MNIST CSVs and return:
        (X_train, y_train), (X_val, y_val), (X_test, y_test)

    Raises FileNotFoundError if CSVs are not present.
    """
    for path in [TRAIN_CSV, TEST_CSV]:
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Dataset not found: {path}\n"
                "Download from https://www.kaggle.com/datasets/datamunge/sign-language-mnist\n"
                f"and place the CSVs in the 'data/raw/' directory."
            )

    # Load raw data
    train_pixels, train_labels = _load_csv(TRAIN_CSV)
    test_pixels,  test_labels  = _load_csv(TEST_CSV)

    # Preprocess
    X_train_full, y_train_full = _preprocess(train_pixels, train_labels)
    X_test,       y_test       = _preprocess(test_pixels,  test_labels)

    # Train / validation split
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_full, y_train_full,
        test_size=VAL_SPLIT,
        random_state=RANDOM_SEED,
        stratify=np.argmax(y_train_full, axis=1),
    )

    print(f"[DataLoader] Train   : {X_train.shape[0]:,} samples")
    print(f"[DataLoader] Val     : {X_val.shape[0]:,} samples")
    print(f"[DataLoader] Test    : {X_test.shape[0]:,} samples")
    print(f"[DataLoader] Image   : {X_train.shape[1:]}  |  Classes: {NUM_CLASSES}")

    return (X_train, y_train), (X_val, y_val), (X_test, y_test)


def get_generators(X_train, y_train, X_val, y_val):
    """
    Create Keras ImageDataGenerator pipelines for training and validation.
    Augmentation is applied only to training data.
    """
    if AUGMENT:
        train_datagen = ImageDataGenerator(
            rotation_range=ROTATION_RANGE,
            width_shift_range=WIDTH_SHIFT_RANGE,
            height_shift_range=HEIGHT_SHIFT_RANGE,
            zoom_range=ZOOM_RANGE,
            horizontal_flip=HORIZONTAL_FLIP,
            fill_mode="nearest",
        )
    else:
        train_datagen = ImageDataGenerator()

    val_datagen = ImageDataGenerator()   # No augmentation for validation

    train_gen = train_datagen.flow(X_train, y_train, batch_size=BATCH_SIZE, seed=RANDOM_SEED)
    val_gen   = val_datagen.flow(X_val,   y_val,   batch_size=BATCH_SIZE, shuffle=False)

    return train_gen, val_gen


# ─── Quick sanity check ───────────────────────────────────────────────────────

if __name__ == "__main__":
    (X_tr, y_tr), (X_v, y_v), (X_te, y_te) = load_data()
    print("Train X:", X_tr.shape, "  y:", y_tr.shape)
    print("Val   X:", X_v.shape,  "  y:", y_v.shape)
    print("Test  X:", X_te.shape, "  y:", y_te.shape)
