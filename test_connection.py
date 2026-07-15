import ee

# Force the Earth Engine dedicated login flow, not gcloud's shared client
ee.Authenticate(auth_mode='localhost', force=True)

ee.Initialize(project='forest-502505')

image = ee.Image('USGS/SRTMGL1_003')
print("Connection successful!")
print(image.getInfo()['bands'][0]['id'])