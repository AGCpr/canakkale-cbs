"""09 — Teslim paketi: GPKG + proje dosyasi listesi + sha256 + kontrol.

Rapor karsiligi: §11 cikti 05. Cikti: 09_teslim/ (zip + MANIFEST.sha256).
"""
from pathlib import Path
import geopandas as gpd, hashlib, zipfile, datetime
ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "09_teslim"
import shutil

# GPKG birlestir
kat = []
for p, ad in [(ROOT/"05_olcut_model/ornek_noktalar.gpkg", "ornek_noktalar"),
              (ROOT/"05_olcut_model/aday_noktalar.gpkg", "aday_noktalar_taslak"),
              (ROOT/"03_veri/islenmis/koridor.gpkg", "koridor"),
              (ROOT/"03_veri/islenmis/su_hedef.gpkg", "su_hedef")]:
    if p.exists():
        try:
            g = gpd.read_file(p)
            kat.append((ad, g))
        except Exception as e:
            print(f"atlandi {p}: {e}")
gpkg = T / "canakkale_cbs.gpkg"
if (T / "canakkale_cbs.gpkg").exists():
    (T / "canakkale_cbs.gpkg").unlink()
for ad, g in kat:
    g.to_file(gpkg, layer=ad, driver="GPKG")
(T / "KULLANIM_NOTU.md").write_text(
 "# Kullanim notu (kisa)\n\n1. QGIS 4.2.2'de `canakkale_cbs.gpkg` + `../03_veri/islenmis/dem_30m_32635.tif` + `../05_olcut_model/U_raster_*.tif` acilir.\n"
 "2. CRS: EPSG:32635. Parametreler: `../params/model.yaml` (surum + tohum icerir).\n"
 "3. Gorus protokolu: `../05_olcut_model/GORUS_PROTOKOL.txt`.\n"
 "4. Bastan calistirma: README 'Hizli baslat' (loglar `../logs/`).\n"
 f"5. Paket tarihi (UTC): {datetime.datetime.utcnow().isoformat()}Z.\n", encoding="utf-8")
files = []
for pat in [(ROOT / "params").glob("*"), (ROOT / "05_olcut_model").glob("*"),
            (ROOT / "03_veri" / "islenmis").glob("*"), T.glob("*.png"), T.glob("*.md"),
            (ROOT / "02_envanter").glob("*.csv"), (ROOT / "02_envanter").glob("*.md"),
            (ROOT / "06_karsilastirma").glob("*"), (ROOT / "07_belirsizlik").glob("*"),
            (ROOT / "04_pilot_kalite").glob("*.md"), (ROOT / "qgis").glob("*.qgz"),
            (ROOT / "qgis").glob("*.md"), (ROOT / "logs").glob("*.txt"),
            (ROOT / "web").glob("*.html"), (ROOT / "web").glob("*.css"),
            (ROOT / "web").glob("*.js"), (ROOT / "web" / "data").glob("*.json"),
            (ROOT / "web" / "img").glob("*.png"), (ROOT / "web" / "dosya").glob("*"),
            (ROOT / "web").glob("_headers")]:
    files += [p for p in pat if p.is_file()]
files += [ROOT / "README.md", ROOT / "00_yonetim" / "KARAR_KAYDI.md",
          ROOT / "00_yonetim" / "IS_PLANI.md", ROOT / "requirements.txt"]
files = sorted({str(p): p for p in files if p.is_file() and p.suffix != ".zip"}.values(),
               key=lambda p: str(p))
files = [p for p in files if "ham" not in p.parts and p.stat().st_size < 150e6]
man = []
for p in files:
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    man.append(f"{h}  {p.relative_to(ROOT)}")
(T / "MANIFEST.sha256").write_text("\n".join(man), encoding="utf-8")
z = T / "cbs_teslim_paketi.zip"
with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zz:
    for p in files + [gpkg]:
        if p.exists(): zz.write(p, p.relative_to(ROOT))
print(f"-> {z} ({len(man)} dosya, sha256 manifestli)")
