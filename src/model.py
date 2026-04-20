"""
model.py — CNN architecture for Sign Language Recognition.

Architecture:
    Input (64×64×1 grayscale)
    → Conv2D(32)  + BN + MaxPool + Dropout
    → Conv2D(64)  + BN + MaxPool + Dropout
    → Conv2D(128) + BN + MaxPool + Dropout
    → Conv2D(256) + BN + MaxPool + Dropout
    → Flatten → Dense(512) + Dropout
    → Dense(24, Softmax)

Target accuracy: ~98.9%
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tensorflow.keras import Model, Input
from tensorflow.keras.layers import (
    Conv2D, BatchNormalization, MaxPooling2D, Dropout,
    Flatten, Dense, Activation,
)
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.regularizers import l2

from src.config import IMG_SHAPE, NUM_CLASSES, LEARNING_RATE


def build_model(input_shape=IMG_SHAPE, num_classes=NUM_CLASSES, lr=LEARNING_RATE) -> Model:
    """
    Build and compile the Sign Language CNN.

    Args:
        input_shape : Tuple (H, W, C)  — default from config (64, 64, 1)
        num_classes : int              — default from config (24)
        lr          : float            — initial learning rate

    Returns:
        Compiled Keras Model
    """

    def conv_block(x, filters: int, dropout_rate: float = 0.25):
        """Conv2D → BN → ReLU → MaxPool → Dropout"""
        x = Conv2D(filters, (3, 3), padding="same", kernel_regularizer=l2(1e-4))(x)
        x = BatchNormalization()(x)
        x = Activation("relu")(x)
        x = MaxPooling2D((2, 2))(x)
        x = Dropout(dropout_rate)(x)
        return x

    inputs = Input(shape=input_shape, name="input_image")

    x = conv_block(inputs, 32,  dropout_rate=0.25)
    x = conv_block(x,      64,  dropout_rate=0.25)
    x = conv_block(x,      128, dropout_rate=0.25)
    x = conv_block(x,      256, dropout_rate=0.30)

    x = Flatten()(x)
    x = Dense(512, activation="relu", kernel_regularizer=l2(1e-4))(x)
    x = Dropout(0.50)(x)

    outputs = Dense(num_classes, activation="softmax", name="predictions")(x)

    model = Model(inputs, outputs, name="SignLanguageCNN")

    model.compile(
        optimizer=Adam(learning_rate=lr),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    return model


if __name__ == "__main__":
    model = build_model()
    model.summary()
