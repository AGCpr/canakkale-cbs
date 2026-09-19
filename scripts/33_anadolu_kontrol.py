"""33 — Anadolu kontrol ekleme (v2): koridor-ici dar maske + bilesen esleme.

Bulgu D10: 48 kontrolun tamami Avrupa; sebebi ornekleme degil, karsilastirma
sonrasi yaka etiketleriydi — 04 seridi koridor-icidir ve gecerlidir.
Bu betik ayni dar-maske kuraliyla Anadolu seridinden 16 nokta ekler:
serit = dar-kara & ~erozyon & (bilesen==Anadolu).
bilesen: dar-maske etiketleri genis-maske 284 ile cogunluk oyuyla eslenir.
Olcek DONDURULDU (p5/p95 ilk 48'den). Tekrar calisirsa onceki A-ekleri siler.
Cikti: olcut_tablosu 48->64, ornek_noktalar 48->64.
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
assert kara_dar.shape == (H, W), (kara_dar.shape, (H, W))
lab_dar, _ = ndimage.label(kara_dar)
# genis-maske 284 (Anadolu) ile esle
kara_genis = np.nan_to_num(dem) > 0.5
lab_genis, _ = ndimage.label(kara_genis)
from pyproj import Transformer
TTT = Transformer.from_crs("EPSG:4326", "EPSG:32635", always_xy=True).transform
Xa, Ya = TTT(26.40, 40.14)[:2]
ra, ca = int((tr.f - Ya) / res - 0.5), int((Xa - tr.c) / res - 0.5)
if lab_genis[ra, ca] == 0:
    _, ix = ndimage.distance_transform_edt(lab_genis == 0, return_indices=True)
    ANAD_GENIS = lab_genis[ix[0][ra, ca], ix[1][ra, ca]]
else:
    ANAD_GENIS = lab_genis[ra, ca]
oy = {}
for b in np.unique(lab_dar[lab_dar > 0]):
    m = (lab_dar == b) & kara_dar
    oy[b] = (m & (lab_genis == ANAD_GENIS)).sum() / max(m.sum(), 1)
ANAD = max(oy, key=oy.get)
s1 = int(((lab_dar == ANAD)).sum()); s0 = int(kara_dar.sum())
print(f"dar-maske: {lab_dar.max()} bilesen; Anadolu payi {s1}/{s0} = {s1 / max(s0, 1):.3f}")

er2 = ndimage.binary_erosion(kara_dar, iterations=int(2000 / res))
serit = kara_dar & ~er2 & (lab_dar == ANAD)
ys, xs = np.where(serit)
print("Anadolu serit hucre:", len(xs))
rng = np.random.default_rng(SEED + 8)
sec = rng.choice(len(xs), size=min(16, len(xs)), replace=False)
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

# geri alma: onceki kotu ek varsa sil (idempotent)
tab0 = pd.read_csv(CIK / "olcut_tablosu.csv")
tab0 = tab0[~tab0["nok_id"].str.startswith("A")].reset_index(drop=True)
g0 = gpd.read_file(CIK / "ornek_noktalar.gpkg")
g0 = g0[~g0["nok_id"].str.startswith("A")].reset_index(drop=True)
print(f"geri alma sonrasi: {len(tab0)} nokta")

sat, nok = [], []
for j, i in enumerate(sec):
    X, Y = tr * (xs[i] + 0.5, ys[i] + 0.5)
    r, c = int(ys[i]), int(xs[i])
    fV = gdal_fV(X, Y)
    Rv, Sv = float(R[r, c]), float(egim[r, c])
    assert np.isfinite(Rv), f"R nan {j}"
    sat.append({"nok_id": f"A{j + 1:03d}", "tur": "kontrol_adayi", "x": X, "y": Y,
                "fV": round(fV, 4), "R": round(Rv, 2), "egim": round(Sv, 2),
                "fE": fE_ornekle(X, Y), "yontem": "gdal_viewshed", "yaka": "Anadolu"})
    nok.append({"nok_id": f"A{j + 1:03d}", "tur": "kontrol_adayi", "x": X, "y": Y})
    print(f"A{j + 1:03d} fV={fV:.4f} R={Rv:.1f}")

t = pd.DataFrame(sat)
v0 = tab0["R"].to_numpy(float)
lo, hi = np.percentile(v0, [5, 95])
print(f"dondurulmus olcek: p5={lo:.2f} p95={hi:.2f}")
t["fR"] = pd.Series(np.clip((t["R"].to_numpy(float) - lo) / max(hi - lo, 1e-9), 0, 1)).round(4)
t["fS"] = (1 - (t["egim"] - es["duz"]) / (es["dik"] - es["duz"])).clip(0, 1).round(4)
t.to_csv(CIK / "olcut_anadolu_ek.csv", index=False)
yeni_g = gpd.GeoDataFrame(nok, geometry=[Point(n["x"], n["y"]) for n in nok], crs=crs)
pd.concat([g0, yeni_g], ignore_index=True).to_file(CIK / "ornek_noktalar.gpkg", driver="GPKG")
pd.concat([tab0, t[tab0.columns]], ignore_index=True).to_csv(CIK / "olcut_tablosu.csv", index=False)
print(f"-> birlesti: {len(tab0)} + {len(t)} = {len(tab0) + len(t)} nokta")
