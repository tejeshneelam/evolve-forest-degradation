import rasterio
import numpy as np
import glob

files = sorted(glob.glob('data/raw_monthly/*.tif'))
print(f"Found {len(files)} files\n")

for f in files:
    with rasterio.open(f) as src:
        data = src.read()  # shape: (bands, height, width)
        ndvi_band = data[6].astype(float)
        ndvi_band[ndvi_band == -9999] = np.nan # bands were: B2,B3,B4,B8,B11,B12,NDVI,EVI -> NDVI is index 6
        valid = ndvi_band[~np.isnan(ndvi_band)]
        print(f"{f.split('/')[-1]}: shape={data.shape}, mean NDVI={valid.mean():.3f}, valid pixels={len(valid)}/{ndvi_band.size}")

# Flag suspiciously identical months (likely duplicate source imagery)
print("\nDuplicate check:")
means = {}
for f in files:
    with rasterio.open(f) as src:
        ndvi_band = src.read(7)
        means[f.split('/')[-1]] = round(float(np.nanmean(ndvi_band)), 4)

seen = {}
for fname, mean in means.items():
    if mean in seen:
        print(f"  ⚠️  {fname} has IDENTICAL mean NDVI to {seen[mean]} ({mean}) — likely duplicate data")
    seen[mean] = fname