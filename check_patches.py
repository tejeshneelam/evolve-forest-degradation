import numpy as np
import json

with open('data/patches/patch_index.json') as f:
    index = json.load(f)

months = index['months']
print(f"Months: {months[0]} to {months[-1]} ({len(months)} total)")
print(f"Total patches: {len(index['patches'])}")

# Load one patch and inspect it
sample = np.load('data/patches/patch_0000.npy')
print(f"\nPatch shape: {sample.shape}  (months, bands, height, width)")

ndvi_band_idx = 6  # bands were B2,B3,B4,B8,B11,B12,NDVI,EVI
ndvi_over_time = sample[:, ndvi_band_idx, :, :]

print(f"NaN fraction in this patch: {np.isnan(ndvi_over_time).mean():.3f}")
print(f"NDVI range: min={np.nanmin(ndvi_over_time):.3f}, max={np.nanmax(ndvi_over_time):.3f}")

# Show mean NDVI per month for this one patch -- should look like a plausible seasonal curve
monthly_means = np.nanmean(ndvi_over_time, axis=(1, 2))
for m, v in zip(months[:6], monthly_means[:6]):
    print(f"  {m}: {v:.3f}")
print("  ...")
for m, v in zip(months[-6:], monthly_means[-6:]):
    print(f"  {m}: {v:.3f}")