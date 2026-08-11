import rasterio
import numpy as np

def load_ndvi(path):
    with rasterio.open(path) as src:
        data = src.read(7).astype(float)
    data[data == -9999] = np.nan
    return data

a = load_ndvi('data/raw_monthly/2019-04.tif')
b = load_ndvi('data/raw_monthly/2021-04.tif')

diff = np.abs(a - b)
valid_mask = ~np.isnan(a) & ~np.isnan(b)

print(f"Max pixel difference: {np.nanmax(diff):.6f}")
print(f"Mean pixel difference: {np.nanmean(diff):.6f}")
print(f"Percent of pixels that are EXACTLY identical: {(diff[valid_mask] == 0).sum() / valid_mask.sum() * 100:.2f}%")
print(f"2019-04 mean (full precision): {np.nanmean(a):.8f}")
print(f"2021-04 mean (full precision): {np.nanmean(b):.8f}")