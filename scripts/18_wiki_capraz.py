"""18 — Wiki capraz kontrol: OSM taslak noktalar Vikipedi koordinatlariyla karsilastirilir.

Kaynak: MediaWiki API (tr.wikipedia.org, acik). Eslesme kurali (on-kayit):
dist(OSM, Wiki) <= 500 m -> capraz_guven=orta, hata 500 m; aksi halde dusuk/1000 m.
Envanter koordinatlari HALA bos; bu yalnizca aday guven bayragini gunceller.
Cikti: aday_noktalar_taslak.csv'ye wiki_* sutunlari + ADAY_NOTU.md eki.
"""
from pathlib import Path
import math
import requests
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "02_envanter" / "aday_noktalar_taslak.csv"
UA = {"User-Agent": "cbs-pilot-arastirma/1.0 (akademik yontem pilotu)"}

WIKI_AD = {
    "T01": "Namazgah Tabyası", "T02": "Hamidiye Tabyası", "T03": "Mecidiye Tabyası",
    "T04": "Anadolu Hamidiye Tabyası", "T05": "Orhaniye Tabyası",
    "T06": "Kumkale Kalesi", "T07": "Seddülbahir Kalesi", "T08": "Kilitbahir Kalesi",
    "T09": "Çimenlik Kalesi", "T10": None,
}

def wiki_koord(baslik):
    if not baslik:
        return None
    KUTU = (25.9, 39.9, 27.1, 40.7)  # proje kapsami disi sonuc = yanlis madde, REDDET
    def kutuda(lat, lon):
        return KUTU[0] <= lon <= KUTU[2] and KUTU[1] <= lat <= KUTU[3]
    try:
        r = requests.get("https://tr.wikipedia.org/w/api.php",
            params={"action": "query", "prop": "coordinates", "titles": baslik,
                    "format": "json"}, headers=UA, timeout=30).json()
        for pg in r["query"]["pages"].values():
            if "coordinates" in pg:
                c = pg["coordinates"][0]
                if kutuda(float(c["lat"]), float(c["lon"])):
                    return float(c["lat"]), float(c["lon"]), baslik
                return None  # dogrudan madde kapsam disi -> yanlis eslesme riski, dur
        s = requests.get("https://tr.wikipedia.org/w/api.php",
            params={"action": "opensearch", "search": baslik, "limit": 3,
                    "format": "json"}, headers=UA, timeout=30).json()
        for alt in s[1]:
            r2 = requests.get("https://tr.wikipedia.org/w/api.php",
                params={"action": "query", "prop": "coordinates", "titles": alt,
                        "format": "json"}, headers=UA, timeout=30).json()
            for pg in r2["query"]["pages"].values():
                if "coordinates" in pg:
                    c = pg["coordinates"][0]
                    if kutuda(float(c["lat"]), float(c["lon"])):
                        return float(c["lat"]), float(c["lon"]), alt + " (arama)"
        # ayrica enwiki dene (Askeri yapilar cogunlukla enwiki'de kayitli)
        s3 = requests.get("https://en.wikipedia.org/w/api.php",
            params={"action": "opensearch", "search": baslik, "limit": 5,
                    "format": "json"}, headers=UA, timeout=30).json()
        for alt in s3[1]:
            r3 = requests.get("https://en.wikipedia.org/w/api.php",
                params={"action": "query", "prop": "coordinates", "titles": alt,
                        "format": "json"}, headers=UA, timeout=30).json()
            for pg in r3["query"]["pages"].values():
                if "coordinates" in pg:
                    c = pg["coordinates"][0]
                    if kutuda(float(c["lat"]), float(c["lon"])):
                        return float(c["lat"]), float(c["lon"]), alt + " (enwiki)"
    except Exception as e:
        return ("HATA:" + str(e),)
    return None

def haversine(a, b, c, d):
    R = 6371000.0
    p1, p2 = math.radians(a), math.radians(c)
    dp = math.radians(c - a); dl = math.radians(d - b)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))

df = pd.read_csv(CSV)
df["lon_wgs84"] = pd.to_numeric(df["lon_wgs84"], errors="coerce")
df["lat_wgs84"] = pd.to_numeric(df["lat_wgs84"], errors="coerce")
# tekrar calisabilirlik: eski capraz sutunlari temizle
df = df.drop(columns=[c for c in ["wiki_baslik", "wiki_lat", "wiki_lon",
    "osm_wiki_uyum_m", "capraz_guven", "onerilen_hata_m"] if c in df.columns])
sat = []
for _, r in df.iterrows():
    w = wiki_koord(WIKI_AD.get(r["yapi_id"]))
    if w and len(w) == 3:
        wlat, wlon, wbas = w
        if pd.notna(r["lon_wgs84"]):
            uyum = haversine(r["lat_wgs84"], r["lon_wgs84"], wlat, wlon)
            guven = "orta" if uyum <= 500 else "dusuk"
            hata = 500 if uyum <= 500 else 1000
        else:
            uyum, guven, hata = "", "dusuk", 1000
        sat.append({"yapi_id": r["yapi_id"], "wiki_baslik": wbas,
            "wiki_lat": round(wlat, 6), "wiki_lon": round(wlon, 6),
            "osm_wiki_uyum_m": round(uyum, 1) if uyum != "" else "",
            "capraz_guven": guven, "onerilen_hata_m": hata})
        print(f"{r['yapi_id']}: wiki {wlat:.4f},{wlon:.4f} uyum={uyum if uyum=='' else round(uyum)}m -> {guven}")
    else:
        sat.append({"yapi_id": r["yapi_id"], "wiki_baslik": "", "wiki_lat": "",
            "wiki_lon": "", "osm_wiki_uyum_m": "", "capraz_guven": "dusuk",
            "onerilen_hata_m": 1000})
        print(f"{r['yapi_id']}: wiki BULUNAMADI")
w = pd.DataFrame(sat)
df = df.merge(w, on="yapi_id", how="left")
df.to_csv(CSV, index=False)
with open(ROOT / "02_envanter" / "ADAY_NOTU.md", "a", encoding="utf-8") as f:
    f.write("\n## Capraz kontrol (18)\n\nVikipedi koordinatlariyla karsilastirma; "
            "<=500 m uyumda capraz_guven=orta (hata 500 m). Kaynak: tr.wikipedia.org (acik).\n")
print("-> aday_noktalar_taslak.csv guncellendi")
