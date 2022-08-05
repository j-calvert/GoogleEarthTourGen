import os

# https://pypi.org/project/ExifRead/
# Read Exif position and timestamp info
import exifread

# Parse timestamp info
import datetime
from dataclasses import dataclass

# Ref: (usage) http://pymotw.com/2/xml/etree/ElementTree/create.html
# Generate XML (KML in particular)
from xml.etree import ElementTree
from xml.dom import minidom


# folder path
dir_path = r"/Users/jcalvert/Downloads/Kauai_June_2022"

# User-friendly exif data that we extract
@dataclass
class ImageData:
    name: str
    dt: datetime
    lat: float
    long: float


# Thanks https://medium.com/spatial-data-science/how-to-extract-gps-coordinates-from-images-in-python-e66e542af354
def decimal_coords(coords, ref):
    decimal_degrees = coords[0] + coords[1] / 60 + coords[2] / 3600
    if ref == "S" or ref == "W":
        decimal_degrees = -decimal_degrees
    return float(decimal_degrees)


# This feels pretty brittle and possibly specific to images originating from my particular phone (Pixel 5A)
def getImageData(path: str) -> ImageData:
    f = open(path, "rb")
    tags = exifread.process_file(f)
    lat = decimal_coords(
        tags["GPS GPSLatitude"].values, tags["GPS GPSLatitudeRef"].values
    )
    long = decimal_coords(
        tags["GPS GPSLongitude"].values, tags["GPS GPSLongitudeRef"].values
    )
    date = [int(x) for x in tags["GPS GPSDate"].values.split(":")]
    time = [int(x) for x in tags["GPS GPSTimeStamp"].values]
    dt = datetime.datetime(
        date[0],
        date[1],
        date[2],
        time[0],
        time[1],
        time[2],
        tzinfo=datetime.timezone.utc,
    )
    return ImageData(path, dt, lat, long)


# XML Utils
def prettify(elem) -> str:
    """Return a pretty-printed XML string for the Element."""
    rough_string = ElementTree.tostring(elem, "utf-8")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def textLeaf(parent: ElementTree.Element, leafName: str, leafText: str):
    leaf = ElementTree.SubElement(parent, leafName)
    leaf.text = str(leafText)


def addPhotoOverlayChild(parent: ElementTree.Element, image: ImageData):
    overlay = ElementTree.SubElement(parent, "PhotoOverlay")
    name = image.dt.strftime("%B %d, %H:%M %p")
    textLeaf(overlay, "name", name)
    # description = str(datetime.datetime.timestamp(image.dt))
    # textLeaf(overlay, "description", description)
    textLeaf(overlay, "visibility", 1)
    # Ref: https://developers.google.com/kml/documentation/cameras
    camera = ElementTree.SubElement(overlay, "Camera")
    textLeaf(camera, "latitude", image.lat)
    textLeaf(camera, "longitude", image.long)
    textLeaf(camera, "altitude", 100)
    textLeaf(camera, "heading", -30)  # Compass 30 degrees
    textLeaf(camera, "tilt", 90)  # Photo parallel to earth radius (not perp, a.k.a flat)
    # textLeaf(camera, "roll", 20) # 20 deg off level w/ horizon 
    icon = ElementTree.SubElement(overlay, "Icon")
    textLeaf(icon, "href", f"file://{image.name}")

    # Ref: https://developers.google.com/kml/documentation/photos#field-of-view
    view = ElementTree.SubElement(overlay, "ViewVolume")
    textLeaf(view, "leftFov", -20)
    textLeaf(view, "rightFov", 20)
    textLeaf(view, "bottomFov", -9)
    textLeaf(view, "topFov", 9)
    textLeaf(view, "near", 10)



# Main
kml = ElementTree.Element("kml")
kml.set("xmlns", "http://www.opengis.net/kml/2.2")
kml.set("xmlns:gx", "http://www.google.com/kml/ext/2.2")
kml.set("xmlns:kml", "http://www.opengis.net/kml/2.2")
kml.set("xmlns:atom", "http://www.w3.org/2005/Atom")
folder = ElementTree.SubElement(kml, "Folder")
folder.set("id", "folder_0")
textLeaf(folder, "name", "Kauai, June 2022")
textLeaf(folder, "open", "1")
textLeaf(folder, "visibility", "1")

# Iterate directory
for f in os.listdir(dir_path):
    # check if it's a jpg file
    path = os.path.join(dir_path, f)
    if os.path.isfile(path) and path.endswith(".jpg"):
        imageData = getImageData(path)
        addPhotoOverlayChild(folder, imageData)


print(prettify(kml))
with open(os.path.join(dir_path, "Generated.kml"), 'w') as out:
    out.write(prettify(kml))

