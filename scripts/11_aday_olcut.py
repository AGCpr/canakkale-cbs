"""11 — Aday noktalara ayni-protokol V/R/S + konum hata cevresi dagilimi.

Rapor karsiligi: §03 (gorsel cevre [7]), §06-07 (sabit gorus protokolu).
Girdi: 02_envanter/aday_noktalar_taslak.csv (yalnizca bulunanlar).
- WGS84 -> EPSG:32635; nokta denizdeyse 1000 m icindeki en yakin karaya oturtulur
  (oturtma mesafesi kaydedilir; hata butcesi tuketilir, gizlenmez).
- V: ayni gdal_viewshed protokolu (gozlemci 4 m, hedef 0 m, 15 km, 0.13).
- Hata cevresi: 1000 m yariçapli dairede fR/fS/egim medyan+IQR (rapor [7]).
Cikti: 05_olcut_model/aday_olcut_tablosu.csv + aday_noktalar.gpkg.
"""
from pathlib import Path
import numpy as np, yaml, subprocess, tempfile, os
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CIK = ROOT / "05_olcut_model"
P = yaml.safe_load(open(ROOT / "params" / "model.yaml", encoding="utf-8"))
G = P["gorus"]
QD = Path(r"C:\Program Files\QGIS 4.2.2\bin\gdal_viewshed.exe")

import rasterio
from pyproj import Transformer
import geopandas as gpd
from shapely.geometry import Point
from scipy import ndimage

aday = pd.read_csv(ROOT / "02_envanter" / "aday_noktalar_taslak.csv")
aday["lon_wgs84"] = pd.to_numeric(aday["lon_wgs84"], errors="coerce")
aday["lat_wgs84"] = pd.to_numeric(aday["lat_wgs84"], errors="coerce")
aday = aday.dropna(subset=["lon_wgs84", "lat_wgs84"]).copy()

with rasterio.open(CIK / "koridor_dem.tif") as d:
    dem = d.read(1).astype(float); tr = d.transform; crs = d.crs
    res = abs(tr.a); H, W = dem.shape
with rasterio.open(CIK / "egim_derece.tif") as d:
    egim = d.read(1).astype(float)
with rasterio.open(CIK / "r_1000m.tif") as d:
    R = d.read(1).astype(float)
suH = None
import geopandas as _g
# ORTAK payda: 04 ile ayni su hedef maskesi (su_hedef_mask.tif). GPKG yalnizca
# gorunum icindir; payda olarak kullanilmaz (D6: sabit toplam hedef alani).
with rasterio.open(CIK / "su_hedef_mask.tif") as _d:
    suH = _d.read(1) == 1
    assert suH.shape == (H, W), (suH.shape, (H, W))
sg = None
kara = np.nan_to_num(dem) > 0.5  # gercek kara tanimi (04'teki karaF ile ayni); suH yalnizca V paydasidir
toplam_su = int(suH.sum())

to32635 = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
es = P["egim"]["esik"]

def winsor01(a):
    v = a[np.isfinite(a)]; lo, hi = np.percentile(v, [5, 95])
    return np.clip((a - lo) / max(hi - lo, 1e-9), 0, 1)
fR_full = winsor01(np.where(np.isfinite(R), R, np.nan))
fS_full = np.clip(1 - (egim - es["duz"]) / (es["dik"] - es["duz"]), 0, 1)

def gdal_fV(X, Y, obs_h):
    with tempfile.TemporaryDirectory() as td:
        o = os.path.join(td, "v.tif")
        cmd = [str(QD), "-ox", str(X), "-oy", str(Y), "-oz", str(obs_h),
               "-tz", str(G["hedef_yuksekligi_m"]), "-md", str(G["mesafe_siniri_m"]),
               "-cc", str(G["refraksiyon_katsayisi"]), "-iv", "0",
               str(CIK / "koridor_dem.tif"), o]
        subprocess.run(cmd, capture_output=True, timeout=180, check=True)
        with rasterio.open(o) as d:
            vv = d.read(1); vt = d.transform
        wr, wc = np.where(suH)
        Xs = tr.c + (wc + 0.5) * res; Ys = tr.f - (wr + 0.5) * res
        inv = ~vt
        co = (inv.a * Xs + inv.b * Ys + inv.c).astype(int)
        ro = (inv.d * Xs + inv.e * Ys + inv.f).astype(int)
        ok = (ro >= 0) & (ro < vv.shape[0]) & (co >= 0) & (co < vv.shape[1])
        return float((vv[ro[ok], co[ok]] == 255).sum()) / max(toplam_su, 1)

