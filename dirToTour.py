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
dir_path = r"/Users/jcalvert/Downloads/Photos-001"

# User-friendly exif data that we extract
@dataclass
class ImageData:
    name: str
    dt: datetime
    ts: float
    lat: float
    long: float
    alt: float
    dir: float
    imgW: int
    imgL: int


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
    alt = float(tags["GPS GPSAltitude"].values[0])
    dir = float(tags["GPS GPSImgDirection"].values[0])
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
    ts = datetime.datetime.timestamp(dt)
    imgW = int(tags["Image ImageWidth"].values[0])
    imgL = int(tags["Image ImageLength"].values[0])
    return ImageData(path, dt, ts, lat, long, alt, dir, imgW, imgL)


# XML Utils
def prettify(elem) -> str:
    """Return a pretty-printed XML string for the Element."""
    rough_string = ElementTree.tostring(elem, "utf-8")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def textLeaf(parent: ElementTree.Element, leafName: str, leafText: str):
    leaf = ElementTree.SubElement(parent, leafName)
    leaf.text = str(leafText)


# In a method because I'm not sure how to clone properly (for reuse across PhotoOverlay
# and Tour stop)
# def setCameraStuff(camera, )


def addPhotoOverlayChildAndTourStop(
    folder: ElementTree.Element, playlist: ElementTree.Element, image: ImageData
):
    overlay = ElementTree.SubElement(folder, "PhotoOverlay")
    # https://developers.google.com/kml/documentation/touring
    flyto = ElementTree.SubElement(playlist, "gx:FlyTo")
    textLeaf(flyto, "gx:duration", 3)
    wait = ElementTree.SubElement(playlist, "gx:Wait")
    textLeaf(wait, "gx:duration", 3)
    name = image.dt.strftime("%B %d, %H:%M %p")
    textLeaf(overlay, "name", name)
    # description = str(datetime.datetime.timestamp(image.dt))
    # textLeaf(overlay, "description", description)
    textLeaf(overlay, "visibility", 1)
    # Ref: https://developers.google.com/kml/documentation/cameras
    for camera in [
        ElementTree.SubElement(overlay, "Camera"),
        ElementTree.SubElement(flyto, "Camera"),
    ]:
        textLeaf(camera, "latitude", image.lat)
        textLeaf(camera, "longitude", image.long)
        textLeaf(camera, "altitude", image.alt + 10)
        textLeaf(camera, "heading", image.dir + 90)  # Compass, feeling out calibration?
        textLeaf(camera, "altitudeMode", "absolute")
        textLeaf(camera, "tilt", 45)  # Angle w/ earth radius

    # textLeaf(camera, "roll", 20) # 20 deg off level w/ horizon
    icon = ElementTree.SubElement(overlay, "Icon")
    textLeaf(icon, "href", f"file://{image.name}")

    # Ref: https://developers.google.com/kml/documentation/photos#field-of-view
    view = ElementTree.SubElement(overlay, "ViewVolume")
    textLeaf(view, "leftFov", -image.imgW / 100)
    textLeaf(view, "rightFov", image.imgW / 100)
    textLeaf(view, "bottomFov", -image.imgL / 100)
    textLeaf(view, "topFov", image.imgL / 100)
    textLeaf(view, "near", (image.imgW + image.imgL) / 200)

    # Use the same camera for


# Main
# Directory -> imageData[]
imageData = []
for f in os.listdir(dir_path):
    # check if it's a jpg file
    path = os.path.join(dir_path, f)
    if (
        os.path.isfile(path)
        and path.endswith(".jpg")
        and not path.endswith(".PANO.jpg")
    ):
        imageData.append(getImageData(path))

# Create root KML node
kml = ElementTree.Element("kml")
kml.set("xmlns", "http://www.opengis.net/kml/2.2")
kml.set("xmlns:gx", "http://www.google.com/kml/ext/2.2")
kml.set("xmlns:kml", "http://www.opengis.net/kml/2.2")
kml.set("xmlns:atom", "http://www.w3.org/2005/Atom")
# Folder has the PhotoOverlays
folder = ElementTree.SubElement(kml, "Folder")
folder.set("id", "folder_0")
textLeaf(folder, "name", "Kauai, June 2022")
textLeaf(folder, "open", "1")
textLeaf(folder, "visibility", "1")
# Playlist has the tour stops
tour = ElementTree.SubElement(folder, "gx:Tour")
textLeaf(tour, "name", "Tour Photos")
playlist = ElementTree.SubElement(tour, "gx:Playlist")

# Add an ImageOverlay per imageData (sorting by timestamp)
for i in sorted(imageData, key=lambda imageData: imageData.ts):
    addPhotoOverlayChildAndTourStop(folder, playlist, i)


print(prettify(kml))
with open(os.path.join(dir_path, "Generated.kml"), "w") as out:
    out.write(prettify(kml))
