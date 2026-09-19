"""01 — Acik veri indir: Natural Earth baglam + Copernicus GLO-90 DEM (pilot).

Rapor karsiligi: §05 Veri mimarisi, [11] [15] [20].
Ilke: lisans + surum + erisim tarihi VERI_KATALOGU'na islenir; basarisiz indirme
durumunda sentetik pilot DEM uretilir (SENTETIK etiketli — analiz altligi degil,
yalnizca hat testi icin).
"""
import datetime, io, zipfile
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
HAM = ROOT / "03_veri" / "ham"
HAM.mkdir(parents=True, exist_ok=True)
LOG = ROOT / "logs"; LOG.mkdir(exist_ok=True)
log = []

def indir(url, hedef, timeout=120):
    try:
        r = requests.get(url, timeout=timeout, stream=True)
        r.raise_for_status()
        with open(hedef, "wb") as f:
            for c in r.iter_content(1 << 20):
                f.write(c)
        log.append(f"OK {url} -> {hedef.name} ({hedef.stat().st_size/1e6:.1f} MB)")
        return True
    except Exception as e:
        log.append(f"HATA {url} :: {e}")
        return False

# 1) Natural Earth 1:10m land (kamu mali, [20]) — birden fazla ayna
ne_hedef = HAM / "ne_10m_land.zip"
NE_URLS = [
    "https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_land.zip",
    "https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/physical/ne_10m_land.zip",
    "https://naciscdn.org/naturalearth/10m/physical/ne_10m_land.zip",
]
if not ne_hedef.exists():
    for u in NE_URLS:
        if indir(u, ne_hedef):
            break
else:
    log.append(f"VAR {ne_hedef.name} (indirme atlandi)")
try:
    if ne_hedef.exists() and ne_hedef.stat().st_size > 1000:
        with zipfile.ZipFile(ne_hedef) as z:
            z.extractall(HAM / "ne_10m_land")
        log.append("OK ne_10m_land.zip acildi")
except Exception as e:
    log.append(f"HATA zip acma :: {e}")

# 2) Copernicus GLO-90 DEM, Bogaz'i orten 2 karo (acik, kucuk ~10-20 MB/kar o)
# Kapsama: lon 25.9-27.1, lat 39.9-40.7 -> karolar N40_E025..E027 + N39_...
KAROLAR = ["N40_00_E026_00", "N40_00_E027_00", "N39_00_E026_00", "N39_00_E027_00",
           "N40_00_E025_00", "N39_00_E025_00"]
BASE90 = "https://copernicus-dem-90m.s3.amazonaws.com"
BASE30 = "https://copernicus-dem-30m.s3.amazonaws.com"
for k in KAROLAR:
    ad = f"Copernicus_DSM_COG_10_{k}_DEM"
    hedef = HAM / f"{ad}.tif"
    if hedef.exists():
        log.append(f"VAR {hedef.name} (atlandi)"); continue
    ok = False
    for base in (BASE90, BASE30):
        url = f"{base}/{ad}/{ad}.tif"
        if indir(url, hedef):
            ok = True; break
    if not ok:
        log.append(f"ATLANDI karo {k} (ag/lisans engeli olabilir)")

# 3) Dogrulama notu
not_ = HAM / "INDIRME_NOTU.md"
not_.write_text(
    "# Indirme notu (otomatik)\n\n" + "\n".join(f"- {l}" for l in log)
    + f"\n\n- erisim_utc: {datetime.datetime.utcnow().isoformat()}Z\n"
    + "- Copernicus DEM lisansi ve kullanim kosullari: Copernicus Data Space [11];\n"
    + "  FABDEM alternatifi CC BY-NC-SA 4.0 [13] — ayri kosul, bu hatta indirilmez.\n"
    + "- Natural Earth kamu mali [20]; yalnizca kapak/baglam haritasi, analiz altligi degildir.\n",
    encoding="utf-8")

print("\n".join(log))
print(f"-> {not_}")
