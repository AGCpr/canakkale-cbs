"""23 — Interaktif web atlasi (Leaflet, CDN; harici veri indirilmez).

Cikti: 09_teslim/web_atlas.html (tek dosya). Katmanlar: U_esit raster goruntusu
(kucultulmus PNG), su_hedef+koridor sinirlari (sadelestirilmis GeoJSON),
kontrol + aday noktalar (U/fV popup). Internet: yalnizca Leaflet CDN + OSM altlik.
"""
from pathlib import Path
import json
import numpy as np, pandas as pd
import rasterio
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import geopandas as gpd
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "09_teslim"

with rasterio.open(ROOT / "05_olcut_model" / "U_raster_esit.tif") as d:
    U = d.read(1).astype(float); tr = d.transform
m = np.ma.masked_invalid(U)
fig, ax = plt.subplots(figsize=(10, 8), dpi=100)
ax.imshow(m, cmap="viridis", norm=Normalize(0, 1)); ax.axis("off")
fig.subplots_adjust(0, 0, 1, 1)
fig.savefig(T / "_u.png", pad_inches=0); plt.close(fig)
# sinirlar: koridor PNG ile ayni pencere
south, north = tr.f + m.shape[0] * tr.e, tr.f
west, east = tr.c, tr.c + m.shape[1] * tr.a

to4326 = Transformer.from_crs("EPSG:32635", "EPSG:4326", always_xy=True)
def wgs(g):
    from shapely.ops import transform as _t
    return _t(lambda x, y: to4326.transform(x, y), g)

tab = pd.read_csv(ROOT / "05_olcut_model" / "model_tablosu.csv")
nok = gpd.read_file(ROOT / "05_olcut_model" / "ornek_noktalar.gpkg")
ad = pd.read_csv(ROOT / "05_olcut_model" / "aday_olcut_tablosu.csv")
feat = []
for _, r in nok.iterrows():
    v = tab.loc[tab["nok_id"] == r["nok_id"]].iloc[0]
    lon, lat = to4326.transform(r.geometry.x, r.geometry.y)[:2]
    feat.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": {"tur": "kontrol", "id": r["nok_id"],
                       "U": round(float(v["U_esit"]), 3), "fV": round(float(v["fV"]), 4)}})
for _, r in ad.iterrows():
    lon, lat = to4326.transform(r["x_32635"], r["y_32635"])[:2]
    feat.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": {"tur": "aday", "id": r["yapi_id"] + " " + r["ad_standart"],
                       "U": round(float(r["U_esit"]), 3), "fV": round(float(r["fV"]), 4),
                       "sinif": r.get("okuma_sinifi", "")}})
kor = gpd.read_file(ROOT / "03_veri" / "islenmis" / "koridor.gpkg").to_crs("EPSG:4326")
kor["geometry"] = kor.simplify(0.005).geometry
gj = {"noktalar": {"type": "FeatureCollection", "features": feat},
      "koridor": json.loads(kor.to_json())}

html = f"""<!DOCTYPE html><html lang="tr"><head><meta charset="utf-8">
<title>Çanakkale CBS — Web Atlası (pilot)</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>body{{margin:0}}#m{{height:100vh}}.bilgi{{background:#fff;padding:8px;max-width:320px}}</style></head>
<body><div id="m"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
var map = L.map('m').setView([40.25, 26.4], 10);
L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
  {{attribution:'© OpenStreetMap'}}).addTo(map);
L.imageOverlay('_u.png', [[{south}, {west}], [{north}, {east}]], {{opacity:0.55}}).addTo(map);
var kor = {json.dumps(gj["koridor"])};
L.geoJSON(kor, {{style:{{color:'#0aa', weight:2, fillOpacity:0.05}}}}).addTo(map);
var pts = {json.dumps(gj["noktalar"])};
L.geoJSON(pts, {{pointToLayer: function(f, ll){{
  var a = f.properties.tur === 'aday';
  return L.circleMarker(ll, {{radius: a?7:4, color: a?'red':'#2288ff',
    fillColor: a?'red':'#2288ff', fillOpacity:0.8}});}},
  onEachFeature: function(f, l){{
    var p = f.properties;
    l.bindPopup('<b>'+p.id+'</b><br>U='+p.U+' fV='+p.fV+(p.sinif?'<br>'+p.sinif:''));}}}}).addTo(map);
L.control.attribution({{prefix:'Pilot atlas — yöntem gösterimi, kanıt değil'}}).addTo(map);
</script></body></html>"""
(T / "web_atlas.html").write_text(html, encoding="utf-8")
print("-> web_atlas.html (CDN gerektirir; _u.png ile birlikte acilir)")
