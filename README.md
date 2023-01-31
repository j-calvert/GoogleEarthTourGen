# GoogleEarthTourGen
Python script to generate KML tour or [GeoJSON](https://docs.mapbox.com/help/glossary/geojson/) files from a directory full of (exif GPS-tagged) photos

## Setting up environment

Following https://code.visualstudio.com/docs/python/python-tutorial create virtual environment, then `pip install ExifRead`.

## Running

Run from within VSCode, outputs a file in the hardcoded directory where the images are provided, or

`python3 dirToGeoJSON.py {name}`, where name should be a subdirectory of ~/localPhotos

## Demo
Of clicking around the output https://www.youtube.com/watch?v=KWx3ygBAnyE
