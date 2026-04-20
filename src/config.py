"""
config.py — Global hyperparameters, paths, and class labels
for the Sign Language Recognition project.
"""

import os

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR        = os.path.join(BASE_DIR, "data")
RAW_DIR         = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR   = os.path.join(DATA_DIR, "processed")
MODELS_DIR      = os.path.join(BASE_DIR, "models")
CHECKPOINTS_DIR = os.path.join(MODELS_DIR, "checkpoints")
RESULTS_DIR     = os.path.join(BASE_DIR, "results")
NOTEBOOKS_DIR   = os.path.join(BASE_DIR, "notebooks")

# Sign Language MNIST CSV paths (download from Kaggle)
TRAIN_CSV = os.path.join(RAW_DIR, "sign_mnist_train.csv")
TEST_CSV  = os.path.join(RAW_DIR, "sign_mnist_test.csv")

# Trained model output
MODEL_PATH = os.path.join(MODELS_DIR, "sign_language_cnn.h5")

# ─── Image Settings ───────────────────────────────────────────────────────────
IMG_SIZE    = 64          # Resize all images to IMG_SIZE × IMG_SIZE
CHANNELS    = 1           # 1 = grayscale, 3 = RGB
IMG_SHAPE   = (IMG_SIZE, IMG_SIZE, CHANNELS)

# ─── Class Labels ─────────────────────────────────────────────────────────────
# ASL alphabet A–Z excluding J (9) and Z (25) which require motion
# Sign Language MNIST uses 24 static classes (0–23), mapped to letters below
LABEL_MAP = {
    0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E',
    5: 'F', 6: 'G', 7: 'H', 8: 'I', 9: 'K',   # J skipped (motion)
    10: 'L', 11: 'M', 12: 'N', 13: 'O', 14: 'P',
    15: 'Q', 16: 'R', 17: 'S', 18: 'T', 19: 'U',
    20: 'V', 21: 'W', 22: 'X', 23: 'Y'          # Z skipped (motion)
}
NUM_CLASSES = len(LABEL_MAP)   # 24
CLASS_NAMES = list(LABEL_MAP.values())

# ─── Training Hyperparameters ─────────────────────────────────────────────────
BATCH_SIZE    = 64
EPOCHS        = 50
LEARNING_RATE = 1e-3
VAL_SPLIT     = 0.15       # 15% of training data for validation
RANDOM_SEED   = 42

# ─── Augmentation ─────────────────────────────────────────────────────────────
AUGMENT = True
ROTATION_RANGE      = 10
WIDTH_SHIFT_RANGE   = 0.10
HEIGHT_SHIFT_RANGE  = 0.10
ZOOM_RANGE          = 0.10
HORIZONTAL_FLIP     = False   # Flipping changes gesture meaning

# ─── Inference ────────────────────────────────────────────────────────────────
CONFIDENCE_THRESHOLD = 0.70   # Minimum confidence to display a prediction
WEBCAM_INDEX         = 0      # Default camera index
