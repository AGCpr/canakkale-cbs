"""22 — Deniz-seviyesi duyarliligi: hedef yuksekligi -1 / 0 / +1 m.

Rapor karsiligi: §09 (gorus-konum ailesi) + donem kiyi farki vekili.
8 adaya ayni protokolle yalnizca -tz degisir; fV_{-1,0,+1} karsilastirilir.
Cikti: 07_belirsizlik/deniz_seviyesi.csv. (16 viewshed ~6-8 dk.)
"""
from pathlib import Path
import subprocess, tempfile, os
import numpy as np, pandas as pd, yaml

ROOT = Path(__file__).resolve().parents[1]
BEL = ROOT / "07_belirsizlik"
P = yaml.safe_load(open(ROOT / "params" / "model.yaml", encoding="utf-8"))
G = P["gorus"]
QD = Path(r"C:\Program Files\QGIS 4.2.2\bin\gdal_viewshed.exe")
import rasterio
ad = pd.read_csv(ROOT / "05_olcut_model" / "aday_olcut_tablosu.csv")
with rasterio.open(ROOT / "05_olcut_model" / "koridor_dem.tif") as d:
    tr = d.transform; res = abs(tr.a); H, W = d.height, d.width
with rasterio.open(ROOT / "05_olcut_model" / "su_hedef_mask.tif") as d:
    su = d.read(1) == 1
N = int(su.sum())

def fV_tz(X, Y, tz):
    with tempfile.TemporaryDirectory() as td:
        o = os.path.join(td, "v.tif")
        subprocess.run([str(QD), "-ox", str(X), "-oy", str(Y), "-oz", str(G["gozlemci_yuksekligi_m"]),
                        "-tz", str(tz), "-md", str(G["mesafe_siniri_m"]),
                        "-cc", str(G["refraksiyon_katsayisi"]), "-iv", "0",
                        str(ROOT / "05_olcut_model" / "koridor_dem.tif"), o],
                       capture_output=True, timeout=180, check=True)
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
for _, r in ad.iterrows():
    d = {"yapi_id": r["yapi_id"], "fV_t0": r["fV"]}
    for tz in (-1.0, 1.0):
        d[f"fV_t{tz:+.0f}"] = round(fV_tz(r["x_32635"], r["y_32635"], tz), 4)
    f0 = r["fV"]
    d["degisim_aralik"] = round(max(d["fV_t-1"], d["fV_t+1"], f0) - min(d["fV_t-1"], d["fV_t+1"], f0), 4)
    sat.append(d)
    print(d)
pd.DataFrame(sat).to_csv(BEL / "deniz_seviyesi.csv", index=False)
print("-> deniz_seviyesi.csv (hedef ±1 m; donem-kiyi vekili)")
