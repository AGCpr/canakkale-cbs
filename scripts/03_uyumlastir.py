"""03 — Uyumlastir: mozaik + EPSG:32635 + 30 m ortak grid + kara/su maskesi.

Rapor karsiligi: §07-02, [11,15]. Cikti: 03_veri/islenmis/.
Kural: 5 m'ye ornekleme YASAK (params/model.yaml). Gercek DEM yoksa SENTETIK
pilot DEM uretilir; dosya adi ayni olsa bile DEM_KAYNAK.txt ve logda acikca
SENTETIK yazilir — K2 onayi sentetikle verilemez.
"""
import glob
from pathlib import Path
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
HAM = ROOT / "03_veri" / "ham"
ISL = ROOT / "03_veri" / "islenmis"
KAL = ROOT / "03_veri" / "kalite"
ISL.mkdir(parents=True, exist_ok=True); KAL.mkdir(parents=True, exist_ok=True)
P = yaml.safe_load(open(ROOT / "params" / "model.yaml", encoding="utf-8"))
assert P["ortak_cozunurluk_m"] == 30 and P["cozum_5m_yasak"], "grid karari ihlal!"

import rasterio
from rasterio.merge import merge
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.mask import mask as rio_mask
from rasterio.features import shapes
from shapely.geometry import box, shape, LineString, mapping
from shapely.ops import transform as shp_transform
from pyproj import Transformer
import geopandas as gpd

xmin, ymin, xmax, ymax = P["kapsama_kutusu_wgs84"]
crs_is = P["calisma_crs"]

tiles = sorted(glob.glob(str(HAM / "Copernicus_DSM_COG_10_*.tif")))
kaynak = "GERCEK (Copernicus)"
dem_src = None
if tiles:
    srcs = [rasterio.open(t) for t in tiles]
    mosaik, tr = merge(srcs, nodata=0)
    meta = srcs[0].meta.copy()
    meta.update(height=mosaik.shape[1], width=mosaik.shape[2], transform=tr)
    tmp = HAM / "_mozaik_4326.tif"
    with rasterio.open(tmp, "w", **meta) as d:
        d.write(mosaik)
    for s in srcs: s.close()
    dem_src = str(tmp)
else:
    kaynak = "SENTETIK (gercek DEM inmemis — yalnizca hat testi)"
    print("UYARI: gercek DEM bulunamadi -> SENTETIK pilot DEM uretiliyor.")

# Hedef grid: bbox'u calisma CRS'ine tasarla, 30 m hizala
to32635 = Transformer.from_crs("EPSG:4326", crs_is, always_xy=True).transform
xmin2, ymin2 = to32635(xmin, ymin)[:2]
xmax2, ymax2 = to32635(xmax, ymax)[:2]
res = P["ortak_cozunurluk_m"]
import math
x0 = math.floor(xmin2 / res) * res; y1 = math.ceil(ymax2 / res) * res
nx = int(math.ceil((xmax2 - x0) / res)); ny = int(math.ceil((y1 - ymin2) / res))
from affine import Affine
dst_tr = Affine(res, 0, x0, 0, -res, y1)

if dem_src:
    with rasterio.open(dem_src) as s:
        arr = np.empty((ny, nx), np.float32)
        reproject(rasterio.band(s, 1), arr, src_transform=s.transform, src_crs=s.crs,
                  dst_transform=dst_tr, dst_crs=crs_is, dst_width=nx, dst_height=ny,
                  resampling=Resampling.bilinear, dst_nodata=np.nan)
else:
    rng = np.random.default_rng(20260916)
    yy, xx = np.mgrid[0:ny, 0:nx].astype(float)
    # Bogaz koridoru: capraz kanal (sentetik topografya)
    cx = (xx / nx - 0.5); cy = (yy / ny - 0.5)
    kanal = np.exp(-((cx * 0.7 + cy * 1.4) ** 2) / 0.004)
    tepeler = 60 * np.exp(-((cx - 0.25) ** 2 + (cy + 0.2) ** 2) / 0.05) \
            + 45 * np.exp(-((cx + 0.3) ** 2 + (cy - 0.25) ** 2) / 0.06) \
            + 8 * rng.standard_normal((ny, nx))
    arr = (tepeler * (1 - kanal) - 12 * kanal).astype(np.float32)

