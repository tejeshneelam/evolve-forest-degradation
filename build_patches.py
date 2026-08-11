import rasterio
import numpy as np
import os
import glob
import json

RAW_DIR = 'data/raw_monthly'
OUTPUT_DIR = 'data/patches'
PATCH_SIZE = 64
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_clean(path):
    with rasterio.open(path) as src:
        data = src.read().astype(np.float32)  # shape: (8, H, W)
    data[data == -9999] = np.nan
    return data

# Load all months in chronological order
files = sorted(glob.glob(os.path.join(RAW_DIR, '*.tif')))
months = [os.path.basename(f).replace('.tif', '') for f in files]
print(f"Found {len(files)} months: {months[0]} to {months[-1]}")

# Load first file to get dimensions
sample = load_clean(files[0])
_, H, W = sample.shape
print(f"Grid size: {H} x {W}")

n_patches_h = H // PATCH_SIZE
n_patches_w = W // PATCH_SIZE
print(f"Will create a {n_patches_h} x {n_patches_w} grid of {PATCH_SIZE}x{PATCH_SIZE} patches per month")

# Load every month into memory once (8 bands x H x W x ~72 months -- manageable at this resolution)
print("Loading all months...")
stack = np.stack([load_clean(f) for f in files])  # shape: (T, 8, H, W)
print(f"Full stack shape: {stack.shape}  (months, bands, height, width)")

# Slice into patches, keep per-patch time series
patch_index = []
patch_id = 0

for i in range(n_patches_h):
    for j in range(n_patches_w):
        y0, y1 = i * PATCH_SIZE, (i + 1) * PATCH_SIZE
        x0, x1 = j * PATCH_SIZE, (j + 1) * PATCH_SIZE

        patch_series = stack[:, :, y0:y1, x0:x1]  # shape: (T, 8, 64, 64)

        # Skip patches with too much missing data across their time series
        valid_fraction = np.mean(~np.isnan(patch_series))
        if valid_fraction < 0.7:
            continue

        out_path = os.path.join(OUTPUT_DIR, f"patch_{patch_id:04d}.npy")
        np.save(out_path, patch_series.astype(np.float32))

        patch_index.append({
            "patch_id": patch_id,
            "grid_row": i, "grid_col": j,
            "pixel_bounds": [y0, y1, x0, x1],
            "valid_fraction": round(float(valid_fraction), 3),
            "n_months": patch_series.shape[0],
        })
        patch_id += 1

with open(os.path.join(OUTPUT_DIR, 'patch_index.json'), 'w') as f:
    json.dump({"months": months, "patches": patch_index}, f, indent=2)

print(f"\nCreated {patch_id} valid patches out of {n_patches_h * n_patches_w} possible")
print(f"Each patch shape: (months={stack.shape[0]}, bands=8, {PATCH_SIZE}, {PATCH_SIZE})")
print(f"Saved to {OUTPUT_DIR}/")