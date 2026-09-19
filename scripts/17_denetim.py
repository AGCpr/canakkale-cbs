"""17 — Bagimsiz denetim: uretim kodundan AYRI yeniden-hesapla dogrula.

Kapsam: grid tutarliligi, tablo formulleri, OWA/kararlilik/H-istatistikleri,
maske mantigi, belge-sayi tutarliligi. Cikti: logs/denetim.txt + PASS/FAIL.
Cikis kodu: hata varsa 1.
"""
from pathlib import Path
import numpy as np, pandas as pd, yaml
ROOT = Path(__file__).resolve().parents[1]
P = yaml.safe_load(open(ROOT / "params" / "model.yaml", encoding="utf-8"))
sonuc = []
def kayit(ad, ok, detay=""):
    sonuc.append((ad, bool(ok), str(detay)))
    print(("PASS " if ok else "FAIL ") + ad + (f" :: {detay}" if detay else ""))

import rasterio
# A. Grid tutarliligi
koridor = ["05_olcut_model/egim_derece.tif", "05_olcut_model/r_1000m.tif",
           "05_olcut_model/fR.tif", "05_olcut_model/fS.tif",
           "05_olcut_model/U_raster_esit.tif", "05_olcut_model/kumulatif_gorus.tif",
           "05_olcut_model/koridor_dem.tif"]
meta0 = None
for f in koridor:
    try:
        with rasterio.open(ROOT / f) as d:
            m = (d.crs.to_epsg(), round(abs(d.res[0]), 6), d.height, d.width, str(d.transform))
            if meta0 is None: meta0 = m
            kayit(f"A-grid:{Path(f).name}", m == meta0 and m[0] == 32635 and m[1] == 30.0, str(m[2:]))
    except Exception as e:
        kayit(f"A-grid:{f}", False, str(e))
with rasterio.open(ROOT / "03_veri/islenmis/dem_30m_32635.tif") as d:
    kayit("A-DEM:crs+cozum", d.crs.to_epsg() == 32635 and abs(d.res[0] - 30) < 1e-9,
          f"{d.crs.to_epsg()} {d.res} {d.width}x{d.height}")

# B. olcut_tablosu (48+4; olcek ilk 48'den donduruldu)
t = pd.read_csv(ROOT / "05_olcut_model" / "olcut_tablosu.csv")
kayit("B-olcut:satir", len(t) == 52, f"n={len(t)}")
kayit("B-olcut:aralik", bool(((t[["fV", "fR", "fS"]] >= 0) & (t[["fV", "fR", "fS"]] <= 1)).all().all()))
v = t.loc[~t["nok_id"].str.startswith("A"), "R"].to_numpy(float)
lo, hi = np.percentile(v, [5, 95])
fr = np.clip((t["R"].to_numpy(float) - lo) / (hi - lo), 0, 1)
kayit("B-olcut:fR-winsor", np.allclose(fr, t["fR"].to_numpy(float), atol=6e-5), f"p5={lo:.2f} p95={hi:.2f}")
es = P["egim"]["esik"]
fs = np.clip(1 - (t["egim"].to_numpy(float) - es["duz"]) / (es["dik"] - es["duz"]), 0, 1)
kayit("B-olcut:fS", np.allclose(fs, t["fS"].to_numpy(float), atol=5e-5))

# C. model_tablosu (U: params agirliklariyla; tolerans 4-ondalik yuvarlama)
m1 = pd.read_csv(ROOT / "05_olcut_model/model_tablosu.csv")
we = P["agirliklar"]["esit"]
u = we["wV"] * m1["fV"] + we["wR"] * m1["fR"] + we["wS"] * m1["fS"]
kayit("C-model:U_esit", np.allclose(u, m1["U_esit"], atol=6e-5))
kayit("C-model:M0/M1", bool((m1["M0"] == m1["fV"]).all() and (m1["M1_esit"] == m1["U_esit"]).all()))
w2 = P["agirliklar"]["uzman_gorus_agirlikli"]
uu = w2["wV"] * m1["fV"] + w2["wR"] * m1["fR"] + w2["wS"] * m1["fS"]
kayit("C-model:U_uzman", np.allclose(uu, m1["U_uzman_gorus_agirlikli"], atol=5e-5))

