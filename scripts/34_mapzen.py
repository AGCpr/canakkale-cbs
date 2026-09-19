"""34 — Mapzen Terrarium ikinci yukseklik kaynagi (H3 ikinci dayanak).

Kaynak: elevation-tiles-prod Terrarium z12 (~29 m/px). Mozaik -> 30 m
calisma gridine; Copernicus ile karsilastirma: medyan fark, NMAD,
Spearman (orneklem), fR/fS bilesen sira uyumu (gorus HARIC - sinir notunda).
Terrarium bilesik kaynaktir; tam bagimsiz dogrulama sayilmaz.
Cikti: 03_veri/islenmis/mapzen_dem_30m.tif + mapzen_karsilastirma.json
"""
from pathlib import Path
import math
import numpy as np, requests, yaml

ROOT = Path(__file__).resolve().parents[1]
HAM = ROOT / "03_veri" / "ham" / "terrarium_z12"
HAM.mkdir(parents=True, exist_ok=True)
ISL = ROOT / "03_veri" / "islenmis"
P = yaml.safe_load(open(ROOT / "params" / "model.yaml", encoding="utf-8"))
xmin, ymin, xmax, ymax = P["kapsama_kutusu_wgs84"]
Z = 12
N = 2 ** Z

def xy(lon, lat):
    x = int((lon + 180) / 360 * N)
    s = math.sin(math.radians(lat))
    y = int((0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * N)
    return x, y

x0, y1 = xy(xmin, ymin); x1, y0 = xy(xmax, ymax)
print(f"karo: x {x0}-{x1}, y {y0}-{y1} ({(x1 - x0 + 1) * (y1 - y0 + 1)} adet)")
import rasterio
from rasterio.merge import merge
from rasterio.warp import reproject, Resampling
from rasterio.io import MemoryFile
from rasterio.transform import from_origin
from collections import namedtuple
Karo = namedtuple("Karo", ["x", "y", "fp"])
karolar = []
for x in range(x0, x1 + 1):
    for y in range(y0, y1 + 1):
        f = HAM / f"t_{x}_{y}.png"
        if not (f.exists() and f.stat().st_size > 1000):
            r = requests.get(f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{Z}/{x}/{y}.png",
                             timeout=60)
            r.raise_for_status()
            f.write_bytes(r.content)
        karolar.append(Karo(x, y, str(f)))
# Terrarium: WebMercator, 256px; yukseklik = R*256+G+B/256-32768
BOYUT = 40075016.68 / N
srcs = []
for k in karolar:
    with rasterio.open(k.fp) as s:
        rgb = s.read().astype(float)
    z = rgb[0] * 256 + rgb[1] + rgb[2] / 256 - 32768
    bati = k.x * BOYUT - 20037508.34
    kuzey = 20037508.34 - k.y * BOYUT
    mem = MemoryFile()
    ds = mem.open(driver="GTiff", height=256, width=256, count=1, dtype="float32",
                  crs="EPSG:3857", transform=from_origin(bati, kuzey, BOYUT / 256, BOYUT / 256))
    ds.write(z.astype(np.float32), 1)
    srcs.append(ds)
mos, trm = merge(srcs)
arr = mos[0]
crs0 = "EPSG:3857"
for s in srcs:
    s.close()

with rasterio.open(ROOT / "03_veri" / "islenmis" / "dem_30m_32635.tif") as d:
    ref = d.read(1).astype(float); tr = d.transform; crs = d.crs
    H, W = ref.shape
out = np.empty((H, W), np.float32)
reproject(arr, out, src_transform=trm, src_crs=crs0,
          dst_transform=tr, dst_crs=crs, dst_width=W, dst_height=H,
          resampling=Resampling.bilinear, dst_nodata=np.nan)
m = dict(driver="GTiff", height=H, width=W, count=1, dtype="float32", crs=crs,
         transform=tr, nodata=np.nan, compress="deflate", tiled=True)
with rasterio.open(ISL / "mapzen_dem_30m.tif", "w", **m) as d:
    d.write(out, 1)

import pandas as pd
kara = np.isfinite(ref) & (ref > 0.5) & np.isfinite(out)
fark = out[kara] - ref[kara]
med = float(np.median(fark))
nmad = float(1.4826 * np.median(np.abs(fark - med)))
rng = np.random.default_rng(20260916)
idx = rng.choice(int(kara.sum()), size=min(200000, int(kara.sum())), replace=False)
from scipy.stats import spearmanr
rho, _ = spearmanr(ref[kara].ravel()[idx], out[kara].ravel()[idx])
# fR/fS bilesen uyumu (nokta duzeyi)
from scipy import ndimage
res = abs(tr.a)
rp = int(round(1000 / res))
yy, xx = np.ogrid[-rp:rp + 1, -rp:rp + 1]
kk = (xx * xx + yy * yy <= rp * rp).astype(float); kk /= kk.sum()
def fRsat(a):
    mz = np.isfinite(a).astype(float)
    R = a - (ndimage.convolve(np.nan_to_num(np.where(np.isfinite(a), a, 0.0)), kk, mode="nearest")
             / np.maximum(ndimage.convolve(mz, kk, mode="nearest"), 1e-6))
    v = R[np.isfinite(R)]; lo, hi = np.percentile(v, [5, 95])
    return np.clip((R - lo) / max(hi - lo, 1e-9), 0, 1)
fRc, fRm = fRsat(ref), fRsat(out)
tab = pd.read_csv(ROOT / "05_olcut_model" / "model_tablosu.csv")
import geopandas as gpd
nok = gpd.read_file(ROOT / "05_olcut_model" / "ornek_noktalar.gpkg").set_index("nok_id")
def hc(X, Y):
    return int((tr.f - Y) / res - 0.5), int((X - tr.c) / res - 0.5)
a_, b_ = [], []
for _, r in tab.iterrows():
    g = nok.loc[r["nok_id"], "geometry"]
    rr, cc = hc(g.x, g.y)
    a_.append(fRc[rr, cc]); b_.append(fRm[rr, cc])
rho_fR, _ = spearmanr(a_, b_)
son = {"medyan_fark_m": round(med, 2), "NMAD_m": round(nmad, 2),
       "Spearman_yukseklik": round(float(rho), 3),
       "Spearman_fR_nokta": round(float(rho_fR), 3),
       "not": "Terrarium bilesik kaynak; dusey datum uzlastirilmadi; bagimsiz dogruluk iddiasi yok."}
import json
json.dump(son, open(ISL / "mapzen_karsilastirma.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(son)
