"""14 — Tamamlayici analizler: kumulatif gorus + OWA saglamlik.

Rapor karsiligi: §04 (gorevli yontemler), [5,7] + [4,10].
(a) Kumulatif gorus: 8 adayn gdal_viewshed rasterlarinin toplami (koridor
    penceresi). Yorum siniri: gorsel baglanti != haberlesme kaniti.
(b) OWA: 3 olcutte orness senaryolari (OR=1.0, notr=0.5, AND=0.0); M1 ile
    sira korelasyonu (Spearman); uyusmazlik aciklanir.
Cikti: 05_olcut_model/kumulatif_gorus.tif, gorsel_ag.csv, owa_tablosu.csv
"""
from pathlib import Path
import numpy as np, pandas as pd, yaml, subprocess, tempfile, os
ROOT = Path(__file__).resolve().parents[1]
CIK = ROOT / "05_olcut_model"
P = yaml.safe_load(open(ROOT / "params" / "model.yaml", encoding="utf-8"))
G = P["gorus"]
QD = Path(r"C:\Program Files\QGIS 4.2.2\bin\gdal_viewshed.exe")

import rasterio
aday = pd.read_csv(CIK / "aday_olcut_tablosu.csv")

with rasterio.open(CIK / "koridor_dem.tif") as d:
    dem = d.read(1); tr = d.transform; crs = d.crs; res = abs(tr.a)
H, W = dem.shape

kum = np.zeros((H, W), dtype=np.float32)
ag_sat = []
for _, a in aday.iterrows():
    with tempfile.TemporaryDirectory() as td:
        o = os.path.join(td, "v.tif")
        cmd = [str(QD), "-ox", str(a["x_32635"]), "-oy", str(a["y_32635"]),
               "-oz", str(G["gozlemci_yuksekligi_m"]), "-tz", str(G["hedef_yuksekligi_m"]),
               "-md", str(G["mesafe_siniri_m"]), "-cc", str(G["refraksiyon_katsayisi"]),
               "-iv", "0", str(CIK / "koridor_dem.tif"), o]
        subprocess.run(cmd, capture_output=True, timeout=180, check=True)
        with rasterio.open(o) as dd:
            vv = dd.read(1); vt = dd.transform
        # koridor gridine izdusur (dunya koordinatiyla)
        ys, xs = np.mgrid[0:H, 0:W]
        Xs = tr.c + (xs + 0.5) * res; Ys = tr.f - (ys + 0.5) * res
        inv = ~vt
        co = (inv.a * Xs + inv.b * Ys + inv.c).astype(int)
        ro = (inv.d * Xs + inv.e * Ys + inv.f).astype(int)
        ok = (ro >= 0) & (ro < vv.shape[0]) & (co >= 0) & (co < vv.shape[1])
        gor = np.zeros((H, W), bool); gor[ok] = (vv[ro[ok], co[ok]] == 255)
        kum += gor.astype(np.float32)
        ag_sat.append({"nok_id": a["yapi_id"], "gorulen_hucre": int(gor.sum())})

m = dict(driver="GTiff", height=H, width=W, count=1, dtype="float32", crs=crs,
         transform=tr, nodata=np.nan, compress="deflate", tiled=True)
with rasterio.open(CIK / "kumulatif_gorus.tif", "w", **m) as d:
    d.write(np.where(np.isfinite(dem), kum, np.nan).astype(np.float32), 1)
print("kumulatif gorus: maks ortak gorunurluk =", int(np.nanmax(np.where(np.isfinite(dem), kum, np.nan))),
      "/ 8 aday")

# gorsel ag: adaylar arasi karsilikli gorus (hucre degeri)
ag = pd.DataFrame(ag_sat).set_index("nok_id")
mat = []
rc = {}
for _, a in aday.iterrows():
    c = int((a["x_32635"] - tr.c) / res - 0.5); r = int((tr.f - a["y_32635"]) / res - 0.5)
    rc[a["yapi_id"]] = (r, c)
with rasterio.open(CIK / "kumulatif_gorus.tif") as d:
    pass
# tek-tek: her adayn penceresini yeniden okumak yerine hizli numpy LOS (kisa mesafe)
def los(r0, c0, r1, c1, obs_h=4.0):
    n = max(abs(r1 - r0), abs(c1 - c0), 1)
    rr = np.clip(np.linspace(r0, r1, n + 1).astype(int), 0, H - 1)
    cc = np.clip(np.linspace(c0, c1, n + 1).astype(int), 0, W - 1)
    h = dem[rr, cc]
    if not np.all(np.isfinite(h)): return False
    dd = np.arange(n + 1) * res
    los = (dem[r0, c0] + obs_h) + ((0.0 - (dem[r0, c0] + obs_h)) * dd / max(dd[-1], 1e-9))
    return bool(np.all(h[1:-1] <= los[1:-1] + 0.5))
sat = []
ids = list(rc)
for i in ids:
    for j in ids:
        if i == j: continue
        sat.append({"kaynak": i, "hedef": j,
                    "gorus_var": los(*rc[i], *rc[j])})
pd.DataFrame(sat).to_csv(CIK / "gorsel_ag.csv", index=False)
print(f"gorsel ag: {sum(s['gorus_var'] for s in sat)}/{len(sat)} yonlu bag (kanit degil, tamamlayici)")

# (b) OWA
from scipy.stats import spearmanr
tab = pd.read_csv(CIK / "model_tablosu.csv")
tum = pd.concat([tab[["nok_id", "fV", "fR", "fS"]],
                 aday.rename(columns={"yapi_id": "nok_id"})[["nok_id", "fV", "fR", "fS"]]],
                ignore_index=True)
F = tum[["fV", "fR", "fS"]].to_numpy()
srt = np.sort(F, axis=1)  # kucukten buyuge
owa = {"OWA_OR": srt[:, 2], "OWA_notr": srt.mean(axis=1), "OWA_AND": srt[:, 0]}
w = P["agirliklar"]["esit"]
m1 = w["wV"] * F[:, 0] + w["wR"] * F[:, 1] + w["wS"] * F[:, 2]
out = pd.DataFrame({"nok_id": tum["nok_id"], "M1_esit": np.round(m1, 4),
    "OWA_OR": np.round(owa["OWA_OR"], 4), "OWA_notr": np.round(owa["OWA_notr"], 4),
    "OWA_AND": np.round(owa["OWA_AND"], 4)})
for k in ["OWA_OR", "OWA_notr", "OWA_AND"]:
    rho, _ = spearmanr(m1, out[k])
    print(f"{k} vs M1: Spearman rho={rho:.3f}")
out.to_csv(CIK / "owa_tablosu.csv", index=False)
open(CIK / "OWA_NOTU.md", "w", encoding="utf-8").write(
 "# OWA notu (§04 istege bagli saglamlik)\n\n- OR: tek guclu olcut yeter; AND: tum olcutler gerekli.\n"
 "- Telafi varsayimi degisiminin sirayi bozup bozmadigina bakilir; uyusmazlik ana sonucla birlikte aciklanir [4,10].\n"
 "- Yuksek rho: sonuc telafi varsayimina duyarsiz (kararli); dusuk rho: agirlik/OWA birlikte raporlanir.\n")
print("-> kumulatif_gorus.tif + gorsel_ag.csv + owa_tablosu.csv")
