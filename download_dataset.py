import kagglehub
import shutil
import os
import glob

# Download latest version
print("Downloading Sign Language MNIST dataset...")
path = kagglehub.dataset_download("datamunge/sign-language-mnist")
print("Path to dataset files:", path)

# Copy CSVs to data/raw/
dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "raw")
os.makedirs(dest, exist_ok=True)

csv_files = glob.glob(os.path.join(path, "**", "*.csv"), recursive=True)
print(f"\nFound {len(csv_files)} CSV file(s):")
for f in csv_files:
    fname = os.path.basename(f)
    dst = os.path.join(dest, fname)
    shutil.copy2(f, dst)
    print(f"  Copied: {fname} → data/raw/")

print("\nDone! Dataset is ready.")
