"""25 — Web veri paketi: JSON + dusuk cozunurluk overlay PNG (web/klasoru).

Cikti: web/data/*.json + web/img/*.png (viridis, seffaf zemin).
"""
from pathlib import Path
import json
import numpy as np, pandas as pd
import rasterio
from rasterio.enums import Resampling
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, LinearSegmentedColormap, LightSource
import geopandas as gpd
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"; (WEB / "data").mkdir(parents=True, exist_ok=True); (WEB / "img").mkdir(exist_ok=True)

# Bogaz pastel paleti (v3, illoca kagidi uzerinde): acik mavi -> kobalt
# Degerler esik-altinda seffaf birakilir (harita nefes alir).
import matplotlib.cm as _cm
PASTEL_U = plt.get_cmap("Blues").copy()
PASTEL_U.set_bad(alpha=0.0)
PASTEL_KUM = plt.get_cmap("Blues").copy()
PASTEL_KUM.set_bad(alpha=0.0)
PASTEL_E = plt.get_cmap("Oranges").copy()
PASTEL_E.set_bad(alpha=0.0)

with rasterio.open(ROOT / "05_olcut_model" / "koridor_dem.tif") as d:
    tr = d.transform; crs = d.crs; H, W = d.height, d.width
to4326 = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)

def overlay(src, ad, vmin=0.0, vmax=1.0, cmap="bogaz", esik=None):
    with rasterio.open(ROOT / src) as d:
        hh, ww = 720, int(720 * d.width / d.height)
        a = d.read(1, out_shape=(hh, ww), resampling=Resampling.bilinear).astype(float)
    m = np.ma.masked_invalid(a)
    if esik is not None:
        m = np.ma.masked_where(m < esik, m)
    cmap_o = {"bogaz": PASTEL_U, "kum": PASTEL_KUM, "erisim": PASTEL_E}.get(cmap, cmap)
    fig, ax = plt.subplots(figsize=(ww / 100, hh / 100), dpi=100)
    ax.imshow(m, cmap=cmap_o,
              norm=Normalize(vmin, vmax), aspect="equal")
    ax.axis("off"); fig.subplots_adjust(0, 0, 1, 1)
    fig.savefig(WEB / "img" / ad, transparent=True, pad_inches=0); plt.close(fig)
    return ww, hh

overlay("05_olcut_model/U_raster_esit.tif", "u_esit.png", 0, 1, "bogaz", 0.03)
overlay("05_olcut_model/U_raster_uzman_gorus_agirlikli.tif", "u_uzman.png", 0, 1, "bogaz", 0.03)
overlay("05_olcut_model/U_raster_uzman_denge_arayisi.tif", "u_denge.png", 0, 1, "bogaz", 0.03)
overlay("05_olcut_model/kumulatif_gorus.tif", "kum.png", 0, 8, "kum", 0.5)
overlay("05_olcut_model/erisim_maliyet.tif", "erisim.png",
        float(np.nanmin(rasterio.open(ROOT / "05_olcut_model/erisim_maliyet.tif").read(1))),
        float(np.nanpercentile(rasterio.open(ROOT / "05_olcut_model/erisim_maliyet.tif").read(1), 98)), "erisim", None)

# Hero: koridor hillshade, gece-murekkep tonlamali
with rasterio.open(ROOT / "05_olcut_model" / "koridor_dem.tif") as _d:
    _z = _d.read(1).astype(float)
_ls = LightSource(azdeg=315, altdeg=38)
_hs = _ls.hillshade(np.nan_to_num(_z, nan=np.nanmin(_z)), vert_exag=1.6, dx=30, dy=30)
_hs = (_hs - _hs.min()) / max(_hs.max() - _hs.min(), 1e-9)
_mavi = np.array([11, 18, 32]) / 255.0   # #0b1220
_kemik = np.array([237, 234, 226]) / 255.0
_rgb = _mavi[None, None, :] * (0.35 + 0.65 * (1 - _hs[..., None])) + \
    _kemik[None, None, :] * (_hs[..., None] ** 2.2) * 0.28
fig, ax = plt.subplots(figsize=(16, 9), dpi=110)
ax.imshow(np.clip(_rgb, 0, 1), aspect="equal"); ax.axis("off")
fig.subplots_adjust(0, 0, 1, 1)
fig.savefig(WEB / "img" / "hero.jpg", pad_inches=0); plt.close(fig)

south, north = tr.f + H * tr.e, tr.f
west, east = tr.c, tr.c + W * tr.a
c = [to4326.transform(x, y) for x, y in [(west, south), (east, north)]]
bounds = [[c[0][1], c[0][0]], [c[1][1], c[1][0]]]