# Kiyi-esik duyarliligi (rapor §09 'degismis arazi maskesi'): ana maske dem>0.5;
# kiyi yapilari esik-disinda kalabilir. R maskesiz yeniden hesaplanir; nokta
# 'kiyi_esik_disi' bayragi tasir. Esik tarihsel puana gore AYARLANMAZ (D2) —
# iki maske de raporlanir.
from scipy import ndimage as _ndi
_rp = int(round(1000 / res))
_yy, _xx = np.ogrid[-_rp:_rp + 1, -_rp:_rp + 1]
_kk = (_xx * _xx + _yy * _yy <= _rp * _rp).astype(float); _kk /= _kk.sum()
_mz = np.isfinite(dem).astype(float)
R_ham = dem - (_ndi.convolve(np.nan_to_num(np.where(np.isfinite(dem), dem, 0.0)), _kk, mode="nearest")
               / np.maximum(_ndi.convolve(_mz, _kk, mode="nearest"), 1e-6))
_Rv = R_ham[np.isfinite(R_ham)]; _plo, _phi = np.percentile(_Rv, [5, 95])

sat = []
for _, a in aday.iterrows():
    X, Y = to32635.transform(a["lon_wgs84"], a["lat_wgs84"])[:2]
    c = int((X - tr.c) / res - 0.5); r = int((tr.f - Y) / res - 0.5)
    oturtma = 0.0
    if not (0 <= r < H and 0 <= c < W and kara[r, c]):
        # en yakin kara (1000 m icinde)
        rp = int(1000 / res)
        r1, r2 = max(r - rp, 0), min(r + rp + 1, H); c1, c2 = max(c - rp, 0), min(c + rp + 1, W)
        sub = kara[r1:r2, c1:c2]
        if sub.any():
            dist, idx = ndimage.distance_transform_edt(~sub, return_indices=True)
            lr, lc = idx[0][r - r1 if 0 <= r - r1 < sub.shape[0] else 0, 0], None
            # hedefe en yakin kara pikseli: merkezden basla
            cr_ = min(max(r - r1, 0), sub.shape[0] - 1); cc_ = min(max(c - c1, 0), sub.shape[1] - 1)
            rr_, cc_ = idx[0][cr_, cc_], idx[1][cr_, cc_]
            nr, nc = r1 + rr_, c1 + cc_
            oturtma = float(np.hypot(nr - r, nc - c) * res)
            r, c = nr, nc
    X, Y = tr * (c + 0.5, r + 0.5)
    fV = gdal_fV(X, Y, G["gozlemci_yuksekligi_m"])
    kiyi_esik_disi = bool(not kara[r, c])
    Rv = float(R_ham[r, c])  # maskesiz; esik karari bayrakla raporlanir
    # hata cevresi dagilimi (1000 m)
    rp = int(1000 / res)
    yy, xx = np.ogrid[-rp:rp + 1, -rp:rp + 1]
    circ = xx * xx + yy * yy <= rp * rp
    r1, r2 = max(r - rp, 0), min(r + rp + 1, H); c1, c2 = max(c - rp, 0), min(c + rp + 1, W)
    kr = circ[r1 - (r - rp):r2 - (r - rp), c1 - (c - rp):c2 - (c - rp)]
    cevR = R[r1:r2, c1:c2][kr]; cevR = cevR[np.isfinite(cevR)]
    cevS = egim[r1:r2, c1:c2][kr]; cevS = cevS[np.isfinite(cevS)]
    Sv = float(egim[r, c])
    fRv = float(np.clip((Rv - _plo) / max(_phi - _plo, 1e-9), 0, 1))
    fSv = float(np.clip(1 - (Sv - es["duz"]) / (es["dik"] - es["duz"]), 0, 1))
    sat.append({"yapi_id": a["yapi_id"], "ad_standart": a["ad_standart"],
        "x_32635": round(X, 1), "y_32635": round(Y, 1), "oturtma_m": round(oturtma, 1),
        "fV": round(fV, 4), "R": round(Rv, 2), "egim": round(Sv, 2),
        "fR": round(fRv, 4), "fS": round(fSv, 4),
        "cevre_R_med": round(float(np.median(cevR)), 2) if len(cevR) else "",
        "cevre_R_iqr": round(float(np.percentile(cevR, 75) - np.percentile(cevR, 25)), 2) if len(cevR) else "",
        "cevre_egim_med": round(float(np.median(cevS)), 2) if len(cevS) else "",
        "konum_guven": "dusuk", "hata_yaricapi_m": 1000,
        "kiyi_esik_disi": str(kiyi_esik_disi),
        "kaynak": a["kaynak"]})

t = pd.DataFrame(sat)
w = P["agirliklar"]["esit"]
t["U_esit"] = (w["wV"] * t["fV"] + w["wR"] * t["fR"] + w["wS"] * t["fS"]).round(4)
t["M0"] = t["fV"]; t["M1_esit"] = t["U_esit"]
t.to_csv(CIK / "aday_olcut_tablosu.csv", index=False)
gpd.GeoDataFrame(t, geometry=[Point(x, y) for x, y in zip(t["x_32635"], t["y_32635"])],
    crs=crs).to_file(CIK / "aday_noktalar.gpkg", driver="GPKG")
print(t[["yapi_id", "fV", "R", "egim", "U_esit", "oturtma_m"]].to_string(index=False))
print(f"-> aday_olcut_tablosu.csv ({len(t)} aday)")
