# Known Failure Modes

## Data and File System

### Missing dataset files
- **Trigger:** Train or test CSV files not present in `data/raw/`
- **System behavior:** `load_data()` raises `FileNotFoundError` with download instructions
- **Recovery:** Download Sign Language MNIST from Kaggle and place CSV files in `data/raw/`
- **Source:** `src/data_loader.py:83-89`
- **Verified:** No ⚠️

### Missing trained model
- **Trigger:** `.h5` model file not present in `models/` directory
- **System behavior:** Both `inference.py` and `evaluate.py` print error and exit with code 1
- **Recovery:** Run `python src/train.py` to train and save the model
- **Source:** `src/inference.py:78-81`, `src/evaluate.py:99-103`
- **Verified:** No ⚠️

### Missing video file for inference
- **Trigger:** Video file path provided to `--video` argument does not exist
- **System behavior:** Prints error and exits with code 1
- **Recovery:** Provide a valid video file path
- **Source:** `src/inference.py:99-101`
- **Verified:** No ⚠️

## Hardware and Environment

### Webcam unavailable or in use
- **Trigger:** Camera index invalid or camera is already open in another application
- **System behavior:** Prints error "Cannot open video source" and exits with code 1
- **Recovery:** Try different camera index (--camera 1), close other camera applications, or restart the computer
- **Source:** `src/inference.py:110-112`
- **Verified:** No ⚠️

### MediaPipe hand detection failure
- **Trigger:** Poor lighting, occluded hand, or no hand in frame
- **System behavior:** No hand landmarks detected; inference loop continues; displays "No hand detected"
- **Recovery:** Ensure hand is visible, well-lit, and centered in frame
- **Source:** `src/inference.py:151` (checks `results.multi_hand_landmarks`)
- **Verified:** No ⚠️

### Low prediction confidence
- **Trigger:** Hand detected but model confidence below `CONFIDENCE_THRESHOLD` (0.70)
- **System behavior:** Prediction is made internally but not displayed; confidence bar shows low value; box color is orange
- **Recovery:** Hold hand steady, ensure clear view of gesture
- **Source:** `src/inference.py:194-197`
- **Verified:** No ⚠️

### Rapid duplicate letters
- **Trigger:** Same gesture performed faster than `LETTER_DELAY_SEC` (1.2 seconds)
- **System behavior:** Letters are rate-limited; prevents same letter from appearing consecutively
- **Recovery:** Pause briefly between letters or wait 1.2 seconds
- **Source:** `src/inference.py:195, 197`
- **Verified:** No ⚠️

## Inference Pipeline

### Empty ROI from edge-of-frame hand
- **Trigger:** Hand partially outside frame causing bounding box to have zero area
- **System behavior:** Skips prediction for that frame to avoid crash
- **Recovery:** Center hand in frame
- **Source:** `src/inference.py:179` (`if roi.size > 0`)
- **Verified:** No ⚠️

### Prediction index out of LABEL_MAP
- **Trigger:** Model predicts a class index not in the LABEL_MAP dictionary
- **System behavior:** Returns '?' character as fallback
- **Recovery:** This indicates unexpected model behavior; retrain model if it occurs frequently
- **Source:** `src/inference.py:191` (`LABEL_MAP.get(smoothed_idx, '?')`)
- **Verified:** No ⚠️

## Training Pipeline

### Training crashes due to memory
- **Trigger:** GPU out of memory or insufficient RAM for batch processing
- **System behavior:** TensorFlow/Keras throws OOM error during model.fit()
- **Recovery:** Reduce BATCH_SIZE in config.py; close other GPU applications
- **Source:** `src/train.py:132-140` (model.fit call)
- **Verified:** No ⚠️

### No improvement in validation accuracy
- **Trigger:** Model stops learning (plateau)
- **System behavior:** EarlyStopping triggers after patience=8 epochs without improvement
- **Recovery:** Check data quality; adjust learning rate; verify class balance; retrain with different architecture
- **Source:** `src/train.py:53-58` (EarlyStopping callback)
- **Verified:** No ⚠️

### Data augmentation producing invalid images
- **Trigger:** Extreme augmentation transforms cause artifacts
- **System behavior:** May produce degraded training quality; no explicit error
- **Recovery:** Reduce augmentation parameters in config.py (ROTATION_RANGE, ZOOM_RANGE, etc.)
- **Source:** `src/data_loader.py:121-128` (ImageDataGenerator config)
- **Verified:** No ⚠️
