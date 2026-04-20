"""
inference.py — Real-time webcam sign language recognition
using OpenCV + MediaPipe Hands + the trained CNN.

Usage:
python src/inference.py
python src/inference.py --model models/sign_language_cnn.h5 --camera 0
python src/inference.py --video sea_test.mp4

Controls:
Q — Quit
S — Save current frame to results/captured_frames/
C — Clear on-screen text buffer
"""

import os
import sys
import cv2
import argparse
import time
import numpy as np
from datetime import datetime
from collections import deque

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import mediapipe as mp
import tensorflow as tf

from src.config import (
    MODEL_PATH, RESULTS_DIR,
    IMG_SIZE, CHANNELS,
    LABEL_MAP, NUM_CLASSES,
    CONFIDENCE_THRESHOLD,
    WEBCAM_INDEX,
)

# ─── Constants ─────────────────────────────────────────────────────────────────
CAPTURE_DIR = os.path.join(RESULTS_DIR, "captured_frames")
SMOOTHING_WINDOW = 7 # Frame-level prediction smoothing
LETTER_DELAY_SEC = 1.2 # Minimum seconds between accepted letters

# ─── Preprocessing ─────────────────────────────────────────────────────────────

def preprocess_roi(roi: np.ndarray) -> np.ndarray:
    """Resize + normalise a hand-ROI for the CNN."""
    img = cv2.resize(roi, (IMG_SIZE, IMG_SIZE))
    if CHANNELS == 1:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = img[..., np.newaxis]
    img = img.astype("float32") / 255.0
    return img[np.newaxis] # (1, H, W, C)

# ─── Drawing helpers ───────────────────────────────────────────────────────────

def draw_rounded_rect(img, x1, y1, x2, y2, r=15,
                      color=(30, 30, 30), alpha=0.6):
    """Draw a semi-transparent rounded rectangle."""
    overlay = img.copy()
    cv2.rectangle(overlay, (x1 + r, y1), (x2 - r, y2), color, -1)
    cv2.rectangle(overlay, (x1, y1 + r), (x2, y2 - r), color, -1)
    for cx, cy in [(x1+r, y1+r), (x2-r, y1+r), (x1+r, y2-r), (x2-r, y2-r)]:
        cv2.circle(overlay, (cx, cy), r, color, -1)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)


def put_text(frame, text, pos, font_scale=0.8, color=(255, 255, 255),
             thickness=2, font=cv2.FONT_HERSHEY_SIMPLEX):
    cv2.putText(frame, text, pos, font, font_scale, color, thickness, cv2.LINE_AA)

# ─── Main inference loop ───────────────────────────────────────────────────────