# D. aday tablosu
a = pd.read_csv(ROOT / "05_olcut_model/aday_olcut_tablosu.csv")
kayit("D-aday:satir", len(a) == 8, f"n={len(a)}")
ua = we["wV"] * a["fV"] + we["wR"] * a["fR"] + we["wS"] * a["fS"]
kayit("D-aday:U_esit", np.allclose(ua, a["U_esit"], atol=6e-5))
kayit("D-aday:aralik", bool(((a[["fV", "fR", "fS", "U_esit"]] >= 0) & (a[["fV", "fR", "fS", "U_esit"]] <= 1)).all().all()))
kayit("D-aday:bayrak", set(a["konum_guven"]) == {"dusuk"} and bool((a["hata_yaricapi_m"] == 1000).all()))

# E. OWA
o = pd.read_csv(ROOT / "05_olcut_model/owa_tablosu.csv")
F = o[["fV", "fR", "fS"]].to_numpy() if set(["fV", "fR", "fS"]) <= set(o.columns) else None
if F is None:
    tt = pd.read_csv(ROOT / "05_olcut_model/model_tablosu.csv")
    aa = pd.read_csv(ROOT / "05_olcut_model/aday_olcut_tablosu.csv")
    F = pd.concat([tt[["fV", "fR", "fS"]], aa[["fV", "fR", "fS"]]], ignore_index=True).to_numpy()
kayit("E-OWA:OR/AND/notr", bool(np.allclose(o["OWA_OR"], F.max(1), atol=5e-5)
    and np.allclose(o["OWA_AND"], F.min(1), atol=5e-5)
    and np.allclose(o["OWA_notr"], F.mean(1), atol=5e-5)))
from scipy.stats import spearmanr
for k, bek in [("OWA_OR", 0.507), ("OWA_AND", 0.373)]:
    rho, _ = spearmanr(o["M1_esit"], o[k])
    kayit(f"E-OWA:rho-{k}", abs(rho - bek) < 0.005, f"rho={rho:.3f}")

# F. kararlilik yeniden-hesap
s = pd.read_csv(ROOT / "07_belirsizlik/senaryo_tablosu.csv")
k = pd.read_csv(ROOT / "07_belirsizlik/kararlilik.csv")
ust = s.apply(lambda c: c >= c.quantile(0.8))
kayit("F-kararlilik", np.allclose(ust.mean(axis=1).round(3), k["kararlilik"], atol=1e-9))

# G. H-istatistikleri (bagimsiz)
from scipy.stats import mannwhitneyu
tp = pd.read_csv(ROOT / "06_karsilastirma/pilot_tabya_degerleri.csv")
kk = pd.read_csv(ROOT / "06_karsilastirma/pilot_kontrol_degerleri.csv")
hc = pd.read_csv(ROOT / "06_karsilastirma/karsilastirma_tablosu__PILOT_ADAY.csv")
for et, kol in [("H1_tabya_M1_esit", "M1_esit"), ("H1_tabya_fV", "fV")]:
    r = hc[hc["etiket"] == et].iloc[0]
    u_, p_ = mannwhitneyu(tp[kol], kk[kol], alternative="two-sided")
    f_ = float(np.median(tp[kol]) - np.median(kk[kol]))
    kayit(f"G-{et}", abs(p_ - r['p']) / max(abs(float(r['p'])), 1e-3) < 0.02 and abs(f_ - r['medyan_fark']) < 1e-4,
          f"p={p_:.4g} fark={f_:+.4f}")

# H. maske mantigi
with rasterio.open(ROOT / "05_olcut_model/koridor_dem.tif") as d:
    dem = d.read(1).astype(float)
fin = np.isfinite(dem)
kayit("H-maske:sonlu-oran", fin.mean() > 0.9, f"{fin.mean():.3f}")
import geopandas as gpd
sg = gpd.read_file(ROOT / "03_veri/islenmis/su_hedef.gpkg")
pay = (sg.geometry.area / sg.geometry.area.sum())
kayit("H-su_hedef:vektor", bool((pay.max() > 0.99) and (pay[pay < 0.01].sum() < 0.001)),
      f"{len(sg)} poligon, baskin pay={pay.max():.4f}")

# I. belge-sayi tutarliligi
def icerir(yol, *frag):
    txt = (ROOT / yol).read_text(encoding="utf-8")
    return all(f in txt for f in frag)
