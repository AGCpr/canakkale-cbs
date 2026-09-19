"""04 — Olcut uret: egim + goreli yukselti + gorus (nokta-bazli V).

Rapor karsiligi: §06-07, [5,17].
V: fV = gorulen su hucre / toplam su hedef hucre (hedef = 5 km koridor ici su);
birincil gdal_viewshed (QGIS GDAL), yedek numpy LOS. R: R=z-cevre ort; S: Horn.
Islem penceresi: 8 km koridor kirpigi (tam bbox degil — hiz + pilot odagi).
V yalnizca noktalarda raporlanir; kesintisiz hassas yuzeymis gibi uretilmez.
"""
from pathlib import Path
import numpy as np, yaml, subprocess, tempfile, os

ROOT = Path(__file__).resolve().parents[1]
ISL = ROOT / "03_veri" / "islenmis"
CIK = ROOT / "05_olcut_model"; CIK.mkdir(exist_ok=True)
P = yaml.safe_load(open(ROOT / "params" / "model.yaml", encoding="utf-8"))

import rasterio
from rasterio.features import rasterize
from scipy import ndimage
import geopandas as gpd
from shapely.geometry import Point

QD = Path(r"C:\Program Files\QGIS 4.2.2\bin\gdal_viewshed.exe")

with rasterio.open(ISL / "dem_30m_32635.tif") as d:
    demF = d.read(1).astype(np.float32); trF = d.transform; crs = d.crs
    res = abs(trF.a); HF, WF = demF.shape
with rasterio.open(ISL / "su_maske.tif") as d:
    suF = d.read(1) == 1
with rasterio.open(ISL / "kara_maske.tif") as d:
    karaF = d.read(1) == 1

kor = gpd.read_file(ISL / "koridor.gpkg")
koridor_geom = kor.loc[kor["ad"] == "koridor_8km", "geometry"].iloc[0]
hedef_geom = kor.loc[kor["ad"] == "su_hedef_tampon_5km", "geometry"].iloc[0]
kor_mask = rasterize([(koridor_geom, 1)], out_shape=(HF, WF), transform=trF, fill=0, dtype="uint8") == 1
hedef_mask = rasterize([(hedef_geom, 1)], out_shape=(HF, WF), transform=trF, fill=0, dtype="uint8") == 1
suH = suF & hedef_mask  # ortak su hedef alani (sabit payda)

rows = np.where(kor_mask.any(axis=1))[0]; cols = np.where(kor_mask.any(axis=0))[0]
r0, r1, c0, c1 = rows.min(), rows.max() + 1, cols.min(), cols.max() + 1
dem, su, kara = demF[r0:r1, c0:c1], suH[r0:r1, c0:c1], (karaF[r0:r1, c0:c1] & kor_mask[r0:r1, c0:c1])
ny, nx = dem.shape
H, W = ny, nx
from affine import Affine
tr = Affine(res, 0, trF.c + c0 * res, 0, -res, trF.f - r0 * res)

# Koridor DEM dosyasi (gdal_viewshed girdisi — hizli)
kor_dem_yolu = CIK / "koridor_dem.tif"
with rasterio.open(kor_dem_yolu, "w", driver="GTiff", height=H, width=W, count=1,
                   dtype="float32", crs=crs, transform=tr, nodata=-9999,
                   compress="deflate", tiled=True) as d:
    d.write(np.where(np.isfinite(dem), dem, -9999).astype(np.float32), 1)

# --- S: Horn egimi (derece)
z = np.where(np.isfinite(dem), dem, 0).astype(float)
dzdx = (np.roll(z, -1, 1) - np.roll(z, 1, 1)) / (2 * res)
dzdy = (np.roll(z, 1, 0) - np.roll(z, -1, 0)) / (2 * res)
egim = np.degrees(np.arctan(np.hypot(dzdx, dzdy))).astype(np.float32)
egim[~np.isfinite(dem)] = np.nan

