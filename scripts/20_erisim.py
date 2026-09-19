"""20 — Erisim maliyeti (fE) + M2 gerekceli ek model.

Rapor karsiligi: §04 (maliyetli mesafe [6]) + §06 (M2). Donem yolu/iskele
verisi YOK -> modern arazi uzerinden egim-tabanli maliyet vekili; ayri senaryo
olarak isaretlenir, ana sonucla karistirilmaz.
Yontem: 60 m gridde kiyidan ic kesimlere Dijkstra (maliyet = 1 + (egim/10)^2);
fE = ters-dogrusal normalize. M2 agirliklari params/erisim'den.
Cikti: erisim_maliyet.tif, fE nokta sutunu, M2 skoru + H2b kiyasi.
"""
from pathlib import Path
import heapq
import numpy as np, pandas as pd, yaml

ROOT = Path(__file__).resolve().parents[1]
CIK = ROOT / "05_olcut_model"
P = yaml.safe_load(open(ROOT / "params" / "model.yaml", encoding="utf-8"))
import rasterio

with rasterio.open(CIK / "koridor_dem.tif") as d:
    dem = d.read(1).astype(float); tr = d.transform; crs = d.crs
    res = abs(tr.a); H, W = dem.shape
with rasterio.open(CIK / "egim_derece.tif") as d:
    eg = d.read(1).astype(float)
kara = np.nan_to_num(dem) > 0.5

# 60 m'ye indirge (hiz)
f = 2
dem6 = dem[:H // f * f, :W // f * f].reshape(H // f, f, W // f, f).mean(axis=(1, 3))
eg6 = np.nanmean(eg[:H // f * f, :W // f * f].reshape(H // f, f, W // f, f), axis=(1, 3))
kara6 = kara[:H // f * f, :W // f * f].reshape(H // f, f, W // f, f).any(axis=(1, 3))
h6, w6 = dem6.shape
from affine import Affine
tr6 = Affine(tr.a * f, 0, tr.c, 0, tr.e * f, tr.f)

# kiyi hucreleri: karanin su-komsulu pikselleri
from scipy import ndimage
su6 = np.isfinite(dem6) & ~kara6
kenar = kara6 & ndimage.binary_dilation(su6, iterations=1)
mal = np.full((h6, w6), np.inf)
mal[kenar] = 0.0
pq = [(0.0, int(r), int(c)) for r, c in zip(*np.where(kenar))]
heapq.heapify(pq)
gider = 1 + (np.nan_to_num(eg6, nan=30.0) / 10.0) ** 2
while pq:
    m0, r, c = heapq.heappop(pq)
    if m0 > mal[r, c]:
        continue
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if not dr and not dc:
                continue
            rr, cc = r + dr, c + dc
            if 0 <= rr < h6 and 0 <= cc < w6 and kara6[rr, cc]:
                wstep = (gider[r, c] + gider[rr, cc]) / 2 * (1.4142 if dr and dc else 1.0)
                if mal[r, c] + wstep < mal[rr, cc]:
                    mal[rr, cc] = mal[r, c] + wstep
                    heapq.heappush(pq, (mal[rr, cc], rr, cc))
malf = mal[np.isfinite(mal) & kara6]
lo, hi = np.percentile(malf, [5, 95])
fE6 = np.clip(1 - (mal - lo) / max(hi - lo, 1e-9), 0, 1)
fE6[~kara6] = np.nan
m = dict(driver="GTiff", height=h6, width=w6, count=1, dtype="float32", crs=crs,
         transform=tr6, nodata=np.nan, compress="deflate", tiled=True)
with rasterio.open(CIK / "erisim_maliyet.tif", "w", **m) as d:
    d.write(np.where(kara6, mal, np.nan).astype(np.float32), 1)

# nokta ornekleme (30 m koordinat -> 60 m hucre)
def ornekle(X, Y):
    c = int((X - tr6.c) / abs(tr6.a) - 0.5); r = int((tr6.f - Y) / abs(tr6.e) - 0.5)
    r = min(max(r, 0), h6 - 1); c = min(max(c, 0), w6 - 1)
    return float(fE6[r, c]) if np.isfinite(fE6[r, c]) else 0.5

import geopandas as gpd
nok = gpd.read_file(CIK / "ornek_noktalar.gpkg").set_index("nok_id")
tab = pd.read_csv(CIK / "model_tablosu.csv")
tab["fE"] = [round(ornekle(nok.loc[k, "geometry"].x, nok.loc[k, "geometry"].y), 4)
             for k in tab["nok_id"]]
ad = pd.read_csv(CIK / "aday_olcut_tablosu.csv")
ad["fE"] = [round(ornekle(x, y), 4) for x, y in zip(ad["x_32635"], ad["y_32635"])]
WE = P["erisim"]["agirliklar_M2"]
tab["M2"] = (WE["wV"] * tab["fV"] + WE["wR"] * tab["fR"] + WE["wS"] * tab["fS"] + WE["wE"] * tab["fE"]).round(4)
ad["M2"] = (WE["wV"] * ad["fV"] + WE["wR"] * ad["fR"] + WE["wS"] * ad["fS"] + WE["wE"] * ad["fE"]).round(4)
tab.to_csv(CIK / "model_tablosu.csv", index=False)
ad.to_csv(CIK / "aday_olcut_tablosu.csv", index=False)

# H2b: M1 vs M2 etki (pilot tabya vs eslesmis kontrol)
kk = pd.read_csv(ROOT / "06_karsilastirma" / "pilot_kontrol_degerleri.csv")
tp = ad[ad["yapi_id"].isin(["T01", "T03", "T04", "T05"])]
k2 = tab[tab["nok_id"].isin(kk["nok_id"])]
from scipy.stats import mannwhitneyu
def cliffs(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    return float((np.sum(a[:, None] > b) - np.sum(a[:, None] < b)) / (len(a) * len(b)))
for kol in ["M1_esit", "M2"]:
    u_, p_ = mannwhitneyu(tp[kol], k2[kol], alternative="two-sided")
    print(f"H2b-{kol}: fark={np.median(tp[kol])-np.median(k2[kol]):+.4f} p={p_:.3g} cliffs={cliffs(tp[kol], k2[kol]):+.2f}")
open(CIK / "ERISIM_NOTU.md", "w", encoding="utf-8").write(
 "# Erisim notu (§04 veriye-bagli ek)\n\n- Donem yolu/iskele yok -> modern egim-maliyeti VEKIL; ana model disi senaryo.\n"
 "- Maliyet: 60 m grid Dijkstra, kiyidan iceri, agirlik 1+(egim/10)^2; fE ters-dogrusal.\n"
 f"- M2 agirlik: {WE} (params/erisim).\n")
print("-> erisim_maliyet.tif + fE/M2 sutunlari")