kayit("I-PILOT_RAPOR", icerir("04_pilot_kalite/PILOT_RAPOR.md", "48", "0,0018", "0,1404", "25/48"))
kayit("I-K3_HUKMU", icerir("06_karsilastirma/K3_PILOT_HUKMU.md", "ayrışmıyor", "-0.0040", "0.507")
      and icerir("06_karsilastirma/K3_GERCEK_HUKMU.md", "BETIMSEL", "Pareto"))
kayit("I-NIHAI", icerir("09_teslim/NIHAI_RAPOR.md", "104", "ayrışmıyor", "0.51", "0.37"))

# J. spot gorus (ortak maske; deterministik -> esitlik beklenir)
import subprocess as _sp, tempfile as _tf, os as _os
try:
    with rasterio.open(ROOT / "05_olcut_model" / "su_hedef_mask.tif") as _d:
        _su = _d.read(1) == 1
    with rasterio.open(ROOT / "05_olcut_model" / "koridor_dem.tif") as _d:
        _tr = _d.transform; _rs = abs(_tr.a); _H, _W = _d.height, _d.width
    _QD = Path(r"C:\Program Files\QGIS 4.2.2\bin\gdal_viewshed.exe")
    def _fV(X, Y):
        with _tf.TemporaryDirectory() as _td:
            _o = _os.path.join(_td, "s.tif")
            _sp.run([str(_QD), "-ox", str(X), "-oy", str(Y), "-oz", "4", "-tz", "0",
                     "-md", "15000", "-cc", "0.13", "-iv", "0",
                     str(ROOT / "05_olcut_model" / "koridor_dem.tif"), _o],
                    capture_output=True, timeout=180, check=True)
            with rasterio.open(_o) as _dd:
                _vv = _dd.read(1); _vt = _dd.transform
            _wr, _wc = np.where(_su)
            _Xs = _tr.c + (_wc + 0.5) * _rs; _Ys = _tr.f - (_wr + 0.5) * _rs
            _inv = ~_vt
            _co = (_inv.a * _Xs + _inv.b * _Ys + _inv.c).astype(int)
            _ro = (_inv.d * _Xs + _inv.e * _Ys + _inv.f).astype(int)
            _ok = (_ro >= 0) & (_ro < _vv.shape[0]) & (_co >= 0) & (_co < _vv.shape[1])
            return float((_vv[_ro[_ok], _co[_ok]] == 255).sum()) / max(int(_su.sum()), 1)
    import geopandas as _gg
    _g = _gg.read_file(ROOT / "05_olcut_model" / "ornek_noktalar.gpkg").set_index("nok_id")
    _kk = t.loc[t["fV"].idxmax()]
    _pt = _g.loc[_kk["nok_id"], "geometry"]
    _v1 = _fV(float(_pt.x), float(_pt.y))
    kayit("J-spot:kontrol", abs(_v1 - _kk["fV"]) < 6e-5, f"tablo={_kk['fV']:.4f} spot={_v1:.4f}")
    _r5 = a[a["yapi_id"] == "T05"].iloc[0]
    _v2 = _fV(float(_r5["x_32635"]), float(_r5["y_32635"]))
    kayit("J-spot:aday-T05", abs(_v2 - _r5["fV"]) < 6e-5, f"tablo={_r5['fV']:.4f} spot={_v2:.4f}")
except Exception as e:
    kayit("J-spot", False, str(e))

# K. yeni parcalar (100x genisleme)
import json as _js, re as _re
try:
    _ahp = open(ROOT / "logs" / "ahp.txt", encoding="utf-8").read()
    _cr = float(_re.search(r"CR=([0-9.]+)", _ahp).group(1))
    kayit("K-AHP:CR", _cr <= 0.10, f"CR={_cr}")
except Exception as e:
    kayit("K-AHP:CR", False, str(e))
