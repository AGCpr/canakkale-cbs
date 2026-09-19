"""26 — Ozellik-bazinda ayrisma: tabya vs eslesmis kontrol (H1 detayi).

Web'deki 'hangi fiziki ozellikle?' bolumunun verisi. Eslesme kurali 12 ile ayni
(ayni taraf + kiyi uzakligi ±500 m, aday basina en fazla 6 kontrol).
Cikti: web/data/ayrisma.json [{ozellik, ad, fark, p, delta, yorum}].
"""
from pathlib import Path
import json
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]
import rasterio, geopandas as gpd
from shapely.geometry import LineString
from scipy import ndimage
from scipy.stats import mannwhitneyu
from pyproj import Transformer
from shapely.ops import transform as _t

tab = pd.read_csv(ROOT / "05_olcut_model" / "model_tablosu.csv")
ad = pd.read_csv(ROOT / "05_olcut_model" / "aday_olcut_tablosu.csv")
nok = gpd.read_file(ROOT / "05_olcut_model" / "ornek_noktalar.gpkg").set_index("nok_id")
with rasterio.open(ROOT / "05_olcut_model" / "koridor_dem.tif") as d:
    dem = d.read(1).astype(float); tr = d.transform; res = abs(tr.a)
    H, W = dem.shape
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

geo = {k: (r.geometry.x, r.geometry.y) for k, r in nok.iterrows()}
tab = tab.copy()
tab["X"] = tab["nok_id"].map(lambda k: geo[k][0])
tab["Y"] = tab["nok_id"].map(lambda k: geo[k][1])
tab["taraf"] = [taraf(x, y) for x, y in zip(tab["X"], tab["Y"])]
tab["shore_m"] = [float(shore[hucre(x, y)]) for x, y in zip(tab["X"], tab["Y"])]

PILOT = ["T01", "T03", "T04", "T05"]
tp = ad[ad["yapi_id"].isin(PILOT)].copy()
tp["taraf"] = [taraf(x, y) for x, y in zip(tp["x_32635"], tp["y_32635"])]
tp["shore_m"] = [float(shore[hucre(x, y)]) for x, y in zip(tp["x_32635"], tp["y_32635"])]

sec, kullan = [], set()
for _, a in tp.iterrows():
    el = tab[(tab["taraf"] == a["taraf"]) & (tab["shore_m"].sub(a["shore_m"]).abs() <= 500)]
    el = el[~el["nok_id"].isin(kullan)]
    al = el.sample(min(6, len(el)), random_state=20260916) if len(el) else el
    kullan.update(al["nok_id"]); sec.append(al)
kk = pd.concat(sec)

ADLAR = {"fV": "Görünürlük", "fR": "Göreli yükselti", "fS": "Eğim", "fE": "Erişim", "U_esit": "Bileşik U"}
YON = {"fV": ("yüksek", "daha geniş su görüyor"), "fR": ("yüksek", "çevresine daha hâkim"),
       "fS": ("düşük", "daha yatık zeminde"), "fE": ("yüksek", "kıyıya daha yakın"),
       "U_esit": ("yüksek", "ölçütler toplamında önde")}
out = []
for kol, ad_ in ADLAR.items():
    a_ = tp[kol].to_numpy(float); b_ = kk[kol].to_numpy(float)
    _, p_ = mannwhitneyu(a_, b_, alternative="two-sided")
    d_ = float((np.sum(a_[:, None] > b_) - np.sum(a_[:, None] < b_)) / (len(a_) * len(b_)))
    f_ = float(np.median(a_) - np.median(b_))
    buying = YON[kol]
    guc = "iz yok" if abs(d_) < 0.11 else "zayıf iz" if abs(d_) < 0.28 else "orta iz" if abs(d_) < 0.43 else "güçlü iz"
    if kol == "fS":  # dusuk egim beklenen yondur
        yon = buying[0] if f_ <= 0 else "ters yönde"
    else:
        yon = buying[0] if f_ >= 0 else "ters yönde"
    out.append({"ozellik": kol, "ad": ad_, "fark": round(f_, 4), "p": round(float(p_), 4),
                "delta": round(d_, 2),
                "yorum": f"Tabya medyanı {abs(f_):.3f} {yon} — {guc} (p={p_:.2g})."})
    print(out[-1])

Path(ROOT / "web" / "data" / "ayrisma.json").write_text(
    json.dumps(out, ensure_ascii=False), encoding="utf-8")
print("-> web/data/ayrisma.json")
