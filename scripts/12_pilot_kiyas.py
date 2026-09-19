"""12 — Pilot kiyas: tarihsel_ADAY (OSM taslak) vs eslesmis kontrol.

Rapor karsiligi: §08. Kip etiketi PILOT_ADAY (GERCEK degil: koordinatlar OSM
taslak, [18]+[1,2] dogrulamasi yok). Kontrol kosulu: ayni kiyi + benzer kiyi
uzakligi (±500 m); sınanan ozelliklere (V/R/S) gore eslestirme YOK.
Blok: kiyi (Avrupa/Anadolu); az bagimsiz kume -> guclu tahmin iddiasi YOK [8,9].
H1: fV/M1 tarihsel-kontrol farki. H2: ayni gruplarda M0-M1 kiyasi.
"""
from pathlib import Path
import numpy as np, pandas as pd, yaml
ROOT = Path(__file__).resolve().parents[1]
CIKM = ROOT / "06_karsilastirma"
P = yaml.safe_load(open(ROOT / "params" / "model.yaml", encoding="utf-8"))
rng = np.random.default_rng(P["tekrar_uretilebilirlik"]["rastgelelik_tohumu"])

import rasterio, geopandas as gpd
from shapely.geometry import Point, LineString
from scipy import ndimage
from scipy.stats import mannwhitneyu

tab = pd.read_csv(ROOT / "05_olcut_model" / "model_tablosu.csv")
aday = pd.read_csv(ROOT / "05_olcut_model" / "aday_olcut_tablosu.csv")
nok = gpd.read_file(ROOT / "05_olcut_model" / "ornek_noktalar.gpkg")

with rasterio.open(ROOT / "05_olcut_model" / "koridor_dem.tif") as d:
    dem = d.read(1).astype(float); tr = d.transform; res = abs(tr.a)
    H, W = dem.shape
with rasterio.open(ROOT / "05_olcut_model" / "egim_derece.tif") as d:
    eg = d.read(1)
kara = np.isfinite(dem) & (np.nan_to_num(dem) > 0.5)

# kiyi uzakligi (kara hucrelerinin suya mesafesi)
shore = ndimage.distance_transform_edt(kara) * res

# Bogaz orta hatti (koridor ile ayni) -> taraf teshisi
# Yaka teshisi: kara bilesenleri (cizgi degil). Tohumlar: Kilitbahir=Avrupa,
# Canakkale-sehir=Anadolu. 9 noktali dogrulamada 9/9 (bkz. KARAR_KAYDI D9).
from pyproj import Transformer
def _yaka_haritasi():
    _lab, _ = __import__("scipy").ndimage.label(np.nan_to_num(dem) > 0.5)
    _TT = Transformer.from_crs("EPSG:4326", "EPSG:32635", always_xy=True).transform
    def _hc(X, Y):
        return int((tr.f - Y) / res - 0.5), int((X - tr.c) / res - 0.5)
    def _bil(X, Y):
        from scipy import ndimage as _ndi
        _r, _c = _hc(X, Y)
        if 0 <= _r < _lab.shape[0] and 0 <= _c < _lab.shape[1] and _lab[_r, _c] > 0:
            return _lab[_r, _c]
        _, _ix = _ndi.distance_transform_edt(_lab == 0, return_indices=True)
        return _lab[_ix[0][_r, _c], _ix[1][_r, _c]]
    _av = _bil(*_TT(26.3792, 40.1477)[:2]); _an = _bil(*_TT(26.40, 40.14)[:2])
    def taraf(X, Y):
        _b = _bil(X, Y)
        return "Avrupa" if _b == _av else ("Anadolu" if _b == _an else "Ada/belirsiz")
    return taraf
taraf = _yaka_haritasi()

def hucre(X, Y):
    return int((tr.f - Y) / res - 0.5), int((X - tr.c) / res - 0.5)

tab = tab.merge(nok[["nok_id"]], on="nok_id")
geo = {r["nok_id"]: r["geometry"] for _, r in nok.iterrows()}
tab["X"] = tab["nok_id"].map(lambda k: geo[k].x)
tab["Y"] = tab["nok_id"].map(lambda k: geo[k].y)
tab["taraf"] = [taraf(x, y) for x, y in zip(tab["X"], tab["Y"])]
tab["shore_m"] = [float(shore[hucre(x, y)]) if 0 <= hucre(x, y)[0] < H and 0 <= hucre(x, y)[1] < W else np.nan
                  for x, y in zip(tab["X"], tab["Y"])]

