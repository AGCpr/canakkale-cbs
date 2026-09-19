"""28 — Cok-kaynak zenginlestirme: Overpass + Wikidata capraz kontrolu.

Rapor karsiligi: §03 (konum guveni), [18] oncelikli kaynak (degismez).
Yontem: (a) Overpass: bbox icinde historic~fort/castle/battlefield|fortification
veya military~fort/bunker/fortress geometrileri; (b) Wikidata wbsearchentities
(TR+EN ad varyantlari), bbox-gecidi. Uyum kurali (on-kayit): 2+ bagimsiz kaynak
<=300 m -> orta/300 m; tek kaynak -> dusuk/1000 m. Yuksek guven YOK ([18] sart).
Cikti: 02_envanter/capraz_kaynak.csv + ADAY_NOTU eki (analiz tamponlari korunur).
"""
from pathlib import Path
import json, math, time
import requests
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "02_envanter"
UA = {"User-Agent": "cbs-pilot-arastirma/1.0 (akademik yontem pilotu)"}
KUTU = dict(guney=39.9, bati=25.9, kuzey=40.7, dogu=27.1)

ADLAR = {
 "T01": ["Namazgah Tabyası", "Namazgah Tabya", "Namazgah redoubt"],
 "T02": ["Hamidiye Tabyası", "Hamidiye Tabya"],
 "T03": ["Mecidiye Tabyası", "Mecidiye Tabya"],
 "T04": ["Anadolu Hamidiye Tabyası", "Anadolu Hamidiye"],
 "T05": ["Orhaniye Tabyası", "Orhaniye Tabya"],
 "T06": ["Kumkale Kalesi", "Kumkale Castle", "Kumkale Fortress"],
 "T07": ["Seddülbahir Kalesi", "Seddulbahir Castle", "Sedd el Bahr"],
 "T08": ["Kilitbahir Kalesi", "Kilitbahir Castle"],
 "T09": ["Çimenlik Kalesi", "Cimenlik Castle", "Çimenlik Fortress"],
 "T10": ["Nara Burnu", "Nara Cape"],
}

def kutuda(lat, lon):
    return KUTU["bati"] <= lon <= KUTU["dogu"] and KUTU["guney"] <= lat <= KUTU["kuzey"]

# (a) Overpass
ql = (f'[out:json][timeout:90];(node["historic"~"fort|castle|battlefield|fortification"]'
      f'({KUTU["guney"]},{KUTU["bati"]},{KUTU["kuzey"]},{KUTU["dogu"]});'
      f'way["historic"~"fort|castle|battlefield|fortification"]'
      f'({KUTU["guney"]},{KUTU["bati"]},{KUTU["kuzey"]},{KUTU["dogu"]});'
      f'node["military"~"fort|bunker|fortress"]'
      f'({KUTU["guney"]},{KUTU["bati"]},{KUTU["kuzey"]},{KUTU["dogu"]}););out center tags;')
over = []
try:
    r = requests.post("https://overpass.kumi.systems/api/interpreter", data={"data": ql},
                      headers=UA, timeout=120)
    r.raise_for_status()
    for el in r.json().get("elements", []):
        tag = el.get("tags", {})
        if "lat" in el:
            lat, lon = el["lat"], el["lon"]
        elif "center" in el:
            lat, lon = el["center"]["lat"], el["center"]["lon"]
        else:
            continue
        over.append({"ad": tag.get("name", ""), "historic": tag.get("historic", ""),
                     "military": tag.get("military", ""), "lat": lat, "lon": lon,
                     "osm_id": f"{el['type']}/{el['id']}"})
except Exception as e:
    print("Overpass HATASI:", e)
print(f"Overpass: {len(over)} geometri")
pd.DataFrame(over).to_csv(OUT / "overpass_ham.csv", index=False)

# (b) Wikidata
def wd_ara(ad):
    try:
        r = requests.get("https://www.wikidata.org/w/api.php",
            params={"action": "wbsearchentities", "search": ad, "language": "tr",
                    "format": "json", "limit": 5}, headers=UA, timeout=30).json()
        ids = [x["id"] for x in r.get("search", [])]
        if not ids:
            return []
        r2 = requests.get("https://www.wikidata.org/w/api.php",
            params={"action": "wbgetclaims", "entity": "|".join(ids[:5]),
                    "property": "P625", "format": "json"}, headers=UA, timeout=30).json()
        cikti = []
        for i in ids[:5]:
            try:
                v = r2["claims"][i]["P625"][0]["mainsnak"]["datavalue"]["value"]
                if kutuda(v["latitude"], v["longitude"]):
                    cikti.append({"qid": i, "lat": v["latitude"], "lon": v["longitude"]})
            except KeyError:
                pass
        return cikti
    except Exception:
        return []

def haversine(a, b, c, d):
    R = 6371000.0
    p1, p2 = math.radians(a), math.radians(c)
    h = math.sin(math.radians(c - a) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(d - b) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))

df = pd.read_csv(OUT / "aday_noktalar_taslak.csv")
df["lon_wgs84"] = pd.to_numeric(df["lon_wgs84"], errors="coerce")
df["lat_wgs84"] = pd.to_numeric(df["lat_wgs84"], errors="coerce")
sat = []
for _, r in df.iterrows():
    kb = []
    if pd.notna(r["lon_wgs84"]):
        kb.append(("OSM-Nominatim", r["lat_wgs84"], r["lon_wgs84"]))
    for ov in over:
        nm = (ov["ad"] or "").lower()
        if any(k.lower().split()[0] in nm for k in ADLAR.get(r["yapi_id"], []) if k):
            kb.append((f"OSM-Overpass:{ov['osm_id']}", ov["lat"], ov["lon"]))
    for vary in ADLAR.get(r["yapi_id"], []):
        for w in wd_ara(vary):
            kb.append((f"Wikidata:{w['qid']}", w["lat"], w["lon"]))
        time.sleep(0.4)
    # ikili uzakliklar
    if len(kb) >= 2 and pd.notna(r["lon_wgs84"]):
        dmin = min(haversine(r["lat_wgs84"], r["lon_wgs84"], la, lo) for _, la, lo in kb[1:])
        n_yakin = sum(1 for _, la, lo in kb[1:]
                      if haversine(r["lat_wgs84"], r["lon_wgs84"], la, lo) <= 300)
    else:
        dmin, n_yakin = "", 0
    guven = "orta" if (n_yakin >= 1) else "dusuk"
    sat.append({"yapi_id": r["yapi_id"], "kaynak_sayisi": len(kb),
                "en_yakin_bagimsiz_m": round(dmin, 1) if dmin != "" else "",
                "capraz_guven_yeni": guven, "onerilen_hata_m_yeni": 300 if guven == "orta" else 1000,
                "kaynaklar": "; ".join(f"{k}({la:.4f},{lo:.4f})" for k, la, lo in kb[:6])})
    print(r["yapi_id"], "kaynak:", len(kb), "->", guven)
    time.sleep(0.5)

w = pd.DataFrame(sat)
w.to_csv(OUT / "capraz_kaynak.csv", index=False)
with open(OUT / "ADAY_NOTU.md", "a+", encoding="utf-8") as f:
    f.seek(0)
    if "## Cok-kaynak matris (28)" not in f.read():
        f.write("\n## Cok-kaynak matris (28)\n\nOverpass geometrileri + Wikidata koordinatlari; "
            "2+ kaynak <=300 m uyumda orta/300 m. Yuksek guven icin [18] sart; analiz tamponlari (1000 m) korunur.\n")
print("-> capraz_kaynak.csv")
