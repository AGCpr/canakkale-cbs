"""27 — Monte Carlo: agirlik + R-yaricapi uzayinda kararililik (yakinsama izlemeli).

Rapor karsiligi: §09 ("dagilimlar gerekcelendirilebiliyorsa Monte Carlo" [10]).
Dagilimlar: w ~ Dirichlet(6,6,6) (esit-merkezli, dusuk daginiklik);
R yaricapi ~ {500,1000,2000} es-olasilik. fV sabit (gdal 4 m; gozlemci
belirsizligi ayri senaryo). Yakinsama: T05/T07 P(ust) 100 cekimde bir;
son 500'luk pencerede maks degisim <0.005 ise dur (min 1000, maks 5000).
Cikti: 07_belirsizlik/mc_aday.csv + mc_yakinsama.png + MC_NOTU.md.
"""
from pathlib import Path
import numpy as np, pandas as pd, yaml

ROOT = Path(__file__).resolve().parents[1]
BEL = ROOT / "07_belirsizlik"
P = yaml.safe_load(open(ROOT / "params" / "model.yaml", encoding="utf-8"))
SEED = P["tekrar_uretilebilirlik"]["rastgelelik_tohumu"]
rng = np.random.default_rng(SEED)

import rasterio
import geopandas as gpd
from scipy import ndimage

with rasterio.open(ROOT / "05_olcut_model" / "koridor_dem.tif") as d:
    dem = d.read(1).astype(float); tr = d.transform; res = abs(tr.a)
    H, W = dem.shape
nz = np.load(ROOT / "05_olcut_model" / "r_duyarlilik.npz")
R500, R2000 = nz["r500"], nz["r2000"]
_rp = int(round(1000 / res))
_yy, _xx = np.ogrid[-_rp:_rp + 1, -_rp:_rp + 1]
_kk = (_xx * _xx + _yy * _yy <= _rp * _rp).astype(float); _kk /= _kk.sum()
_mz = np.isfinite(dem).astype(float)
R1000 = dem - (ndimage.convolve(np.nan_to_num(np.where(np.isfinite(dem), dem, 0.0)), _kk, mode="nearest")
               / np.maximum(ndimage.convolve(_mz, _kk, mode="nearest"), 1e-6))

def fR_harita(R):
    v = R[np.isfinite(R)]; lo, hi = np.percentile(v, [5, 95])
    return np.clip((R - lo) / max(hi - lo, 1e-9), 0, 1)

F = {500: fR_harita(R500), 1000: fR_harita(R1000), 2000: fR_harita(R2000)}

def hucre(X, Y):
    return int((tr.f - Y) / res - 0.5), int((X - tr.c) / res - 0.5)

tab = pd.read_csv(ROOT / "05_olcut_model" / "model_tablosu.csv")
nok = gpd.read_file(ROOT / "05_olcut_model" / "ornek_noktalar.gpkg").set_index("nok_id")
ad = pd.read_csv(ROOT / "05_olcut_model" / "aday_olcut_tablosu.csv")

def nokta_fR(X, Y):
    r, c = hucre(X, Y)
    r = min(max(r, 0), H - 1); c = min(max(c, 0), W - 1)
    return {rr: round(float(F[rr][r, c]), 4) for rr in (500, 1000, 2000)}

kAd, kCt = {}, {}
for _, r in ad.iterrows():
    kAd[r["yapi_id"]] = {"fV": r["fV"], "fS": r["fS"], "fR": nokta_fR(r["x_32635"], r["y_32635"])}
for _, r in tab.iterrows():
    g = nok.loc[r["nok_id"], "geometry"]
    kCt[r["nok_id"]] = {"fV": r["fV"], "fS": r["fS"], "fR": nokta_fR(g.x, g.y)}

RADII = [500, 1000, 2000]
ust = {k: [] for k in kAd}
iz = {k: [] for k in ("T05", "T07")}
N, n = 5000, 0
while n < N:
    n += 100
    Wm = rng.dirichlet([6, 6, 6], size=100)
    Rm = rng.choice(RADII, size=100)
    for i in range(100):
        w, rr = Wm[i], int(Rm[i])
        Uc = np.array([w[0] * v["fV"] + w[1] * v["fR"][rr] + w[2] * v["fS"] for v in kCt.values()])
        esik = np.quantile(Uc, 0.8)
        for k, v in kAd.items():
            U = w[0] * v["fV"] + w[1] * v["fR"][rr] + w[2] * v["fS"]
            ust[k].append((U, U >= esik))
    for k in iz:
        iz[k].append(float(np.mean([u[1] for u in ust[k]])))
    if n >= 1000:
        deg = max(abs(iz[k][-1] - iz[k][-6]) for k in iz)
        if deg < 0.005:
            break
print(f"cekim: {n} (yakinsama {'saglandi' if n < N else 'saglanamadi'})")

sat = []
for k, L in ust.items():
    U = np.array([u[0] for u in L]); B = np.array([u[1] for u in L])
    sat.append({"yapi_id": k, "cekim": n, "U_ort": round(float(U.mean()), 4),
                "U_sd": round(float(U.std()), 4), "P_ust": round(float(B.mean()), 3)})
pd.DataFrame(sat).to_csv(BEL / "mc_aday.csv", index=False)

import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(7, 4))
xs = np.arange(100, n + 1, 100)
for k in iz:
    ax.plot(xs, iz[k], label=k)
ax.set_xlabel("cekim"); ax.set_ylabel("P(ust-sinif)"); ax.legend(); ax.set_ylim(0, 1)
fig.tight_layout(); fig.savefig(BEL / "mc_yakinsama.png", dpi=130)
open(BEL / "MC_NOTU.md", "w", encoding="utf-8").write(
 "# Monte Carlo notu (§09)\n\n- w~Dirichlet(6,6,6); R~{500,1000,2000}; fV sabit.\n"
 f"- Cekim {n}; durma: son 500'de P degisimi <0.005 (T05/T07 izlenir).\n"
 "- Yorum: P degeri olasilik degil, cekim-kumesi kosullu kararlilik frekansidir.\n")
print(pd.DataFrame(sat).to_string(index=False))
