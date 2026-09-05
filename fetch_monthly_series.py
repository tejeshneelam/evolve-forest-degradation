import ee
import geemap
import os
import json

ee.Initialize(project='forest-502505')

aoi = ee.Geometry.Rectangle([76.325, 11.625, 76.375, 11.675])
OUTPUT_DIR = 'data/raw_monthly'
os.makedirs(OUTPUT_DIR, exist_ok=True)

TOTAL_PIXELS = 310806
MIN_COVERAGE = 0.85
CLOUD_PROB_THRESH = 40


def build_composite(start, end):
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
        scl_mask = (scl.neq(3).And(scl.neq(8)).And(scl.neq(9))
                    .And(scl.neq(10)).And(scl.neq(11)))
        prob_mask = cloud_prob.lt(CLOUD_PROB_THRESH)
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

    image = image.unmask(-9999)
    return image, count, coverage


# ---- Multi-year loop with resume support ----
YEARS = list(range(2019, 2026))  # 2019 through 2025
months_to_fetch = list(range(1, 13))

log_path = os.path.join(OUTPUT_DIR, 'quality_log.json')
quality_log = json.load(open(log_path)) if os.path.exists(log_path) else []
already_done = {entry['month'] for entry in quality_log}

for year in YEARS:
    for month in months_to_fetch:
        label = f"{year}-{month:02d}"
        out_path = os.path.join(OUTPUT_DIR, f"{label}.tif")

        # Resume support: skip months already processed (saved OR confirmed skipped)
        if label in already_done:
            print(f"{label}: already processed, skipping")
            continue

        image, count, coverage = get_monthly_composite(year, month)

        if image is None:
            print(f"{label}: SKIPPED (coverage only {coverage:.0%})")
            quality_log.append({"month": label, "source_images": count, "coverage": round(coverage, 3), "status": "skipped"})
        else:
            geemap.ee_export_image(image, filename=out_path, scale=10, region=aoi, file_per_band=False)
            print(f"{label}: saved ({count} images, {coverage:.0%} coverage)")
            quality_log.append({"month": label, "source_images": count, "coverage": round(coverage, 3), "status": "saved"})

        # Save progress after every month, so a crash/interrupt loses at most one month
        with open(log_path, 'w') as f:
            json.dump(quality_log, f, indent=2)

saved = sum(1 for e in quality_log if e['status'] == 'saved')
skipped = sum(1 for e in quality_log if e['status'] == 'skipped')
print(f"\nDone. {saved} months saved, {skipped} months skipped, out of {len(quality_log)} total processed.")