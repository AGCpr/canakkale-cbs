"""21 — Ogrenen model ikinci asama (dusuk-guclu gosteri): RF + lojistik, bloklu CV.

Rapor karsiligi: §04 (ikinci asama; yeterli ornek + mekânsal sinama sart [8,9]).
Veri: 48 kontrol (y=0) + 4 tabya aday (y=1); ozellik fV,fR,fS[,fE].
Blok: taraf (Avrupa/Anadolu) disarida-birak CV. Etiket: DUSUK GUCLU gosteri;
tahmin iddiasi YOK, yalnizca zincir hazirligi + degisken onem sirasi.
Cikti: 06_karsilastirma/ogrenen_model.json + onem grafigi.
"""
from pathlib import Path
import json
import numpy as np, pandas as pd, yaml

ROOT = Path(__file__).resolve().parents[1]
CIKM = ROOT / "06_karsilastirma"
P = yaml.safe_load(open(ROOT / "params" / "model.yaml", encoding="utf-8"))
rng = int(P["tekrar_uretilebilirlik"]["rastgelelik_tohumu"])

import geopandas as gpd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

tab = pd.read_csv(ROOT / "05_olcut_model" / "model_tablosu.csv")
ad = pd.read_csv(ROOT / "05_olcut_model" / "aday_olcut_tablosu.csv")
nok = gpd.read_file(ROOT / "05_olcut_model" / "ornek_noktalar.gpkg").set_index("nok_id")

FEATS = ["fV", "fR", "fS", "fE"] if "fE" in tab.columns else ["fV", "fR", "fS"]
X0 = tab[FEATS].to_numpy(float)
X1 = ad[ad["yapi_id"].isin(["T01", "T03", "T04", "T05"])][FEATS].to_numpy(float)
X = np.vstack([X0, X1]); y = np.array([0] * len(X0) + [1] * len(X1))

# taraf bloklari
from shapely.geometry import LineString
from pyproj import Transformer
# Yaka teshisi: kara bilesenleri (cizgi degil). Tohumlar: Kilitbahir=Avrupa,
# Canakkale-sehir=Anadolu. 9 noktali dogrulamada 9/9 (bkz. KARAR_KAYDI D9).
def _yaka_haritasi():
    import rasterio as _rio
    with _rio.open(ROOT / "05_olcut_model" / "koridor_dem.tif") as _d:
        _dem = _d.read(1).astype(float); _tr = _d.transform; _rs = abs(_tr.a)
    _lab, _ = __import__("scipy").ndimage.label(np.nan_to_num(_dem) > 0.5)
    _TT = Transformer.from_crs("EPSG:4326", "EPSG:32635", always_xy=True).transform
    def _hc(X, Y):
        return int((_tr.f - Y) / _rs - 0.5), int((X - _tr.c) / _rs - 0.5)
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
blok0 = [taraf(nok.loc[k, "geometry"].x, nok.loc[k, "geometry"].y) for k in tab["nok_id"]]
tp = ad[ad["yapi_id"].isin(["T01", "T03", "T04", "T05"])]
blok1 = [taraf(x, y) for x, y in zip(tp["x_32635"], tp["y_32635"])]
blok = np.array(blok0 + blok1)

out = {"orneklem": {"n0": len(X0), "n1": len(X1)}, "ozellik": FEATS,
       "bloklu_CV": {}, "uyari": "DUSUK GUCLU gosteri; tahmin iddiasi yok [8,9]"}
for b in ["Avrupa", "Anadolu"]:
    te = blok == b; trn = ~te
    if y[trn].sum() == 0 or y[te].sum() == 0:
        out["bloklu_CV"][b] = {"not": "blokta tek sinif; AUC hesaplanamaz"}
        continue
    rf = RandomForestClassifier(200, random_state=rng, class_weight="balanced").fit(X[trn], y[trn])
    lr = LogisticRegression(max_iter=2000, class_weight="balanced").fit(X[trn], y[trn])
    out["bloklu_CV"][b] = {"AUC_RF": round(float(roc_auc_score(y[te], rf.predict_proba(X[te])[:, 1])), 3),
                           "AUC_logit": round(float(roc_auc_score(y[te], lr.predict_proba(X[te])[:, 1])), 3)}
full = RandomForestClassifier(400, random_state=rng, class_weight="balanced").fit(X, y)
out["degisken_onem_RF"] = {k: round(float(v), 3) for k, v in zip(FEATS, full.feature_importances_)}
# LOO mumkun degil (n1=4); 2-katmanli tabakali CV genel AUC tahmini (yine dusuk guclu)
from sklearn.model_selection import cross_val_predict, StratifiedKFold
try:
    p_cv = cross_val_predict(LogisticRegression(max_iter=2000, class_weight="balanced"),
                             X, y, cv=StratifiedKFold(2, shuffle=True, random_state=rng),
                             method="predict_proba")[:, 1]
    out["CV2_AUC_logit"] = round(float(roc_auc_score(y, p_cv)), 3)
except Exception as e:
    out["CV2_AUC_logit"] = f"hesaplanamadi: {e}"
json.dump(out, open(CIKM / "ogrenen_model.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)

import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(6, 3.5))
ax.barh(FEATS, [out["degisken_onem_RF"][k] for k in FEATS])
ax.set_title("RF degisken onemi (dusuk-guclu pilot)")
fig.tight_layout(); fig.savefig(CIKM / "ogrenen_onem.png", dpi=130)
print(json.dumps(out, indent=1, ensure_ascii=False))