meta = dict(driver="GTiff", height=ny, width=nx, count=1, dtype="float32",
            crs=crs_is, transform=dst_tr, nodata=np.nan, compress="deflate",
            tiled=True)
dem_yolu = ISL / "dem_30m_32635.tif"
with rasterio.open(dem_yolu, "w", **meta) as d:
    d.write(arr, 1)
    d.update_tags(kaynak=kaynak, cozum_m="30", dusey="EGM2008(varsayilan)/sifir-deniz SENTETIK" if "SENTETIK" in kaynak else "EGM2008")

# Kara/su maskesi: deniz seviyesi esigi (DEM yuzey modeli; batimetri degil)
kara = (arr > 0.5)
su = ~kara & np.isfinite(arr)
mask_meta = dict(driver="GTiff", height=ny, width=nx, count=1, dtype="uint8",
                 crs=crs_is, transform=dst_tr, nodata=255, compress="deflate")
for ad, m in [("kara_maske", kara), ("su_maske", su)]:
    with rasterio.open(ISL / f"{ad}.tif", "w", **mask_meta) as d:
        d.write(m.astype("uint8"), 1)

# Bogaz orta hatti (pilot, WGS84) -> 8 km koridor + 5 km su hedef tamponu
hat = LineString([(26.05, 39.95), (26.35, 40.25), (26.65, 40.45), (26.95, 40.62)])
to_back = Transformer.from_crs(crs_is, "EPSG:4326", always_xy=True).transform
from shapely.ops import transform as _t
hat_m = _t(lambda x, y: to32635(x, y)[:2], hat)
koridor = hat_m.buffer(8000); hedef_tampon = hat_m.buffer(5000)
gpd.GeoDataFrame({"ad": ["koridor_8km", "su_hedef_tampon_5km"],
    "geometry": [koridor, hedef_tampon]}, crs=crs_is).to_file(ISL / "koridor.gpkg", driver="GPKG")

su_poly = []
with rasterio.open(ISL / "su_maske.tif") as d:
    sm = d.read(1) == 1
    for geom, val in shapes(sm.astype("uint8"), mask=sm, transform=dst_tr):
        su_poly.append(shape(geom))
import geopandas as _g
if su_poly:
    su_g = _g.GeoDataFrame(geometry=su_poly, crs=crs_is)
    su_g = su_g[su_g.intersects(hedef_tampon)]
    su_g["alan"] = "su_hedef"
    su_g.to_file(ISL / "su_hedef.gpkg", driver="GPKG")
    hedef_hucre = int(sm.sum())
else:
    hedef_hucre = 0

(ISL / "DEM_KAYNAK.txt").write_text(
    f"kaynak: {kaynak}\nkarolar: {len(tiles)}\ncozum_m: 30\ncrs: {crs_is}\n"
    f"hizalama: sola-dayali taban (tap-benzeri)\nnot: 5m ornekleme YASAK; "
    f"dosya {'SENTETIK — analiz altligi degil' if 'SENTETIK' in kaynak else 'gercek veri'}\n",
    encoding="utf-8")

fin = arr[np.isfinite(arr)]
(KAL / "dem_kalite.md").write_text(
 f"# DEM kalite notu\n\n- kaynak: {kaynak}\n- gecerli piksel: {np.isfinite(arr).sum()} / {arr.size}\n"
 f"- bos (nan): {int(np.isnan(arr).sum())}\n- min/med/maks: {np.nanmin(fin):.1f} / {np.nanmedian(fin):.1f} / {np.nanmax(fin):.1f} m\n"
 f"- kara piksel: {int(kara.sum())}, su piksel: {int(su.sum())}, hedef su hucre: {hedef_hucre}\n"
 f"- yatay CRS: {crs_is}; cozum: 30 m; dusey: kataloga islenecek\n", encoding="utf-8")
print(f"-> {dem_yolu} [{kaynak}] grid={nx}x{ny}")
