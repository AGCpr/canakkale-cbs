"""30 — Kurumsal noktalara ayni-protokol V/R/S/fE + senaryo kararililigi.

Protokol 04/11 ile birebir (gozlemci 4 m, hedef 0 m, 15 km, cc 0.13;
refraksiyon notu: 0.85714 ile fark <%0.5, GORUS_PROTOKOL notunda kayitli).
Kara tanimi dem>0.5; oturtma 500 m (kurumsal hata) icinde.
Cikti: 05_olcut_model/kurumsal_olcut.csv
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
from scipy import ndimage

kur = pd.read_csv(ROOT / "02_envanter" / "kurumsal_envanter.csv")
with rasterio.open(CIK / "koridor_dem.tif") as d:
    dem = d.read(1).astype(float); tr = d.transform; crs = d.crs
    res = abs(tr.a); H, W = dem.shape
with rasterio.open(CIK / "egim_derece.tif") as d:
    egim = d.read(1).astype(float)
with rasterio.open(CIK / "su_hedef_mask.tif") as d:
    suH = d.read(1) == 1
with rasterio.open(CIK / "erisim_maliyet.tif") as d:
    er = d.read(1).astype(float); tr6 = d.transform
kara = np.nan_to_num(dem) > 0.5
toplam_su = int(suH.sum())
T = Transformer.from_crs("EPSG:4326", str(crs), always_xy=True)
es = P["egim"]["esik"]

_rp = int(round(1000 / res))
_yy, _xx = np.ogrid[-_rp:_rp + 1, -_rp:_rp + 1]
_kk = (_xx * _xx + _yy * _yy <= _rp * _rp).astype(float); _kk /= _kk.sum()
_mz = np.isfinite(dem).astype(float)
R_ham = dem - (ndimage.convolve(np.nan_to_num(np.where(np.isfinite(dem), dem, 0.0)), _kk, mode="nearest")
               / np.maximum(ndimage.convolve(_mz, _kk, mode="nearest"), 1e-6))
_Rv = R_ham[np.isfinite(R_ham)]; _plo, _phi = np.percentile(_Rv, [5, 95])

def gdal_fV(X, Y):
    with tempfile.TemporaryDirectory() as td:
        o = os.path.join(td, "v.tif")
        subprocess.run([str(QD), "-ox", str(X), "-oy", str(Y), "-oz", str(G["gozlemci_yuksekligi_m"]),
                        "-tz", str(G["hedef_yuksekligi_m"]), "-md", str(G["mesafe_siniri_m"]),
                        "-cc", str(G["refraksiyon_katsayisi"]), "-iv", "0",
                        str(CIK / "koridor_dem.tif"), o], capture_output=True, timeout=180, check=True)
        with rasterio.open(o) as dd:
            vv = dd.read(1); vt = dd.transform
        wr, wc = np.where(suH)
        Xs = tr.c + (wc + 0.5) * res; Ys = tr.f - (wr + 0.5) * res
        inv = ~vt
        co = (inv.a * Xs + inv.b * Ys + inv.c).astype(int)
        ro = (inv.d * Xs + inv.e * Ys + inv.f).astype(int)
        ok = (ro >= 0) & (ro < vv.shape[0]) & (co >= 0) & (co < vv.shape[1])
        return float((vv[ro[ok], co[ok]] == 255).sum()) / max(toplam_su, 1)

def fE_ornekle(X, Y):
    c = int((X - tr6.c) / abs(tr6.a) - 0.5); r = int((tr6.f - Y) / abs(tr6.e) - 0.5)
    r = min(max(r, 0), er.shape[0] - 1); c = min(max(c, 0), er.shape[1] - 1)
    v = float(er[r, c])
    return round(float(np.clip(1 - v / 3000.0, 0, 1)), 4) if np.isfinite(v) else 0.5

sat = []
for _, a in kur.iterrows():
    X, Y = T.transform(a["lon_wgs84"], a["lat_wgs84"])[:2]
    c = int((X - tr.c) / res - 0.5); r = int((tr.f - Y) / res - 0.5)
    oturtma = 0.0
    if not (0 <= r < H and 0 <= c < W and kara[r, c]):
        rp = int(500 / res)
        r1, r2 = max(r - rp, 0), min(r + rp + 1, H); c1, c2 = max(c - rp, 0), min(c + rp + 1, W)
        sub = kara[r1:r2, c1:c2]
        if sub.any():
            _, idx = ndimage.distance_transform_edt(~sub, return_indices=True)
            cr_ = min(max(r - r1, 0), sub.shape[0] - 1); cc_ = min(max(c - c1, 0), sub.shape[1] - 1)
            nr, nc = r1 + idx[0][cr_, cc_], c1 + idx[1][cr_, cc_]
            oturtma = float(np.hypot(nr - r, nc - c) * res)
            r, c = nr, nc
    X, Y = tr * (c + 0.5, r + 0.5)
    fV = gdal_fV(X, Y)
    Rv, Sv = float(R_ham[r, c]), float(egim[r, c])
    fRv = float(np.clip((Rv - _plo) / max(_phi - _plo, 1e-9), 0, 1))
    fSv = float(np.clip(1 - (Sv - es["duz"]) / (es["dik"] - es["duz"]), 0, 1))
    fEv = fE_ornekle(X, Y)
    sat.append({"kayit_id": a["kayit_id"], "ad_standart": a["ad_standart"], "grup": a["grup"],
        "x_32635": round(X, 1), "y_32635": round(Y, 1), "oturtma_m": round(oturtma, 1),
        "fV": round(fV, 4), "R": round(Rv, 2), "egim": round(Sv, 2),
        "fR": round(fRv, 4), "fS": round(fSv, 4), "fE": fEv})
    print(sat[-1]["kayit_id"], f"fV={fV:.4f} R={Rv:.1f} egim={Sv:.1f} oturtma={oturtma:.0f}")

t = pd.DataFrame(sat)
agir = dict(P["agirliklar"]); agir["drop_R"] = {"wV": 0.5, "wR": 0.0, "wS": 0.5}
for ad_, w in agir.items():
    t[f"U_{ad_}"] = (w["wV"] * t["fV"] + w["wR"] * t["fR"] + w["wS"] * t["fS"]).round(4)
tab = pd.read_csv(CIK / "model_tablosu.csv")
ust = t[[f"U_{a}" for a in agir]].apply(lambda c: c >= tab["U_esit"].quantile(0.8))
t["kararlilik"] = ust.mean(axis=1).round(3)
med = tab["U_esit"].median()
t["okuma_sinifi"] = t.apply(lambda r:
    "yuksek/kararli" if r.U_esit >= med and r.kararlilik >= .6 else
    "yuksek/degisken" if r.U_esit >= med else
    "dusuk/kararli" if r.kararlilik >= .6 else "dusuk/degisken", axis=1)
t.to_csv(CIK / "kurumsal_olcut.csv", index=False)
print(t[["kayit_id", "fV", "U_esit", "kararlilik", "okuma_sinifi"]].to_string(index=False))
