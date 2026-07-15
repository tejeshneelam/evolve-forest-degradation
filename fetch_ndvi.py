import ee

ee.Initialize(project='forest-502505')

# Define our pilot area: a ~30 sq km box in Wayanad Wildlife Sanctuary (Muthanga range)
aoi = ee.Geometry.Rectangle([76.325, 11.625, 76.375, 11.675])

# Function to mask clouds using Sentinel-2's QA60 band
def mask_clouds(image):
    qa = image.select('QA60')
    cloud_bit_mask = 1 << 10
    cirrus_bit_mask = 1 << 11
    mask = qa.bitwiseAnd(cloud_bit_mask).eq(0).And(qa.bitwiseAnd(cirrus_bit_mask).eq(0))
    return image.updateMask(mask).divide(10000)  # scale reflectance values to 0-1

# Pull Sentinel-2 imagery over our AOI for a recent, low-cloud period
collection = (
    ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(aoi)
    .filterDate('2026-01-01', '2026-06-30')
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
    .map(mask_clouds)
)

print("Number of images found:", collection.size().getInfo())

# Take the median composite (reduces noise, fills small cloud gaps)
composite = collection.median().clip(aoi)

# Compute NDVI = (NIR - Red) / (NIR + Red)  -> Sentinel-2 bands B8 (NIR), B4 (Red)
ndvi = composite.normalizedDifference(['B8', 'B4']).rename('NDVI')

# Print average NDVI over the region as a sanity check
mean_ndvi = ndvi.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=aoi,
    scale=10,
    maxPixels=1e9
).getInfo()

print("Mean NDVI over pilot area:", mean_ndvi)

# Get a visual thumbnail URL so we can actually SEE the NDVI map
thumb_url = ndvi.getThumbURL({
    'min': 0, 'max': 1,
    'palette': ['red', 'yellow', 'green'],
    'dimensions': 512,
    'region': aoi
})
print("View your NDVI map here:")
print(thumb_url)