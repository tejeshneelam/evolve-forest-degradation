import ee
import geemap
import os
import json

ee.Initialize(project='forest-502505')

aoi = ee.Geometry.Rectangle([76.325, 11.625, 76.375, 11.675])
OUTPUT_DIR = 'data/raw_monthly'
os.makedirs(OUTPUT_DIR, exist_ok=True)

TOTAL_PIXELS = 310806  # from your verify_data.py output, 558x557 grid
MIN_COVERAGE = 0.85    # require 85% of the region to have real, cloud-free data


def build_composite(start, end, cloud_prob_thresh=40):
    s2_sr = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
              .filterBounds(aoi).filterDate(start, end))
    s2_clouds = (ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY')
                 .filterBounds(aoi).filterDate(start, end))

    joined = ee.Join.saveFirst('cloud_mask').apply(
        s2_sr, s2_clouds,
        ee.Filter.equals(leftField='system:index', rightField='system:index')
    )

    def mask_with_probability(img):
        img = ee.Image(img)
        cloud_prob = ee.Image(img.get('cloud_mask')).select('probability')

        scl = img.select('SCL')
        # SCL class codes: 3 = cloud shadow, 8/9 = cloud medium/high probability,
        # 10 = thin cirrus, 11 = snow/ice
        scl_mask = (scl.neq(3)
                    .And(scl.neq(8))
                    .And(scl.neq(9))
                    .And(scl.neq(10))
                    .And(scl.neq(11)))

        prob_mask = cloud_prob.lt(cloud_prob_thresh)

        combined_mask = scl_mask.And(prob_mask)
        return img.updateMask(combined_mask).divide(10000)

    collection = ee.ImageCollection(joined).map(mask_with_probability)
    count = collection.size().getInfo()
    if count == 0:
        return None, 0, 0.0

    composite = collection.median().clip(aoi)
    ndvi = composite.normalizedDifference(['B8', 'B4']).rename('NDVI')
    evi = composite.expression(
        '2.5 * ((NIR - RED) / (NIR + 6*RED - 7.5*BLUE + 1))', {
            'NIR': composite.select('B8'), 'RED': composite.select('B4'), 'BLUE': composite.select('B2'),
        }
    ).rename('EVI')
    final = composite.select(['B2', 'B3', 'B4', 'B8', 'B11', 'B12']).addBands([ndvi, evi])

    # THE KEY FIX: measure actual valid-pixel coverage, not just "did any image exist"
    stats = ndvi.reduceRegion(reducer=ee.Reducer.count(), geometry=aoi, scale=10, maxPixels=1e9).getInfo()
    valid_count = stats.get('NDVI', 0)
    coverage = valid_count / TOTAL_PIXELS

    return final, count, coverage


def get_monthly_composite(year, month, max_window_days=20):
    start = ee.Date.fromYMD(year, month, 1)
    end = start.advance(1, 'month')

    image, count, coverage = build_composite(start, end)

    widened = 0
    while (image is None or coverage < MIN_COVERAGE) and widened < max_window_days:
        widened += 10
        image, count, coverage = build_composite(start.advance(-widened, 'day'), end.advance(widened, 'day'))

    if image is None or coverage < MIN_COVERAGE:
        return None, count, coverage

    # Explicitly mark any remaining tiny gaps as a real nodata sentinel (-9999),
    # instead of letting them silently become 0
    image = image.unmask(-9999)
    return image, count, coverage


YEAR = 2025
months_to_fetch = list(range(1, 13))
quality_log = []
log = []

for month in months_to_fetch:
    image, count, coverage = get_monthly_composite(YEAR, month)
    label = f"{YEAR}-{month:02d}"

    if image is None:
        print(f"{label}: SKIPPED (coverage only {coverage:.0%}, below {MIN_COVERAGE:.0%} threshold)")
        log.append((label, count, f'skipped ({coverage:.0%} coverage)'))
        quality_log.append({"month": label, "source_images": count, "coverage": round(coverage, 3), "status": "skipped"})
        continue

    out_path = os.path.join(OUTPUT_DIR, f"{label}.tif")
    geemap.ee_export_image(image, filename=out_path, scale=10, region=aoi, file_per_band=False)
    print(f"{label}: saved ({count} images, {coverage:.0%} valid coverage)")
    log.append((label, count, f'saved ({coverage:.0%} coverage)'))
    quality_log.append({"month": label, "source_images": count, "coverage": round(coverage, 3), "status": "saved"})

print("\nSummary:")
for label, count, status in log:
    print(f"  {label}: {status}")

with open(os.path.join(OUTPUT_DIR, 'quality_log.json'), 'w') as f:
    json.dump(quality_log, f, indent=2)
print(f"\nQuality log saved to {OUTPUT_DIR}/quality_log.json")