_WE = P["erisim"]["agirliklar_M2"]
_m2 = _WE["wV"] * m1["fV"] + _WE["wR"] * m1["fR"] + _WE["wS"] * m1["fS"] + _WE["wE"] * m1["fE"]
kayit("K-M2:model", "M2" in m1.columns and bool(np.allclose(_m2, m1["M2"], atol=6e-5)))
_m2a = _WE["wV"] * a["fV"] + _WE["wR"] * a["fR"] + _WE["wS"] * a["fS"] + _WE["wE"] * a["fE"]
kayit("K-M2:aday", bool(np.allclose(_m2a, a["M2"], atol=6e-5)))
try:
    _og = _js.load(open(ROOT / "06_karsilastirma" / "ogrenen_model.json", encoding="utf-8"))
    kayit("K-ogrenen", "CV2_AUC_logit" in _og and "uyari" in _og, str(_og.get("CV2_AUC_logit")))
except Exception as e:
    kayit("K-ogrenen", False, str(e))
try:
    _dz = pd.read_csv(ROOT / "07_belirsizlik" / "deniz_seviyesi.csv")
    kayit("K-denizsv", set(["fV_t-1", "fV_t+1"]).issubset(_dz.columns) and len(_dz) == 8)
except Exception as e:
    kayit("K-denizsv", False, str(e))
kayit("K-web", (ROOT / "09_teslim" / "web_atlas.html").exists()
      and (ROOT / "09_teslim" / "_u.png").exists()
      and (ROOT / "09_teslim" / "yonetici_raporu.html").exists())
kayit("K-dejenere-notu", icerir("07_belirsizlik/SENARYO_MATRISI.md", "dejenere"))

# L. web arayuzu (amiral gemisi)
import subprocess as _sp2
try:
    _jm = _js.load(open(ROOT / "web" / "data" / "meta.json", encoding="utf-8"))
    _r = hc[hc["etiket"] == "H1_tabya_M1_esit"].iloc[0]
    kayit("L-web:meta-H1", abs(_jm["h1"]["fark"] - _r["medyan_fark"]) < 1e-9
          and _jm["aday_sayisi"] == 8 and _jm["kontrol_sayisi"] == 52,
          f"fark={_jm['h1']['fark']} n={_jm['kontrol_sayisi']}+{_jm['aday_sayisi']}")
except Exception as e:
    kayit("L-web:meta-H1", False, str(e))
try:
    _p = _sp2.run(["node", "--check", str(ROOT / "web" / "app.js")],
                  capture_output=True, text=True, timeout=60)
    kayit("L-web:js-syntax", _p.returncode == 0, (_p.stderr or "").strip()[:120])
except Exception as e:
    kayit("L-web:js-syntax", False, str(e))
try:
    _ay = _js.load(open(ROOT / "web" / "data" / "ayrisma.json", encoding="utf-8"))
    kayit("L-web:ayrisma", len(_ay) == 5 and all(
        set(["ozellik", "fark", "p", "delta", "yorum"]) <= set(x) for x in _ay),
        f"{len(_ay)} olcut")
except Exception as e:
    kayit("L-web:ayrisma", False, str(e))
try:
    _h = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
    _c = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")
    kayit("L-web:html", all(x in _h for x in ["leaflet", 'id="harita"', 'id="sonuclar"',
          'id="veri"', "skip", "role=", "aria-"]) and "../" not in _h and all(x in _c for x in [
          "prefers-reduced-motion", ":focus-visible", "44px"]))
except Exception as e:
    kayit("L-web:html", False, str(e))

try:
    _mc = pd.read_csv(ROOT / "07_belirsizlik" / "mc_aday.csv")
    _cq = pd.read_csv(ROOT / "02_envanter" / "capraz_kaynak.csv")
    kayit("M-mc+capraz", len(_mc) == 8 and set(["U_ort", "P_ust"]) <= set(_mc.columns)
          and set(_cq["capraz_guven_yeni"]) <= {"orta", "dusuk"},
          f"mc={len(_mc)} satir")
except Exception as e:
    kayit("M-mc+capraz", False, str(e))

n_fail = sum(1 for _, ok, _ in sonuc if not ok)
(ROOT / "logs" / "denetim.txt").write_text(
 f"# Denetim {__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()}\n"
 + "\n".join(f"{'PASS' if ok else 'FAIL'} {ad} {d}" for ad, ok, d in sonuc)
 + f"\n\nSONUC: {len(sonuc)-n_fail}/{len(sonuc)} PASS\n", encoding="utf-8")
print(f"\nSONUC: {len(sonuc)-n_fail}/{len(sonuc)} PASS")
raise SystemExit(1 if n_fail else 0)
