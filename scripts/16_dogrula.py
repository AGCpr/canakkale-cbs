"""16 — Teslim dogrulama: dosya varligi + MANIFEST sha256 + CRS/cozum + parametre kisitlari.

Cikis kodu 0 = teslim gecerli. Rapor: logs/dogrulama.txt
"""
from pathlib import Path
import hashlib, sys, zipfile
import xml.etree.ElementTree as ET
import yaml

ROOT = Path(__file__).resolve().parents[1]
hatalar, uyarilar = [], []

def bekle(yol, etiket):
    if not Path(ROOT / yol).exists():
        hatalar.append(f"EKSIK {etiket}: {yol}")

ZORUNLU = [
 ("README.md", "benim-oku"), ("00_yonetim/KARAR_KAYDI.md", "karar"),
 ("params/model.yaml", "parametre"), ("02_envanter/envanter.csv", "envanter"),
 ("02_envanter/aday_noktalar_taslak.csv", "aday"),
 ("03_veri/islenmis/dem_30m_32635.tif", "DEM"), ("03_veri/islenmis/su_hedef.gpkg", "su"),
 ("05_olcut_model/olcut_tablosu.csv", "olcut"), ("05_olcut_model/model_tablosu.csv", "model"),
 ("05_olcut_model/aday_olcut_tablosu.csv", "aday-olcut"),
 ("05_olcut_model/su_hedef_mask.tif", "payda-maske"),
 ("05_olcut_model/AHP_NOTU.md", "AHP"), ("05_olcut_model/ERISIM_NOTU.md", "erisim"),
 ("05_olcut_model/OWA_NOTU.md", "OWA"),
 ("05_olcut_model/kumulatif_gorus.tif", "kumulatif"), ("05_olcut_model/owa_tablosu.csv", "OWA"),
 ("05_olcut_model/gorsel_ag.csv", "gorsel-ag"),
 ("06_karsilastirma/ogrenen_model.json", "ogrenen"),
 ("07_belirsizlik/deniz_seviyesi.csv", "deniz-sv"),
 ("09_teslim/web_atlas.html", "web"), ("09_teslim/yonetici_raporu.html", "yrapor"),
 ("logs/ahp.txt", "ahp-log"),
 ("web/index.html", "web-index"), ("web/app.js", "web-js"),
 ("web/data/meta.json", "web-meta"), ("web/data/ayrisma.json", "web-ayrisma"),
 ("web/img/u_esit.png", "web-png"), ("web/_headers", "web-headers"),
 ("web/dosya/canakkale_cbs.gpkg", "web-gpkg"), ("web/dosya/canakkale_vrs.qgz", "web-qgz"),
 ("02_envanter/capraz_kaynak.csv", "capraz"), ("07_belirsizlik/mc_aday.csv", "mc"),
 ("09_teslim/bulgular.pdf", "pdf"), ("09_teslim/sonuc-tablolari.xlsx", "xlsx"),
 ("06_karsilastirma/karsilastirma_tablosu__PILOT_ADAY.csv", "H-karsilastirma"),
 ("06_karsilastirma/K3_PILOT_HUKMU.md", "K3-hukum"),
 ("07_belirsizlik/kararlilik.csv", "kararlilik"),
 ("04_pilot_kalite/PILOT_RAPOR.md", "K2-rapor"),
 ("09_teslim/canakkale_cbs.gpkg", "GPKG"), ("09_teslim/MANIFEST.sha256", "manifest"),
 ("09_teslim/cbs_teslim_paketi.zip", "zip"), ("qgis/canakkale_vrs.qgz", "qgz"),
]
for y, e in ZORUNLU:
    bekle(y, e)

# MANIFEST kontrolu (zip + gpkg + ana cikti; ham DEM ve zip kendisi haric)
man = (ROOT / "09_teslim" / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines()
okn, kotu = 0, []
for sat in man:
    h, _, yol = sat.partition("  ")
    p = ROOT / yol.strip()
    if not p.exists():
        kotu.append(f"YOK:{yol}"); continue
    if p.stat().st_size > 200e6:
        continue
    if hashlib.sha256(p.read_bytes()).hexdigest() == h:
        okn += 1
    else:
        kotu.append(f"BOZUK:{yol}")
if kotu:
    hatalar += kotu

# qgz butunluk
try:
    with zipfile.ZipFile(ROOT / "qgis" / "canakkale_vrs.qgz") as z:
        ad = z.namelist()
        assert len(ad) == 1 and ad[0].endswith(".qgs")
        kok = ET.fromstring(z.read(ad[0]))
        kat = kok.findall(".//maplayer")
        assert len(kat) == 12, f"katman sayisi {len(kat)}"
except Exception as e:
    hatalar.append(f"QGZ: {e}")

# raster CRS/cozum
try:
    import rasterio
    with rasterio.open(ROOT / "03_veri" / "islenmis" / "dem_30m_32635.tif") as d:
        assert d.crs.to_epsg() == 32635, d.crs
        assert abs(d.res[0] - 30) < 1e-6 and abs(d.res[1] - 30) < 1e-6, d.res
except Exception as e:
    hatalar.append(f"DEM grid: {e}")

# parametre kisitlari
P = yaml.safe_load(open(ROOT / "params" / "model.yaml", encoding="utf-8"))
for ad, w in P["agirliklar"].items():
    assert abs(sum(w.values()) - 1) < 1e-6, ad
    assert all(v >= 0 for v in w.values()), ad
assert P["ortak_cozunurluk_m"] == 30 and P.get("cozum_5m_yasak")

# qgz katman baglantilari
try:
    import zipfile as _zf
    import xml.etree.ElementTree as _ET
    with _zf.ZipFile(ROOT / "qgis" / "canakkale_vrs.qgz") as _z:
        _ad = _z.namelist()
        _kok = _ET.fromstring(_z.read(_ad[0]))
        _eksik = []
        for _ds in _kok.findall(".//datasource"):
            _yol = (_ds.text or "").split("|")[0]
            if _yol and not _yol.startswith("http") and not (ROOT / "qgis" / _yol).exists():
                _eksik.append(_yol)
        if _eksik:
            hatalar.append(f"QGZ eksik katman: {_eksik[:5]}")
except Exception as e:
    hatalar.append(f"QGZ okuma: {e}")

rapor = ["# Dogrulama", f"- zorunlu dosya: {len(ZORUNLU)-len([h for h in hatalar if h.startswith('EKSIK')])}/{len(ZORUNLU)}",
 f"- manifest OK: {okn}", f"- hata: {len(hatalar)}"]
rapor += [f"  ! {h}" for h in hatalar]
(ROOT / "logs" / "dogrulama.txt").write_text("\n".join(rapor), encoding="utf-8")
print("\n".join(rapor))
sys.exit(1 if hatalar else 0)
