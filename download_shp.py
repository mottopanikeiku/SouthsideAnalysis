import os
import requests
import json

url = "https://data.cityofchicago.org/api/geospatial/cauq-8yn6?method=export&format=GeoJSON"
output_path = "data/cca_shp/boundaries.geojson"
os.makedirs(os.path.dirname(output_path), exist_ok=True)

print(f"Downloading from {url}...")
headers = {'User-Agent': 'Mozilla/5.0'}
r = requests.get(url, headers=headers)
if r.status_code == 200:
    print("Download successful.")
    with open(output_path, 'wb') as f:
        f.write(r.content)
    print(f"Saved to {output_path}")
else:
    print(f"Failed to download. Status code: {r.status_code}")