def yaz(ad, arr):
    m = dict(driver="GTiff", height=H, width=W, count=1, dtype="float32", crs=crs,
             transform=tr, nodata=np.nan, compress="deflate", tiled=True)
    with rasterio.open(CIK / ad, "w", **m) as d:
        d.write(arr.astype(np.float32), 1)

yaz("egim_derece.tif", egim)

def dairesel_ort(arr, r_m):
    rp = max(int(round(r_m / res)), 1)
    y, x = np.ogrid[-rp:rp + 1, -rp:rp + 1]
    k = (x * x + y * y <= rp * rp).astype(float); k /= k.sum()
    mz = np.isfinite(arr).astype(float)
    return (ndimage.convolve(np.nan_to_num(np.where(np.isfinite(arr), arr, 0.0)), k, mode="nearest")
            / np.maximum(ndimage.convolve(mz, k, mode="nearest"), 1e-6))

R1000 = dem - dairesel_ort(dem, P["goreli_yukselti"]["varsayilan_yaricap_m"])
R1000[~kara] = np.nan
yaz("r_1000m.tif", R1000.astype(np.float32))
R500 = dem - dairesel_ort(dem, 500); R2000 = dem - dairesel_ort(dem, 2000)
np.savez_compressed(CIK / "r_duyarlilik.npz", r500=R500, r1000=R1000, r2000=R2000)

def winsor01(a):
    v = a[np.isfinite(a)]
    lo, hi = np.percentile(v, [5, 95])
    return np.clip((a - lo) / max(hi - lo, 1e-9), 0, 1)
fR = winsor01(R1000).astype(np.float32); fR[~kara] = np.nan
es = P["egim"]["esik"]
fS = np.clip(1 - (egim - es["duz"]) / max(es["dik"] - es["duz"], 1e-9), 0, 1).astype(np.float32)
fS[~kara] = np.nan
yaz("fR.tif", fR); yaz("fS.tif", fS)

# --- Degerlendirme noktalari: koridor ici kiyi seridi (2 km)
er = ndimage.binary_erosion(kara, iterations=int(2000 / res))
serit = kara & ~er
ys, xs = np.where(serit)
rng = np.random.default_rng(P["tekrar_uretilebilirlik"]["rastgelelik_tohumu"])
sec = rng.choice(len(xs), size=min(48, len(xs)), replace=False)
nok = []
for i in sec:
    X, Y = tr * (xs[i] + 0.5, ys[i] + 0.5)
    nok.append({"nok_id": f"K{i:04d}", "tur": "kontrol_adayi", "x": X, "y": Y,
                "col": int(xs[i]), "row": int(ys[i])})
gpd.GeoDataFrame(nok, geometry=[Point(n["x"], n["y"]) for n in nok],
    crs=crs).to_file(CIK / "ornek_noktalar.gpkg", driver="GPKG")

# --- V paydasi: ORTAK su hedef maskesi (tum noktalarda SABIT payda, §06/D6)
# Bu maske su_hedef_mask.tif olarak arsivlenir; 11 ve denetim ayni dosyayi yukler.
G = P["gorus"]; toplam_su = int(su.sum())
mm = dict(driver="GTiff", height=H, width=W, count=1, dtype="uint8", crs=crs,
          transform=tr, nodata=255, compress="deflate", tiled=True)
with rasterio.open(CIK / "su_hedef_mask.tif", "w", **mm) as d:
    d.write(su.astype("uint8"), 1)
su_idx = np.argwhere(su)
seyreltme = 1.0
if len(su_idx) > 4000:
    su_idx = su_idx[rng.choice(len(su_idx), 4000, replace=False)]
    seyreltme = len(su_idx) / max(toplam_su, 1)

