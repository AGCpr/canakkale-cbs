"""10 — OSM aday nokta derleme: envanter KIRLETILMEZ.

Rapor karsiligi: §03 (konum hata cevresi), [18] oncelikli kaynak.
Bu betik ayri bir `aday_noktalar_taslak.csv/gpkg` uretir; `02_envanter/envanter.csv`
koordinatlari BOS kalir. Tum adaylar konum_guven=dusuk + hata 1000 m + kaynak=OSM
Nominatim (dogrulanmadi) bayragi tasir. Tarihsel yapi konumu iddiasi DEGILDIR;
yalnizca yontem zincirini gosteren pilot girdisidir.
"""
from pathlib import Path
import time
import requests
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "02_envanter"
LOG = ROOT / "logs"; LOG.mkdir(exist_ok=True)

SORGULAR = [
    ("T01", "Namazgah Tabyasi", "Namazgah Tabyası, Çanakkale"),
    ("T02", "Hamidiye Tabyasi (Avrupa)", "Hamidiye Tabyası, Eceabat"),
    ("T03", "Mecidiye Tabyasi", "Mecidiye Tabyası, Çanakkale"),
    ("T04", "Anadolu Hamidiyesi", "Anadolu Hamidiye Tabyası, Çanakkale"),
    ("T05", "Orhaniye Tabyasi", "Orhaniye Tabyası, Çanakkale"),
    ("T06", "Kumkale Kalesi", "Kumkale Kalesi, Çanakkale"),
    ("T07", "Seddulbahir Kalesi", "Seddülbahir Kalesi, Eceabat"),
    ("T08", "Kilitbahir Kalesi", "Kilitbahir Kalesi, Eceabat"),
    ("T09", "Cimenlik Kalesi", "Çimenlik Kalesi, Çanakkale"),
    ("T10", "Nara Burnu", "Nara Burnu, Çanakkale"),
]
BBOX = "25.9,39.9,27.1,40.7"  # viewbox: sol,ust,sag,alt (lon,lat)
UA = {"User-Agent": "cbs-pilot-arastirma/1.0 (akademik yontem pilotu; iletisim: yerel)"}

sat, ham_log = [], []
for yid, ad, q in SORGULAR:
    url = "https://nominatim.openstreetmap.org/search"
    par = {"q": q, "format": "json", "limit": 3, "viewbox": BBOX, "bounded": 1,
           "countrycodes": "tr", "addressdetails": 1}
    try:
        r = requests.get(url, params=par, headers=UA, timeout=30)
        r.raise_for_status()
        js = r.json()
    except Exception as e:
        js = []
        ham_log.append(f"{yid} {ad}: SORGU_HATASI {e}")
    if js:
        ilk = js[0]
        sat.append({"yapi_id": yid, "ad_standart": ad, "sorgu": q,
            "lon_wgs84": float(ilk["lon"]), "lat_wgs84": float(ilk["lat"]),
            "osm_display": ilk.get("display_name", "")[:160],
            "osm_class": ilk.get("class", ""), "osm_type": ilk.get("type", ""),
            "konum_guven": "dusuk", "hata_yaricapi_m": 1000,
            "kaynak": "OSM Nominatim TASLAK (dogrulanmadi; [18]+[1,2] gerekli)",
            "durum": "aday_taslak"})
        ham_log.append(f"{yid} {ad}: BULUNDU {ilk['lat']},{ilk['lon']} ({ilk.get('class')}/{ilk.get('type')}) +{len(js)-1} alternatif")
    else:
        sat.append({"yapi_id": yid, "ad_standart": ad, "sorgu": q,
            "lon_wgs84": "", "lat_wgs84": "", "osm_display": "", "osm_class": "",
            "osm_type": "", "konum_guven": "dusuk", "hata_yaricapi_m": 1000,
            "kaynak": "BULUNAMADI (Nominatim); [18]+donem haritasi gerekli",
            "durum": "aday_yok"})
        ham_log.append(f"{yid} {ad}: BULUNAMADI")
    time.sleep(1.1)  # Nominatim kullanim kurali

df = pd.DataFrame(sat)
hedef_csv = OUT / "aday_noktalar_taslak.csv"
if hedef_csv.exists():
    # sonraki adimlarin ekledigi sutunlari koru (18/28)
    eski = pd.read_csv(hedef_csv)
    ekstra = [c for c in eski.columns if c not in df.columns]
    if ekstra:
        df = df.merge(eski[["yapi_id"] + ekstra], on="yapi_id", how="left")
df.to_csv(hedef_csv, index=False)
not_yolu = OUT / "ADAY_NOTU.md"
baslik = ("# Aday nokta notu (otomatik)\n\n" + "\n".join(f"- {l}" for l in ham_log)
 + "\n\nUYARI: Bu dosya tarihsel kanit degildir. Gercek envanter koordinatlari "
   "[18] kurumsal envanter + donem haritalari + [1,2] ile doldurulacaktir. "
   "Bulunan noktalar dusuk guven + 1000 m hata ile yalnizca pilot zincir testinde kullanilir.\n")
ek = ""
if not_yolu.exists():
    eski_not = not_yolu.read_text(encoding="utf-8")
    i = eski_not.find("\n## ")
    if i >= 0:
        ek = eski_not[i:]  # sonraki adimlarin bolumleri korunur
not_yolu.write_text(baslik + ek, encoding="utf-8")
print("\n".join(ham_log))
print(f"-> aday_noktalar_taslak.csv ({(df.lon_wgs84!='').sum()}/{len(df)} bulundu)")