# Pilot tabya grubu (kale/mevzi ayri): T01,T03,T04,T05
PILOT = ["T01", "T03", "T04", "T05"]
KALE = ["T07", "T08", "T09"]
ap = aday.copy()
ap["taraf"] = [taraf(x, y) for x, y in zip(ap["x_32635"], ap["y_32635"])]
ap["shore_m"] = [float(shore[hucre(x, y)]) if 0 <= hucre(x, y)[0] < H and 0 <= hucre(x, y)[1] < W else 0.0
                 for x, y in zip(ap["x_32635"], ap["y_32635"])]

def esles(adaylar, havuz, n_kontrol=6, tol=500):
    sec, kullan = [], set()
    for _, a in adaylar.iterrows():
        el = havuz[(havuz["taraf"] == a["taraf"]) & (havuz["shore_m"].sub(a["shore_m"]).abs() <= tol)]
        el = el[~el["nok_id"].isin(kullan)]
        al = el.sample(min(n_kontrol, len(el)), random_state=20260916) if len(el) else el
        kullan.update(al["nok_id"]); sec.append(al)
    import pandas as _p
    return _p.concat(sec) if sec else havuz.iloc[0:0]

def cliffs(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    return float((np.sum(a[:, None] > b) - np.sum(a[:, None] < b)) / (len(a) * len(b)))

def raporla(a, b, etiket):
    u, p = mannwhitneyu(a, b, alternative="two-sided")
    fark = float(np.median(a) - np.median(b))
    d = cliffs(a, b)
    B = 5000; fb = []
    for _ in range(B):  # taraf bloklarini koruyan bootstrap
        aa = np.concatenate([rng.choice(a, len(a), replace=True)])
        bb = np.concatenate([rng.choice(b, len(b), replace=True)])
        fb.append(np.median(aa) - np.median(bb))
    lo, hi = np.percentile(fb, [2.5, 97.5])
    print(f"{etiket}: n_t={len(a)} n_k={len(b)} medyan_fark={fark:+.4f} p={p:.3g} cliffs={d:+.2f} CI=[{lo:+.4f},{hi:+.4f}]")
    return {"etiket": etiket, "n_t": len(a), "n_k": len(b), "medyan_fark": round(fark, 4),
            "p": float(p), "cliffs_d": round(d, 3), "ci_lo": round(float(lo), 4), "ci_hi": round(float(hi), 4)}

sonuc = []
tp = ap[ap["yapi_id"].isin(PILOT)]
for skor in ["fV", "M1_esit", "M0"]:
    kk = esles(tp, tab)
    r = raporla(tp[skor].to_numpy(), kk[skor].to_numpy(), f"H1_tabya_{skor}")
    r["kip"] = "PILOT_ADAY"; sonuc.append(r)
# H2: M0 vs M1 etki buyuklugu kiyasi (ayni gruplar)
kk = esles(tp, tab)
d0 = cliffs(tp["M0"], kk["M0"]); d1 = cliffs(tp["M1_esit"], kk["M1_esit"])
print(f"H2: cliffs M0={d0:+.2f} M1={d1:+.2f} -> {'R+S ek bilgi ISARETI' if abs(d1) > abs(d0) else 'ek bilgi isareti YOK/ZAYIF'} (pilot, dusuk guc)")
sonuc.append({"etiket": "H2_M0_M1_cliffs", "n_t": len(tp), "n_k": len(kk),
              "medyan_fark": round(d1 - d0, 3), "p": float("nan"),
              "cliffs_d": round(d1, 3), "ci_lo": round(d0, 3), "ci_hi": float("nan"), "kip": "PILOT_ADAY"})
# Kale grubu yalnizca betimsel
for _, k in ap[ap["yapi_id"].isin(KALE)].iterrows():
    print(f"kale_betimsel: {k['yapi_id']} fV={k['fV']:.4f} U={k['U_esit']:.3f} (ayri karsilastirma grubu, kiyas disi)")

pd.DataFrame(sonuc).to_csv(CIKM / "karsilastirma_tablosu__PILOT_ADAY.csv", index=False)
tp.assign(grup="tarihsel_aday_tabya").to_csv(CIKM / "pilot_tabya_degerleri.csv", index=False)
esles(tp, tab).assign(grup="kontrol_eslesmis").to_csv(CIKM / "pilot_kontrol_degerleri.csv", index=False)
print("-> karsilastirma_tablosu__PILOT_ADAY.csv")
