"""
High-Accuracy Cattle Disease Image Classifier Training Script
Architecture: Transfer Learning with MobileNetV2 (ImageNet Pre-trained)
Targets 3 Classes:
  0: foot-and-mouth
  1: healthy
  2: lumpy
Target Accuracy: >95% using Two-Phase Fine-Tuning and Data Augmentation.
Output: backend/models/cattle_image/cattle_disease_image_model.keras
"""

import json
import os
import sys
from pathlib import Path
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

# Force channels_last and deterministic seed
tf.keras.backend.set_image_data_format("channels_last")
tf.keras.utils.set_random_seed(42)

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "data" / "Cows datasets"
OUTPUT_DIR = BASE_DIR / "backend" / "models" / "cattle_image"
MODEL_SAVE_PATH = OUTPUT_DIR / "cattle_disease_image_model.keras"
CLASSES_SAVE_PATH = OUTPUT_DIR / "cattle_disease_classes.json"

# Hyperparameters
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
INITIAL_EPOCHS = 12
FINE_TUNE_EPOCHS = 12
INITIAL_LR = 1e-3
FINE_TUNE_LR = 1e-5
NUM_CLASSES = 3

def check_dataset():
    if not DATASET_DIR.exists():
        print(f"Error: Dataset directory not found at: {DATASET_DIR}")
        sys.exit(1)
    
    classes = sorted([d.name for d in DATASET_DIR.iterdir() if d.is_dir()])
    expected = ["foot-and-mouth", "healthy", "lumpy"]
    print(f"Found classes: {classes}")
    assert classes == expected, f"Expected classes {expected}, but found {classes}"
    return classes

def build_datasets():
    print("\nLoading and splitting dataset (80% Train, 20% Validation)...")
    train_ds = tf.keras.utils.image_dataset_from_directory(
        str(DATASET_DIR),
        labels="inferred",
        label_mode="categorical",
        class_names=["foot-and-mouth", "healthy", "lumpy"],
        color_mode="rgb",
        batch_size=BATCH_SIZE,
        image_size=IMG_SIZE,
        shuffle=True,
        seed=42,
        validation_split=0.2,
        subset="training"
    )

    val_ds = tf.keras.utils.image_dataset_from_directory(
        str(DATASET_DIR),
        labels="inferred",
        label_mode="categorical",
        class_names=["foot-and-mouth", "healthy", "lumpy"],
        color_mode="rgb",
        batch_size=BATCH_SIZE,
        image_size=IMG_SIZE,
        shuffle=False,
        seed=42,
        validation_split=0.2,
        subset="validation"
    )

    # Optimization: prefetch to memory/GPU
    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)
    return train_ds, val_ds

def create_model():
    print("\nBuilding model with MobileNetV2 backbone + Data Augmentation...")
    
    # 1. Base model pre-trained on ImageNet
    base_model = tf.keras.applications.MobileNetV2(
        include_top=False,
        weights="imagenet",
        input_shape=(224, 224, 3)
    )
    base_model.trainable = False  # Freeze base during phase 1

    # 2. Input layer with pixels in [0, 255]
    inputs = keras.Input(shape=(224, 224, 3), name="input_layer")

    # 3. Data Augmentation
    data_augmentation = keras.Sequential([
        layers.RandomFlip("horizontal_and_vertical"),
        layers.RandomRotation(0.2),
        layers.RandomZoom(0.2),
        layers.RandomContrast(0.15),
    ], name="data_augmentation")

    x = data_augmentation(inputs)
    # Preprocessing layer: maps [0, 255] -> [-1, 1] for MobileNetV2
    x = layers.Rescaling(1./127.5, offset=-1)(x)
    x = base_model(x, training=False)

    # 4. Classification head
    x = layers.GlobalAveragePooling2D(name="avg_pool")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.3, name="top_dropout")(x)
    x = layers.Dense(128, activation="relu", name="dense_features")(x)
    x = layers.Dropout(0.2)(x)
    outputs = layers.Dense(NUM_CLASSES, activation="softmax", name="predictions")(x)

    model = keras.Model(inputs=inputs, outputs=outputs, name="CattleDiseaseMobileNetV2")
    return model, base_model

def train():
    check_dataset()
    train_ds, val_ds = build_datasets()
    model, base_model = create_model()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Callbacks
    callbacks = [
        keras.callbacks.ModelCheckpoint(
            filepath=str(MODEL_SAVE_PATH),
            monitor="val_accuracy",
            mode="max",
            save_best_only=True,
            verbose=1
        ),
        keras.callbacks.EarlyStopping(
            monitor="val_accuracy",
            patience=5,
            restore_best_weights=True,
            verbose=1
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=2,
            min_lr=1e-7,
            verbose=1
        )
    ]

    # --- Phase 1: Train Top Classification Head ---
    print("\n--- Phase 1: Training Classification Head (Base Frozen) ---")
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=INITIAL_LR),
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )
    model.summary()

    history_phase1 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=INITIAL_EPOCHS,
        callbacks=callbacks
    )

    # --- Phase 2: Fine-Tuning Top Layers ---
    print("\n--- Phase 2: Fine-Tuning Base Model Top Layers ---")
    base_model.trainable = True
    # Freeze bottom layers, fine-tune top 30 layers
    for layer in base_model.layers[:-30]:
        layer.trainable = False

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=FINE_TUNE_LR),
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )

    history_phase2 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=INITIAL_EPOCHS + FINE_TUNE_EPOCHS,
        initial_epoch=len(history_phase1.epoch),
        callbacks=callbacks
    )

    # Write classes metadata json
    metadata = {
        "classes": ["foot-and-mouth", "healthy", "lumpy"],
        "class_to_index": {"foot-and-mouth": 0, "healthy": 1, "lumpy": 2},
        "image_size": [224, 224],
        "model": "MobileNetV2",
        "task": "cattle_image_classification"
    }
    with open(CLASSES_SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
    print(f"📋 Classes metadata saved to: {CLASSES_SAVE_PATH}")

    # Final evaluation
    print("\nEvaluating best saved model...")
    best_model = keras.models.load_model(str(MODEL_SAVE_PATH))
    loss, acc = best_model.evaluate(val_ds)
    print(f"\n==========================================")
    print(f"🎉 Final Validation Accuracy: {acc * 100:.2f}%")
    print(f"📁 Model saved to: {MODEL_SAVE_PATH}")
    print(f"==========================================")

if __name__ == "__main__":
    train()
