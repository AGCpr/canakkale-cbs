"""39 — Kontrol siklastirma: koridor-ici Avrupa seridinden +48 nokta.

Amac: bant-eslesmede referans basina n_k>=5'e ulasip K3'u cikarimsal kilmak.
Ayni dar-maske + serit kurali (33b), tohum SEED+9, ID B001-B048.
fR olcegi donduruldu (ilk 48 p5/p95). Tekrar calisirsa B-* satirlari siler.
"""
from pathlib import Path
import numpy as np, yaml, subprocess, tempfile, os
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CIK = ROOT / "05_olcut_model"
P = yaml.safe_load(open(ROOT / "params" / "model.yaml", encoding="utf-8"))
G = P["gorus"]
SEED = P["tekrar_uretilebilirlik"]["rastgelelik_tohumu"]
QD = Path(r"C:\Program Files\QGIS 4.2.2\bin\gdal_viewshed.exe")

import rasterio
from rasterio.features import rasterize
from scipy import ndimage
import geopandas as gpd
from shapely.geometry import Point
from pyproj import Transformer

with rasterio.open(CIK / "koridor_dem.tif") as d:
    dem = d.read(1).astype(float); tr = d.transform; crs = d.crs
    res = abs(tr.a); H, W = dem.shape
with rasterio.open(CIK / "egim_derece.tif") as d:
    egim = d.read(1).astype(float)
with rasterio.open(CIK / "r_1000m.tif") as d:
    R = d.read(1).astype(float)
with rasterio.open(CIK / "su_hedef_mask.tif") as d:
    su = d.read(1) == 1
with rasterio.open(CIK / "erisim_maliyet.tif") as d:
    er = d.read(1).astype(float); tr6 = d.transform
with rasterio.open(ROOT / "03_veri" / "islenmis" / "dem_30m_32635.tif") as d:
    trF = d.transform; HF, WF = d.height, d.width
with rasterio.open(ROOT / "03_veri" / "islenmis" / "kara_maske.tif") as d:
    karaF = d.read(1) == 1
kor = gpd.read_file(ROOT / "03_veri" / "islenmis" / "koridor.gpkg")
kg = kor.loc[kor["ad"] == "koridor_8km", "geometry"].iloc[0]
km = rasterize([(kg, 1)], out_shape=(HF, WF), transform=trF, fill=0, dtype="uint8") == 1
rows = np.where(km.any(axis=1))[0]; cols = np.where(km.any(axis=0))[0]
r0, r1, c0, c1 = rows.min(), rows.max() + 1, cols.min(), cols.max() + 1
kara_dar = karaF[r0:r1, c0:c1] & km[r0:r1, c0:c1]
assert kara_dar.shape == (H, W)
lab, _ = ndimage.label(kara_dar)
TT = Transformer.from_crs("EPSG:4326", "EPSG:32635", always_xy=True).transform
Xk, Yk = TT(26.3792, 40.1477)[:2]
rk, ck = int((tr.f - Yk) / res - 0.5), int((Xk - tr.c) / res - 0.5)
if lab[rk, ck] == 0:  # tohum kiyi hucresine denk geldiyse en yakin kara
    _, ix = ndimage.distance_transform_edt(lab == 0, return_indices=True)
    AVRUPA = lab[ix[0][rk, ck], ix[1][rk, ck]]
else:
    AVRUPA = lab[rk, ck]
er2 = ndimage.binary_erosion(kara_dar, iterations=int(2000 / res))
# mevcut 48 noktanin 300 m cevresi haric (bagimsizligi artir)
g0 = gpd.read_file(CIK / "ornek_noktalar.gpkg")
mevcut = np.zeros((H, W), bool)
for _, r in g0.iterrows():
    rr = int((tr.f - r.geometry.y) / res - 0.5); cc = int((r.geometry.x - tr.c) / res - 0.5)
    rr0, rr1 = max(rr - 10, 0), min(rr + 11, H); cc0, cc1 = max(cc - 10, 0), min(cc + 11, W)
    yy, xx = np.ogrid[rr0 - rr:rr1 - rr, cc0 - cc:cc1 - cc]
    mevcut[rr0:rr1, cc0:cc1] |= (xx * xx + yy * yy) <= 100
