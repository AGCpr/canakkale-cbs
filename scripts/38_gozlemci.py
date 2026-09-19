"""38 — Gozlemci yuksekligi duyarliligi: kurumsal 11 nokta x {2, 10} m.

Protokol 30 ile ayni; yalnizca -oz degisir (4 m referans degerler korunur).
cba olcegiyle uyumlu 2/10 m uclari. 22 viewshed ~10 dk.
Cikti: 05_olcut_model/kurumsal_olcut.csv'ye fV_h2/fV_h10 + aralik sutunlari.
"""
from pathlib import Path
import numpy as np, subprocess, tempfile, os
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CIK = ROOT / "05_olcut_model"
P = __import__("yaml").safe_load(open(ROOT / "params" / "model.yaml", encoding="utf-8"))
G = P["gorus"]
QD = Path(r"C:\Program Files\QGIS 4.2.2\bin\gdal_viewshed.exe")
import rasterio

t = pd.read_csv(CIK / "kurumsal_olcut.csv")
with rasterio.open(CIK / "koridor_dem.tif") as d:
    tr = d.transform; res = abs(tr.a); H, W = d.height, d.width
with rasterio.open(CIK / "su_hedef_mask.tif") as d:
    su = d.read(1) == 1
N = int(su.sum())

def fV_h(X, Y, h):
    with tempfile.TemporaryDirectory() as td:
        o = os.path.join(td, "v.tif")
        subprocess.run([str(QD), "-ox", str(X), "-oy", str(Y), "-oz", str(h),
                        "-tz", str(G["hedef_yuksekligi_m"]), "-md", str(G["mesafe_siniri_m"]),
                        "-cc", str(G["refraksiyon_katsayisi"]), "-iv", "0",
                        str(CIK / "koridor_dem.tif"), o], capture_output=True, timeout=180, check=True)
        with rasterio.open(o) as dd:
            vv = dd.read(1); vt = dd.transform
        wr, wc = np.where(su)
        Xs = tr.c + (wc + 0.5) * res; Ys = tr.f - (wr + 0.5) * res
        inv = ~vt
        co = (inv.a * Xs + inv.b * Ys + inv.c).astype(int)
        ro = (inv.d * Xs + inv.e * Ys + inv.f).astype(int)
        ok = (ro >= 0) & (ro < vv.shape[0]) & (co >= 0) & (co < vv.shape[1])
        return float((vv[ro[ok], co[ok]] == 255).sum()) / max(N, 1)

sat = []
for _, r in t.iterrows():
    v2 = round(fV_h(r["x_32635"], r["y_32635"], 2.0), 4)
    v10 = round(fV_h(r["x_32635"], r["y_32635"], 10.0), 4)
    sat.append((v2, v10))
    print(r["kayit_id"], f"h2={v2:.4f} h4={r['fV']:.4f} h10={v10:.4f}")
t["fV_h2"] = [s[0] for s in sat]
t["fV_h10"] = [s[1] for s in sat]
t["fV_aralik_h"] = (t[["fV_h2", "fV", "fV_h10"]].max(axis=1) - t[["fV_h2", "fV", "fV_h10"]].min(axis=1)).round(4)
t.to_csv(CIK / "kurumsal_olcut.csv", index=False)
print("-> fV_h2/fV_h10 eklendi")
