"""32 — K3-GERCEK: kurumsal 7 tabya vs bantli kontrol + ablasyon + Pareto + Dirichlet.

Eslesme (cba bant tasarimi uyarlamasi): ayni yaka + kiyi bandi
([0,300),[300,1000),[1000,2000),[2000,inf)) + kuzey ±2 km + tum referanslarin
150 m cevresi haric. Kontrol yoklugu kanitlamaz; <5 kontrolde yuzdelik yok.
Ablasyon: M0 / geometrik / tek-olcut-cikarma (Spearman + ust20 Jaccard).
Agirlik: Dirichlet(1,1,1) x2000 (ucgen-tamami). Pareto: baskinlanmayanlar.
Cikti: 06_karsilastirma/K3_GERCEK_HUKMU.md + gercek_kiyas.json
"""
from pathlib import Path
import json
import numpy as np, pandas as pd, yaml

ROOT = Path(__file__).resolve().parents[1]
CIKM = ROOT / "06_karsilastirma"
P = yaml.safe_load(open(ROOT / "params" / "model.yaml", encoding="utf-8"))
SEED = P["tekrar_uretilebilirlik"]["rastgelelik_tohumu"]
rng = np.random.default_rng(SEED)

import rasterio, geopandas as gpd
from shapely.geometry import LineString
from scipy import ndimage
from scipy.stats import mannwhitneyu, spearmanr
from pyproj import Transformer
from shapely.ops import transform as _t

tab = pd.read_csv(ROOT / "05_olcut_model" / "model_tablosu.csv")
kur = pd.read_csv(ROOT / "05_olcut_model" / "kurumsal_olcut.csv")
tas = pd.read_csv(ROOT / "05_olcut_model" / "aday_olcut_tablosu.csv")
nok = gpd.read_file(ROOT / "05_olcut_model" / "ornek_noktalar.gpkg").set_index("nok_id")
with rasterio.open(ROOT / "05_olcut_model" / "koridor_dem.tif") as d:
    dem = d.read(1).astype(float); tr = d.transform; res = abs(tr.a)
kara = np.nan_to_num(dem) > 0.5
shore = ndimage.distance_transform_edt(kara) * res
# Yaka teshisi: kara bilesenleri (cizgi degil). Tohumlar: Kilitbahir=Avrupa,
# Canakkale-sehir=Anadolu. 9 noktali dogrulamada 9/9 (bkz. KARAR_KAYDI D9).
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

def band(s):
    return 0 if s < 300 else 1 if s < 1000 else 2 if s < 2000 else 3

geo = {k: (r.geometry.x, r.geometry.y) for k, r in nok.iterrows()}
tab = tab.copy()
tab["X"] = tab["nok_id"].map(lambda k: geo[k][0])
tab["Y"] = tab["nok_id"].map(lambda k: geo[k][1])
tab["taraf"] = [taraf(x, y) for x, y in zip(tab["X"], tab["Y"])]
tab["shore_m"] = [float(shore[hucre(x, y)]) for x, y in zip(tab["X"], tab["Y"])]
tab["band"] = tab["shore_m"].map(band)

TABYA = ["R01", "R02", "R03", "R04", "R05", "R06", "R07"]
tp = kur[kur["kayit_id"].isin(TABYA)].copy()
tp["taraf"] = [taraf(x, y) for x, y in zip(tp["x_32635"], tp["y_32635"])]
tp["shore_m"] = [float(shore[hucre(x, y)]) for x, y in zip(tp["x_32635"], tp["y_32635"])]
tp["band"] = tp["shore_m"].map(band)

# dislama: tum referanslarin 150 m cevresi
ref_xy = list(zip(tp["x_32635"], tp["y_32635"])) + \
    list(zip(tas["x_32635"], tas["y_32635"]))
def uzakta(x, y):
    return all(np.hypot(x - rx, y - ry) > 150 for rx, ry in ref_xy)

