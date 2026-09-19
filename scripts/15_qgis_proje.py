"""15 — QGIS proje dosyasi (canakkale_vrs.qgz) uretimi.

.qgz = .qgs XML + zip. Katman yolları GORELI (proje qgis/ klasorunde).
Dogrulama: zip butunlugu + XML ayristirma + katman sayisi (16_dogrula).
"""
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
QG = ROOT / "qgis"

RASTERS = [
    ("dem_30m_32635", "../03_veri/islenmis/dem_30m_32635.tif"),
    ("egim_derece", "../05_olcut_model/egim_derece.tif"),
    ("r_1000m", "../05_olcut_model/r_1000m.tif"),
    ("fR", "../05_olcut_model/fR.tif"),
    ("fS", "../05_olcut_model/fS.tif"),
    ("U_esit", "../05_olcut_model/U_raster_esit.tif"),
    ("U_uzman", "../05_olcut_model/U_raster_uzman_gorus_agirlikli.tif"),
    ("kumulatif_gorus", "../05_olcut_model/kumulatif_gorus.tif"),
]
VECTORS = [
    ("su_hedef", "../09_teslim/canakkale_cbs.gpkg", "su_hedef"),
    ("koridor", "../09_teslim/canakkale_cbs.gpkg", "koridor"),
    ("ornek_noktalar", "../09_teslim/canakkale_cbs.gpkg", "ornek_noktalar"),
    ("aday_noktalar_taslak", "../09_teslim/canakkale_cbs.gpkg", "aday_noktalar_taslak"),
]

qgis = ET.Element("qgis", {"projectname": "Canakkale VRS",
    "version": "4.2.2-Belem do Para", "minVersion": "3.30.0"})
tree = ET.SubElement(qgis, "layer-tree-group", {"name": "root", "checked": "Qt::Checked"})
canv = ET.SubElement(qgis, "mapcanvas", {"name": "theMapCanvas"})
ET.SubElement(canv, "units").text = "meters"
ET.SubElement(canv, "extent")
proj = ET.SubElement(qgis, "projectCrs")
srs = ET.SubElement(proj, "spatialrefsys", {"nativeFormat": "xml"})
ET.SubElement(srs, "srsid").text = "100034"
ET.SubElement(srs, "srid").text = "32635"
ET.SubElement(srs, "authid").text = "EPSG:32635"
ET.SubElement(srs, "proj4").text = "+proj=utm +zone=35 +datum=WGS84 +units=m +no_defs"
layers = ET.SubElement(qgis, "projectlayers")

def rid(*a):
    import hashlib
    return hashlib.md5("_".join(a).encode()).hexdigest()[:8]

for i, (ad, yol) in enumerate(RASTERS):
    _id = f"{ad}_{rid(ad)}"
    li = ET.SubElement(tree, "layer-tree-layer", {"id": _id, "name": ad, "checked": "Qt::Checked"})
    ml = ET.SubElement(layers, "maplayer", {"type": "raster"})
    ET.SubElement(ml, "id").text = _id
    ET.SubElement(ml, "datasource").text = yol
    ET.SubElement(ml, "provider").text = "gdal"
    ET.SubElement(ml, "layername").text = ad
    ET.SubElement(ml, "srs")
    ET.SubElement(ml.find("srs"), "spatialrefsys")
    ET.SubElement(ml.find("srs/spatialrefsys"), "authid").text = "EPSG:32635"
for ad, yol, kat in VECTORS:
    _id = f"{ad}_{rid(ad, kat)}"
    ET.SubElement(tree, "layer-tree-layer", {"id": _id, "name": ad, "checked": "Qt::Checked"})
    ml = ET.SubElement(layers, "maplayer", {"type": "vector"})
    ET.SubElement(ml, "id").text = _id
    ET.SubElement(ml, "datasource").text = f"{yol}|layername={kat}"
    ET.SubElement(ml, "provider").text = "ogr"
    ET.SubElement(ml, "layername").text = ad

qgs = QG / "canakkale_vrs.qgs"
ET.ElementTree(qgis).write(qgs, encoding="utf-8", xml_declaration=True)
qgz = QG / "canakkale_vrs.qgz"
with zipfile.ZipFile(qgz, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(qgs, qgs.name)
print(f"-> {qgz} ({len(RASTERS)} raster + {len(VECTORS)} vektor)")
