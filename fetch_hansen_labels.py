import ee
import geemap
import os
import numpy as np
import rasterio

ee.Initialize(project='forest-502505')

aoi = ee.Geometry.Rectangle([76.325, 11.625, 76.375, 11.675])
OUTPUT_DIR = 'data/labels'
os.makedirs(OUTPUT_DIR, exist_ok=True)

gfc = ee.Image('UMD/hansen/global_forest_change_2025_v1_13')  # updated, covers through 2025

treecover2000 = gfc.select('treecover2000')
loss = gfc.select('loss')
lossyear = gfc.select('lossyear')

combined = treecover2000.addBands([loss, lossyear]).clip(aoi)

out_path = os.path.join(OUTPUT_DIR, 'hansen_gfc.tif')
geemap.ee_export_image(combined, filename=out_path, scale=10, region=aoi, file_per_band=False)
print(f"Saved to {out_path}")

with rasterio.open(out_path) as src:
    data = src.read()
print(f"Raw shape: {data.shape}")

# Crop to exactly match your Sentinel grid (558 x 557) -- fixes the 1-column mismatch
TARGET_H, TARGET_W = 558, 557
data = data[:, :TARGET_H, :TARGET_W]
print(f"Cropped shape: {data.shape}")

np.save(os.path.join(OUTPUT_DIR, 'hansen_aligned.npy'), data.astype(np.float32))

treecover, loss_flag, loss_year = data[0], data[1], data[2]
print(f"\nMean tree cover in 2000: {treecover.mean():.1f}%")
print(f"Total loss pixels: {(loss_flag == 1).sum()} / {loss_flag.size} ({(loss_flag == 1).mean()*100:.2f}%)")
print("\nLoss by year (within your data window, 2019-2025):")
for yr in range(19, 26):
    count = (loss_year == yr).sum()
    print(f"  20{yr}: {count} pixels")