esles = {}
for _, a in tp.iterrows():
    el = tab[(tab["taraf"] == a["taraf"]) & (tab["band"] == a["band"])]
    el = el[[uzakta(x, y) for x, y in zip(el["X"], el["Y"])]]
    # cba ±2 km penceresi seyrek agda bos doner; ayni niyetle en yakin 6 secilir
    # (yaka+bant korunur). Referans basina <5 kontrolde yuzdelik yok (cba kurali).
    el = el.iloc[(el["Y"].sub(a["y_32635"]).abs()).argsort()[:6]]
    esles[a["kayit_id"]] = el
kk = pd.concat(esles.values()) if esles else tab.iloc[0:0]
print("eslesmis kontrol:", {k: len(v) for k, v in esles.items()}, "toplam", len(kk))

def cliffs(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    return float((np.sum(a[:, None] > b) - np.sum(a[:, None] < b)) / (len(a) * len(b)))

sonuc = {}
A = tp["U_esit"].to_numpy(); B = kk["U_esit"].to_numpy() if len(kk) else tab["U_esit"].to_numpy()
guc_yeterli = all(len(v) >= 5 for v in esles.values()) and len(kk) >= 5
u_, p_ = mannwhitneyu(A, B, alternative="two-sided")
sonuc["H1_M1"] = {"n_t": len(A), "n_k": len(B), "fark": round(float(np.median(A) - np.median(B)), 4),
                  "p": round(float(p_), 4) if guc_yeterli else None,
                  "delta": round(cliffs(A, B), 2),
                  "cikarim": "test" if guc_yeterli else "betimsel (n_k<5 referans var)"}
A0 = tp["fV"].to_numpy(); B0 = kk["fV"].to_numpy() if len(kk) else tab["fV"].to_numpy()
u0, p0 = mannwhitneyu(A0, B0, alternative="two-sided")
sonuc["H1_fV"] = {"fark": round(float(np.median(A0) - np.median(B0)), 4),
                  "p": round(float(p0), 4) if guc_yeterli else None,
                  "delta": round(cliffs(A0, B0), 2)}
print("H1_M1:", sonuc["H1_M1"]); print("H1_fV:", sonuc["H1_fV"])

# Ablasyon (kontroller uzerinde sira etkisi)
F = tab[["fV", "fR", "fS"]].to_numpy()
w = P["agirliklar"]["esit"]
m1 = w["wV"] * F[:, 0] + w["wR"] * F[:, 1] + w["wS"] * F[:, 2]
def ust20(v):
    return set(np.where(v >= np.quantile(v, 0.8))[0])
ref = ust20(m1)
abl = {"M0_yalniz_gorus": F[:, 0],
       "geometrik": (F[:, 0] * F[:, 1] * F[:, 2]) ** (1 / 3),
       "V_haric": (F[:, 1] + F[:, 2]) / 2,
       "R_haric": (F[:, 0] + F[:, 2]) / 2,
       "S_haric": (F[:, 0] + F[:, 1]) / 2}
sonuc["ablasyon"] = []
for ad_, v in abl.items():
    rho, _ = spearmanr(m1, v)
    ju = len(ref & ust20(v)) / max(len(ref | ust20(v)), 1)
    sonuc["ablasyon"].append({"model": ad_, "spearman": round(float(rho), 3),
                              "ust20_jaccard": round(float(ju), 3)})
    print(ad_, f"rho={rho:.3f} J={ju:.3f}")

# Pareto (kontroller + tabya)
hepsi = pd.concat([tab[["nok_id", "fV", "fR", "fS"]].rename(columns={"nok_id": "id"}),
                   tp[["kayit_id", "fV", "fR", "fS"]].rename(columns={"kayit_id": "id"})],
                  ignore_index=True)
M = hepsi[["fV", "fR", "fS"]].to_numpy()
dom = (M[:, None, :] >= M[None, :, :]).all(axis=2) & (M[:, None, :] > M[None, :, :]).any(axis=2)
pareto = hepsi[~dom.any(axis=0)]
sonuc["pareto_n"] = int(len(pareto))
sonuc["pareto_tabya"] = sorted(pareto[pareto["id"].str.startswith("R")]["id"].tolist())
print("Pareto:", len(pareto), "kume (tabya:", sonuc["pareto_tabya"], ")")

# Dirichlet(1,1,1) x2000 — kurumsal P(ust), vektorize
Wm = rng.dirichlet([1, 1, 1], size=2000)
Uc = np.array([tab["fV"], tab["fR"], tab["fS"]]).T            # (48,3)
Kk = tp[["fV", "fR", "fS"]].to_numpy(float)                  # (7,3)
S = Uc @ Wm.T                                                # (48,2000)
es = np.quantile(S, 0.8, axis=0)                             # (2000,)
Pust = ((Kk @ Wm.T) >= es).mean(axis=1)
sonuc["dirichlet"] = {kid: round(float(p), 3) for kid, p in zip(tp["kayit_id"], Pust)}
print("Dirichlet P(ust):", sonuc["dirichlet"])

json.dump(sonuc, open(CIKM / "gercek_kiyas.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
h1, h1v = sonuc["H1_M1"], sonuc["H1_fV"]
cumle = ("ayrışıyor" if (h1["p"] is not None and h1["p"] < 0.05) else "ayrışmıyor")
h1_satir = (f"- H1 (M1, n_t={h1['n_t']} vs bant-eslesmis n_k={h1['n_k']}): fark {h1['fark']:+.4f}, "
            f"p={h1['p']}, delta {h1['delta']:+.2f}.\n" if h1["p"] is not None else
            f"- H1 (M1, n_t={h1['n_t']} vs n_k={h1['n_k']}): cikarim BETIMSEL ({h1['cikarim']}); "
            f"medyan fark {h1['fark']:+.4f}, delta {h1['delta']:+.2f}.\n")
h1v["p"] = round(float(h1v["p"]), 4) if guc_yeterli else None
h1v_satir = (f"- H1 (fV): fark {h1v['fark']:+.4f}, p={h1v['p']}, delta {h1v['delta']:+.2f}.\n"
             if h1v["p"] is not None else
             f"- H1 (fV): medyan fark {h1v['fark']:+.4f}, delta {h1v['delta']:+.2f} (betimsel).\n")
open(CIKM / "K3_GERCEK_HUKMU.md", "w", encoding="utf-8").write(
 "# K3-GERCEK hukmu (kurumsal ziyaret referansli, tanisal)\n\n"
 "## Sablon cumle (§11)\n\n"
 f"> \"Tarihsel noktalar, tanımlanan fiziki ölçütler bakımından karşılaştırma alanlarından "
 f"{cumle}; bu sonuç belirtilen veri ve senaryo sınırları içinde geçerli.\"\n\n"
 f"- Birincil grup: 7 tabya (R01-R07, kurumsal ziyaret referansi; ozgun oturum dogrulanmadi).\n"
 f"{h1_satir}{h1v_satir}"
 f"- Kaleler (RK1-RK4) ayri donem: betimsel, kiyas disi.\n"
 f"- Pareto'da tabya: {sonuc['pareto_tabya'] if sonuc['pareto_tabya'] else 'yok'}.\n"
 "- Dirichlet(1,1,1)x2000 P(ust): " + ", ".join(f"{k}={v}" for k, v in sonuc["dirichlet"].items()) + ".\n"
 "\n## Sinirlar\n\n- Ziyaret koordinati ozgun platform degildir (kaynakta False).\n"
 "- Kilitbahir kumesinde fV~0: alcak-kiyi + buyuk payda etkisi; metrik tanimi geregi, tarihsel yargi degil.\n"
 "- Kontrol yoklugu yapi yoklugu degildir; <5 kontrolde yuzdelik verilmez.\n")
print("-> K3_GERCEK_HUKMU.md")
