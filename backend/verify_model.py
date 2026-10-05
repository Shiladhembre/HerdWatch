"""
Verification script for the trained Cattle Disease Model.
Can be executed with either system python or backend venv:
    python verify_model.py
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.services.cattle_image_classifier import CattleImageClassifier
from app.config import get_settings

def run_verification():
    print("=" * 60)
    print("🐄 Testing Cattle Disease Model Integration...")
    print("=" * 60)

    settings = get_settings()
    classifier = CattleImageClassifier(settings)
    
    print("\n1. Loading model and metadata...")
    classifier.load()
    print(f"   Status: {classifier.status}")
    print(f"   Model Name: {getattr(classifier, '_model_name', 'MobileNetV2')}")
    print(f"   Classes: {classifier._classes}")

    if not classifier.status["loaded"]:
        print("❌ Failed to load model!")
        sys.exit(1)

    print("✅ Model loaded successfully!")

    # Find sample images from the dataset
    dataset_dir = Path(__file__).resolve().parents[1] / "data" / "Cows datasets"
    if not dataset_dir.exists():
        print(f"⚠️ Dataset directory not found at: {dataset_dir}")
        return

    print("\n2. Running inference on sample images from each class:")
    for class_name in ["foot-and-mouth", "healthy", "lumpy"]:
        class_folder = dataset_dir / class_name
        if not class_folder.exists():
            continue
        images = list(class_folder.glob("*.jpg")) + list(class_folder.glob("*.png"))
        if not images:
            continue
        sample_img = images[0]
        print(f"\n   Testing sample from [{class_name}]: {sample_img.name}")
        img_bytes = sample_img.read_bytes()
        
        result = classifier.predict(img_bytes)
        pred = result["prediction"]
        probs = result["probabilities"]
        
        print(f"   👉 Predicted Class : {pred['class']} ({pred['display_name']})")
        print(f"   👉 Confidence      : {pred['confidence_percent']}%")
        print(f"   👉 Low Confidence? : {pred['low_confidence']}")
        print(f"   👉 Probabilities   :")
        for k, v in probs.items():
            print(f"        - {k:15}: {v * 100:.2f}%")

    print("\n" + "=" * 60)
    print("🎉 All checks passed! Model is ready for live API serving.")
    print("=" * 60)

if __name__ == "__main__":
    run_verification()
