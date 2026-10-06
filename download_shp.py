import os
import requests

url = "https://data.cityofchicago.org/api/geospatial/cauq-8yn6?method=export&format=GeoJSON"
output_path = "data/cca_shp/Boundaries - Community Areas (current).geojson"
os.makedirs(os.path.dirname(output_path), exist_ok=True)

print(f"Downloading from {url}...")
headers = {'User-Agent': 'Mozilla/5.0'}
r = requests.get(url, headers=headers)
r.raise_for_status()
with open(output_path, 'wb') as f:
    f.write(r.content)
print(f"Saved to {output_path}")
