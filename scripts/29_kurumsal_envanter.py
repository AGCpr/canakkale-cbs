"""29 — Kurumsal envanter ithali (cba -> cbs, dogrulamali).

Kaynak: cba 02_Arastirma/04_kayitlar/tarihsel_envanter.csv (Alan Baskanligi
ziyaret sayfalari, erisim 16-17 Eylul 2026). Caveat'lar aynen korunur:
konum_turu=kurumsal_ziyaret_referansi, ozgun_oturum_dogrulandi=False.
Dogrulama: bizim OSM taslaklarla mesafe; >500 m uyumsuzluk BAYRAKLANIR.
ID ad-alani: R01-R07 tabya, RK1-RK4 kale (carpismasiz).
Cikti: 02_envanter/kurumsal_envanter.csv + KURUMSAL_NOT.md
"""
from pathlib import Path
import csv, math
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CBA = Path(r"C:\Users\AGC\OneDrive\Masaüstü\cba\02_Arastirma\04_kayitlar\tarihsel_envanter.csv")
ENV = ROOT / "02_envanter"

kaynak = pd.read_csv(CBA)
bizim = pd.read_csv(ENV / "aday_noktalar_taslak.csv")
bizim["lon_wgs84"] = pd.to_numeric(bizim["lon_wgs84"], errors="coerce")
bizim["lat_wgs84"] = pd.to_numeric(bizim["lat_wgs84"], errors="coerce")

def hav(a, b, c, d):
    R = 6371000.0
    p1, p2 = math.radians(a), math.radians(c)
    h = math.sin(math.radians(c - a) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(d - b) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))

ESLESME = {"T01": "T01", "T02": "T03", "T03": None, "T04": "T04",
           "T05": None, "T06": None, "T07": None,
           "K01": "T08", "K02": "T07", "K03": None, "K04": None}
YENI = {"T01": "R01", "T02": "R02", "T03": "R03", "T04": "R04",
        "T05": "R05", "T06": "R06", "T07": "R07",
        "K01": "RK1", "K02": "RK2", "K03": "RK3", "K04": "RK4"}

sat = []
for _, r in kaynak.iterrows():
    kid = r["id"]
    uyum, bayrak = "", ""
    es = ESLESME.get(kid)
    if es:
        b = bizim[bizim["yapi_id"] == es].iloc[0]
        if pd.notna(b["lon_wgs84"]):
            uyum = round(hav(r["lat"], r["lon"], b["lat_wgs84"], b["lon_wgs84"]), 1)
            bayrak = "" if uyum <= 500 else "UYUMSUZ-500m+"
    sat.append({"kayit_id": YENI[kid], "cba_id": kid, "ad_standart": r["ad"],
        "lon_wgs84": r["lon"], "lat_wgs84": r["lat"], "grup": r["grup"],
        "donem": r["donem"], "kaynak_url": r["kaynak"], "erisim": r["erisilen_tarih"],
        "konum_turu": r["konum_turu"], "ozgun_oturum_dogrulandi": r["ozgun_oturum_dogrulandi"],
        "konum_guven": "orta", "hata_yaricapi_m": 500,
        "osm_capraz_m": uyum, "capraz_bayrak": bayrak,
        "not": r["not_"]})
    print(YENI[kid], r["ad"][:30], "osm_uyum:", uyum if uyum != "" else "yok", bayrak)

pd.DataFrame(sat).to_csv(ENV / "kurumsal_envanter.csv", index=False)
(ENV / "KURUMSAL_NOT.md").write_text(
 "# Kurumsal envanter notu (29)\n\n- Kaynak: cba tarihsel_envanter.csv (Alan Baskanligi ziyaret sayfalari).\n"
 "- Guven ORTA (kurumsal referans), hata 500 m; ozgun oturum dogrulanmadi (kaynakta False).\n"
 "- OSM capraz mesafesi 500 m uzeri BAYRAKLANIR; analiz noktasi tasinmaz.\n"
 "- K3-GERCEK birincil grup: R01-R07 tabyalar; RK1-RK4 betimsel (ayri donem).\n",
 encoding="utf-8")
print("-> kurumsal_envanter.csv (11 kayit)")