def los_gorunur(r0_, c0_, r1_, c1_, obs_h, tgt_h=0.0):
    n = max(abs(r1_ - r0_), abs(c1_ - c0_), 1)
    rr = np.clip(np.linspace(r0_, r1_, n + 1).astype(int), 0, H - 1)
    cc = np.clip(np.linspace(c0_, c1_, n + 1).astype(int), 0, W - 1)
    h = dem[rr, cc]
    if not np.all(np.isfinite(h)): return False
    d = np.arange(n + 1) * res
    los = (dem[r0_, c0_] + obs_h) + ((tgt_h - (dem[r0_, c0_] + obs_h)) * d / max(d[-1], 1e-9))
    return bool(np.all(h[1:-1] <= los[1:-1] + 0.5))

def gdal_vshed(row, col, obs_h):
    if not QD.exists(): return None
    X, Y = tr * (col + 0.5, row + 0.5)
    with tempfile.TemporaryDirectory() as td:
        o = os.path.join(td, "v.tif")
        cmd = [str(QD), "-ox", str(X), "-oy", str(Y), "-oz", str(obs_h),
               "-tz", str(G["hedef_yuksekligi_m"]), "-md", str(G["mesafe_siniri_m"]),
               "-cc", str(G["refraksiyon_katsayisi"]), "-iv", "0",
               str(kor_dem_yolu), o]
        try:
            subprocess.run(cmd, capture_output=True, timeout=180, check=True)
            with rasterio.open(o) as d:
                vv = d.read(1); vt = d.transform
            # su hedef hucrelerini dunya koordinatiyla cikti penceresine izdusur
            wr, wc = np.where(su)
            Xs = tr.c + (wc + 0.5) * res
            Ys = tr.f - (wr + 0.5) * res
            inv = ~vt
            co = (inv.a * Xs + inv.b * Ys + inv.c).astype(int)
            ro = (inv.d * Xs + inv.e * Ys + inv.f).astype(int)
            ok = (ro >= 0) & (ro < vv.shape[0]) & (co >= 0) & (co < vv.shape[1])
            gor = int(((vv[ro[ok], co[ok]] == 255)).sum())
            return gor / max(int(su.sum()), 1)
        except Exception:
            return None

import pandas as pd
sat = []
for n in nok:
    f = gdal_vshed(n["row"], n["col"], G["gozlemci_yuksekligi_m"])
    yontem = "gdal_viewshed"
    if f is None or not np.isfinite(f):
        gor = sum(los_gorunur(n["row"], n["col"], int(r), int(c),
                              G["gozlemci_yuksekligi_m"]) for r, c in su_idx)
        f = gor / max(len(su_idx), 1); yontem = "numpy_LOS_yedek"
    sat.append({"nok_id": n["nok_id"], "fV": round(float(f), 4),
        "R": round(float(R1000[n["row"], n["col"]]), 2),
        "egim": round(float(egim[n["row"], n["col"]]), 2),
        "yontem": yontem})
tab = pd.DataFrame(sat)
tab["fR"] = pd.Series(winsor01(tab["R"].to_numpy(dtype=float))).round(4)
tab["fS"] = (1 - (tab["egim"] - es["duz"]) / (es["dik"] - es["duz"])).clip(0, 1).round(4)
tab.to_csv(CIK / "olcut_tablosu.csv", index=False)
open(CIK / "GORUS_PROTOKOL.txt", "w", encoding="utf-8").write(
 f"gozlemci_m: {G['gozlemci_yuksekligi_m']}; hedef_m: {G['hedef_yuksekligi_m']} (deniz seviyesi)\n"
 f"mesafe_m: {G['mesafe_siniri_m']}; refraksiyon: {G['refraksiyon_katsayisi']}; egriklik: acik\n"
 f"islem_penceresi: 8km koridor kirpigi {W}x{H}; toplam_su_hedef_hucre(koridor): {toplam_su}\n"
 f"hedef_seyreltme_orani: {seyreltme:.3f} (yalnizca numpy yedekte)\n"
 f"birincil: gdal_viewshed ({'bulundu' if QD.exists() else 'yok -> yedek'}); tampon_m: {G['arazi_tampon_m']}\n")
print(tab.describe().to_string())
print(f"-> {CIK/'olcut_tablosu.csv'} ({len(tab)} nokta, koridor {W}x{H})")
