import os
import exifread
import datetime
from dataclasses import dataclass


# folder path
dir_path = r'/Users/jcalvert/Downloads/Kauai, June 2022'

# User-friendly exif data that we extract
@dataclass
class ImageData:
    name: str
    timestamp: float
    lat: float
    long: float

# list to store files
res = []

# Thanks https://medium.com/spatial-data-science/how-to-extract-gps-coordinates-from-images-in-python-e66e542af354
def decimal_coords(coords, ref):
    decimal_degrees = coords[0] + coords[1] / 60 + coords[2] / 3600
    if ref == 'S' or ref == 'W':
        decimal_degrees = -decimal_degrees
    return float(decimal_degrees)

def getImageData(path: str)->ImageData:
    f = open(path, 'rb')
    tags = exifread.process_file(f)
    lat = decimal_coords(tags['GPS GPSLatitude'].values, tags['GPS GPSLatitudeRef'].values)
    long = decimal_coords(tags['GPS GPSLongitude'].values, tags['GPS GPSLongitudeRef'].values)
    date = [int(x) for x in tags['GPS GPSDate'].values.split(':')]
    time = [int(x) for x in tags['GPS GPSTimeStamp'].values]
    dt = datetime.datetime(date[0], date[1], date[2], time[0], time[1], time[2], tzinfo=datetime.timezone.utc).microsecond
    return ImageData(path, dt, lat, long)


# Iterate directory
for f in os.listdir(dir_path):
    # check if it's a jpg file
    path = os.path.join(dir_path, f)
    if os.path.isfile(path) and path.endswith('.jpg'):
        imageData = getImageData(path)
        res.append(imageData)
print(res)