def run_inference(model_path: str = MODEL_PATH, camera: int = WEBCAM_INDEX, video: str = None):
    os.makedirs(CAPTURE_DIR, exist_ok=True)

    # Load model
    if not os.path.exists(model_path):
        print(f"[ERROR] Model not found: {model_path}")
        print("Run `python src/train.py` first to train the model.")
        sys.exit(1)

    print(f"[Inference] Loading model: {model_path}")
    model = tf.keras.models.load_model(model_path)

    # MediaPipe Hands
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    mp_styles = mp.solutions.drawing_styles
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.60,
        min_tracking_confidence=0.50,
    )

    # Video source: file or camera
    if video:
        if not os.path.exists(video):
            print(f"[ERROR] Video file not found: {video}")
            sys.exit(1)
        cap = cv2.VideoCapture(video)
        print(f"[Inference] Loading video: {video}")
        flip_frame = False
    else:
        cap = cv2.VideoCapture(camera)
        print("[Inference] Starting webcam …")
        flip_frame = True

    if not cap.isOpened():
        print(f"[ERROR] Cannot open video source: {video if video else f'camera index {camera}'}")
        sys.exit(1)

    if not video:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    # State
    prediction_buffer = deque(maxlen=SMOOTHING_WINDOW)
    text_buffer = ""
    last_letter_time = 0.0
    fps_buffer = deque(maxlen=30)
    prev_time = time.time()

    print("[Inference] Press Q to quit | S to save frame | C to clear text")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if flip_frame:
            frame = cv2.flip(frame, 1) # Mirror view
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        # ── FPS ──
        now = time.time()
        fps_buffer.append(1.0 / max(now - prev_time, 1e-5))
        prev_time = now
        fps = np.mean(fps_buffer)

        # ── Background panel (top) ──
        draw_rounded_rect(frame, 0, 0, w, 110, r=0,
                          color=(20, 20, 20), alpha=0.75)

        letter = None
        confidence = 0.0

        if results.multi_hand_landmarks:
            lm = results.multi_hand_landmarks[0]

            # Landmarks will be drawn later so they don't corrupt the CNN input

            # Bounding box around hand (with padding)
            xs = [p.x * w for p in lm.landmark]
            ys = [p.y * h for p in lm.landmark]

            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)

            # Force square bounding box to prevent stretching during resize
            box_w = x_max - x_min
            box_h = y_max - y_min
            side = max(box_w, box_h)

            cx = x_min + box_w / 2
            cy = y_min + box_h / 2

            pad = 20
            x1 = max(0, int(cx - side / 2) - pad)
            y1 = max(0, int(cy - side / 2) - pad)
            x2 = min(w, int(cx + side / 2) + pad)
            y2 = min(h, int(cy + side / 2) + pad)

            # Crop ROI and predict
            roi = frame[y1:y2, x1:x2]
            if roi.size > 0:
                inp = preprocess_roi(roi)
                pred = model.predict(inp, verbose=0)[0]
                idx = np.argmax(pred)
                confidence = float(pred[idx])
                prediction_buffer.append(idx)

                # Smoothed prediction
                smoothed_idx = int(np.bincount(
                    list(prediction_buffer),
                    minlength=NUM_CLASSES
                ).argmax())
                letter = LABEL_MAP.get(smoothed_idx, "?")

                # Accept letter if confident and enough time has passed
                if (confidence >= CONFIDENCE_THRESHOLD
                    and now - last_letter_time >= LETTER_DELAY_SEC):
                    text_buffer += letter
                    last_letter_time = now

            # Draw bounding box
            box_color = (0, 220, 100) if confidence >= CONFIDENCE_THRESHOLD else (0, 150, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)

            # Draw landmarks on the frame AFTER predicting
            mp_drawing.draw_landmarks(
                frame, lm, mp_hands.HAND_CONNECTIONS,
                mp_styles.get_default_hand_landmarks_style(),
                mp_styles.get_default_hand_connections_style(),
            )

        # ── HUD ──
        if letter:
            put_text(frame, f"Sign : {letter}", (20, 45), font_scale=1.2,
                     color=(80, 230, 180), thickness=3)
            pct = int(confidence * 100)
            bar_w = int((w - 260) * (pct / 100))
            cv2.rectangle(frame, (220, 28), (220 + bar_w, 60), (0, 200, 120), -1)
            put_text(frame, f"{pct}%", (w - 80, 50), font_scale=0.8,
                     color=(255, 255, 255))
        else:
            put_text(frame, "No hand detected", (20, 45), font_scale=1.0,
                     color=(150, 150, 150))

        put_text(frame, f"FPS: {fps:.1f}", (w - 130, 95), font_scale=0.6)

        # ── Text buffer panel (bottom) ──
        draw_rounded_rect(frame, 0, h - 70, w, h, r=0,
                          color=(20, 20, 20), alpha=0.75)
        display_text = text_buffer[-50:] if len(text_buffer) > 50 else text_buffer
        put_text(frame, f"Text: {display_text}_", (20, h - 30),
                 font_scale=0.9, color=(255, 220, 80))

        cv2.imshow("Sign Language Recognition — Press Q to quit", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("s"):
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(CAPTURE_DIR, f"frame_{ts}.png")
            cv2.imwrite(path, frame)
            print(f"[Inference] Frame saved → {path}")
        elif key == ord("c"):
            text_buffer = ""
            print("[Inference] Text buffer cleared.")

    cap.release()
    hands.close()
    cv2.destroyAllWindows()
    print(f"\n[Inference] Session ended. Final text: '{text_buffer}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real-time Sign Language Inference")
    parser.add_argument("--model", type=str, default=MODEL_PATH, help="Path to .h5 model")
    parser.add_argument("--camera", type=int, default=WEBCAM_INDEX, help="Camera index (ignored if --video is set)")
    parser.add_argument("--video", type=str, default=None, help="Path to video file (overrides --camera)")
    args = parser.parse_args()
    run_inference(model_path=args.model, camera=args.camera, video=args.video)