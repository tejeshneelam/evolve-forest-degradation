import rasterio
import numpy as np
import matplotlib.pyplot as plt

def load_and_clean(path):
    with rasterio.open(path) as src:
        data = src.read().astype(float)
    data[data == -9999] = np.nan
    return data

# Compare a dry-season month (100% coverage) against the monsoon-tail month (90% coverage)
files = {
    "2025-05 (dry season, 100% coverage)": "data/raw_monthly/2025-05.tif",
    "2025-09 (monsoon tail, 90% coverage)": "data/raw_monthly/2025-09.tif",
}

fig, axes = plt.subplots(1, len(files), figsize=(14, 6))

for ax, (label, path) in zip(axes, files.items()):
    data = load_and_clean(path)

    # True-color-ish preview using B4 (red), B3 (green), B2 (blue) -> bands 2,1,0
    rgb = np.dstack([data[2], data[1], data[0]])
    rgb = np.clip(rgb * 3.5, 0, 1)  # brighten for visibility

    ax.imshow(rgb)
    ax.set_title(label, fontsize=10)
    ax.axis('off')

plt.tight_layout()
plt.savefig('data/raw_monthly/visual_check.png', dpi=150)
print("Saved to data/raw_monthly/visual_check.png")

for label, path in files.items():
    data = load_and_clean(path)
    ndvi = data[6]
    valid = ndvi[~np.isnan(ndvi)]
    print(f"\n{label}")
    print(f"  min={valid.min():.3f}  max={valid.max():.3f}  std={valid.std():.3f}")