tab = pd.read_csv(ROOT / "05_olcut_model" / "model_tablosu.csv")
nok = gpd.read_file(ROOT / "05_olcut_model" / "ornek_noktalar.gpkg")
ad = pd.read_csv(ROOT / "05_olcut_model" / "aday_olcut_tablosu.csv")
pts = []
for _, r in nok.iterrows():
    v = tab.loc[tab["nok_id"] == r["nok_id"]].iloc[0]
    lon, lat = to4326.transform(r.geometry.x, r.geometry.y)
    pts.append({"id": r["nok_id"], "tur": "kontrol", "ad": "Kontrol noktası",
        "lon": round(lon, 5), "lat": round(lat, 5),
        "fV": round(float(v["fV"]), 4), "fR": round(float(v["fR"]), 4),
        "fS": round(float(v["fS"]), 4), "U": round(float(v["U_esit"]), 3),
        "M2": round(float(v.get("M2", 0)), 3)})
for _, r in ad.iterrows():
    lon, lat = to4326.transform(r["x_32635"], r["y_32635"])
    pts.append({"id": r["yapi_id"], "tur": "aday", "ad": r["ad_standart"],
        "lon": round(lon, 5), "lat": round(lat, 5),
        "fV": round(float(r["fV"]), 4), "fR": round(float(r["fR"]), 4),
        "fS": round(float(r["fS"]), 4), "U": round(float(r["U_esit"]), 3),
        "M2": round(float(r.get("M2", 0)), 3),
        "sinif": r.get("okuma_sinifi", ""), "karar": float(r.get("kararlilik", 0))})
kur = pd.read_csv(ROOT / "05_olcut_model" / "kurumsal_olcut.csv")
env = pd.read_csv(ROOT / "02_envanter" / "kurumsal_envanter.csv").set_index("kayit_id")
for _, r in kur.iterrows():
    lon, lat = to4326.transform(r["x_32635"], r["y_32635"])
    e = env.loc[r["kayit_id"]]
    pts.append({"id": r["kayit_id"], "tur": "tarihsel", "ad": r["ad_standart"],
        "lon": round(lon, 5), "lat": round(lat, 5),
        "fV": round(float(r["fV"]), 4), "fR": round(float(r["fR"]), 4),
        "fS": round(float(r["fS"]), 4), "U": round(float(r["U_esit"]), 3),
        "M2": round(float(r.get("M2", 0)), 3),
        "sinif": r.get("okuma_sinifi", ""), "karar": float(r.get("kararlilik", 0)),
        "grup": r["grup"], "guven": "orta (kurumsal ziyaret referansi)"})
kor = gpd.read_file(ROOT / "03_veri" / "islenmis" / "koridor.gpkg").to_crs("EPSG:4326")
kor["geometry"] = kor.simplify(0.004).geometry
k = pd.read_csv(ROOT / "06_karsilastirma" / "karsilastirma_tablosu__PILOT_ADAY.csv")
h1 = k[k["etiket"] == "H1_tabya_M1_esit"].iloc[0]
h1v = k[k["etiket"] == "H1_tabya_fV"].iloc[0]

(WEB / "data" / "noktalar.json").write_text(json.dumps(pts, ensure_ascii=False), encoding="utf-8")
(WEB / "data" / "koridor.json").write_text(kor.to_json(), encoding="utf-8")
# Bogaz orta hatti (isik hizli rota cizgisi icin; white-desert ucus cizgisi dili)
HAT = [[26.05, 39.95], [26.35, 40.25], [26.65, 40.45], [26.95, 40.62]]
(WEB / "data" / "hat.json").write_text(json.dumps(
    {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"ad": "bogaz_hatti"},
         "geometry": {"type": "LineString", "coordinates": HAT}}]},
    ensure_ascii=False), encoding="utf-8")
(WEB / "data" / "meta.json").write_text(json.dumps({
    "bounds": bounds,
    "overlays": {"esit": "img/u_esit.png", "uzman": "img/u_uzman.png",
                 "denge": "img/u_denge.png", "kumulatif": "img/kum.png",
                 "erisim": "img/erisim.png"},
    "h1": {"fark": float(h1["medyan_fark"]), "p": float(h1["p"]),
           "nt": int(h1["n_t"]), "nk": int(h1["n_k"])},
    "h1v": {"fark": float(h1v["medyan_fark"]), "p": float(h1v["p"])},
    "aday_sayisi": int(len(ad)), "kontrol_sayisi": int(len(tab)),
    "uretim": "web veri paketi (pilot; kanit degil)"}, ensure_ascii=False), encoding="utf-8")
print(f"-> web/data ({len(pts)} nokta) + web/img (5 overlay)")