serit = kara_dar & ~er2 & (lab == AVRUPA) & ~mevcut
ys, xs = np.where(serit)
print("Avrupa serit (mevcut-haric) hucre:", len(xs))
rng = np.random.default_rng(SEED + 9)
sec = rng.choice(len(xs), size=min(48, len(xs)), replace=False)
toplam_su = int(su.sum())
es = P["egim"]["esik"]

def gdal_fV(X, Y):
    with tempfile.TemporaryDirectory() as td:
        o = os.path.join(td, "v.tif")
        subprocess.run([str(QD), "-ox", str(X), "-oy", str(Y), "-oz", str(G["gozlemci_yuksekligi_m"]),
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
        return float((vv[ro[ok], co[ok]] == 255).sum()) / max(toplam_su, 1)

def fE_ornekle(X, Y):
    c = int((X - tr6.c) / abs(tr6.a) - 0.5); r = int((tr6.f - Y) / abs(tr6.e) - 0.5)
    r = min(max(r, 0), er.shape[0] - 1); c = min(max(c, 0), er.shape[1] - 1)
    v = float(er[r, c])
    return round(float(np.clip(1 - v / 3000.0, 0, 1)), 4) if np.isfinite(v) else 0.5

tab0 = pd.read_csv(CIK / "olcut_tablosu.csv")
tab0 = tab0[~tab0["nok_id"].str.startswith("B")].reset_index(drop=True)
g0 = g0[~g0["nok_id"].str.startswith("B")].reset_index(drop=True)
sat, nok = [], []
for j, i in enumerate(sec):
    X, Y = tr * (xs[i] + 0.5, ys[i] + 0.5)
    r, c = int(ys[i]), int(xs[i])
    fV = gdal_fV(X, Y)
    Rv, Sv = float(R[r, c]), float(egim[r, c])
    assert np.isfinite(Rv), f"R nan {j}"
    sat.append({"nok_id": f"B{j + 1:03d}", "tur": "kontrol_adayi", "x": X, "y": Y,
                "fV": round(fV, 4), "R": round(Rv, 2), "egim": round(Sv, 2),
                "fE": fE_ornekle(X, Y), "yontem": "gdal_viewshed", "yaka": "Avrupa"})
    nok.append({"nok_id": f"B{j + 1:03d}", "tur": "kontrol_adayi", "x": X, "y": Y})
    if (j + 1) % 12 == 0:
        print(f"{j + 1}/48...")
t = pd.DataFrame(sat)
v0 = tab0.loc[~tab0["nok_id"].str.startswith("A"), "R"].to_numpy(float)
lo, hi = np.percentile(v0, [5, 95])
t["fR"] = pd.Series(np.clip((t["R"].to_numpy(float) - lo) / max(hi - lo, 1e-9), 0, 1)).round(4)
t["fS"] = (1 - (t["egim"] - es["duz"]) / (es["dik"] - es["duz"])).clip(0, 1).round(4)
t.to_csv(CIK / "olcut_yogun_ek.csv", index=False)
yeni_g = gpd.GeoDataFrame(nok, geometry=[Point(n["x"], n["y"]) for n in nok], crs=crs)
pd.concat([g0, yeni_g], ignore_index=True).to_file(CIK / "ornek_noktalar.gpkg", driver="GPKG")
pd.concat([tab0, t[tab0.columns]], ignore_index=True).to_csv(CIK / "olcut_tablosu.csv", index=False)
print(f"-> birlesti: {len(tab0)} + {len(t)} = {len(tab0) + len(t)} nokta")
