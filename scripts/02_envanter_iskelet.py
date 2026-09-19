"""02 — Envanter iskeleti: semaya uygun CSV + GeoPackage taslagi.

Rapor karsiligi: §03 Tarihsel kanit, [1-3,18,21].
DURUSLIK NOTU: Bu betikteki tum koordinatlar BOS birakilir ya da acikca
TASLAK/DUSUK-GUVEN bayragi tasir. Gercek konumlar [18] kurumsal envanter +
donem haritalari + [1,2] yayinlariyla tek tek dogrulanmadan yuksek guvene
alinmaz. Kayip/belgeli yikik yapilar icin ayri satir acilir (korunma yanliligi
onlemi).
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "02_envanter"; ENV.mkdir(exist_ok=True)

ALANLAR = ["yapi_id","ad_standart","ad_varyantlari","kiyi","islev","evre",
 "tarih_bas","tarih_bit","tarih_guven","kaynak","ozgun_geometri",
 "lon_wgs84","lat_wgs84","konum_guven","hata_yaricapi_m","durum","not"]

# Pilot grup: 19.yy 2.yarisi-20.yy basi kiyi tabyalari (ad listesi on-envanter;
# koordinat girilmez — dogrulama [18]+[1,2] ile sahada/belgede yapilacak).
ADLAR = [
 ("T01","Namazgah Tabyasi","Namazgah; Namazgâh","Avrupa","kiyi_tabyasi","kullanim_1915","1868","1915","orta","[2] Acıoğlu 2016; [18] Alan Bşk. (dogrulanacak)"),
 ("T02","Hamidiye Tabyasi (Avrupa)","Hamidiye","Avrupa","kiyi_tabyasi","kullanim_1915","1890","1915","orta","[2]; [18] (dogrulanacak)"),
 ("T03","Mecidiye Tabyasi","Mecidiye","Avrupa","kiyi_tabyasi","kullanim_1915","1890","1915","orta","[2]; [18] (dogrulanacak)"),
 ("T04","Anadolu Hamidiyesi","Hamidiye (Anadolu)","Anadolu","kiyi_tabyasi","kullanim_1915","1890","1915","orta","[2]; [18] (dogrulanacak)"),
 ("T05","Orhaniye Tabyasi","Orhaniye","Anadolu","kiyi_tabyasi","kullanim_1915","1880","1915","dusuk","[2]; [18] (dogrulanacak)"),
 ("T06","Kumkale Kalesi (kale grubu)","Kumkale","Anadolu","kale","ilk_insa","1659","1915","orta","[1] Acıoğlu 2015 (ayri karsilastirma grubu)"),
 ("T07","Seddulbahir Kalesi (kale grubu)","Seddülbahir","Avrupa","kale","ilk_insa","1659","1915","orta","[1] (ayri karsilastirma grubu)"),
 ("T08","Kilitbahir Kalesi (kale grubu)","Kilitbahir; Kilidülbahir","Avrupa","kale","ilk_insa","1462","1915","orta","[1] (ayri karsilastirma grubu)"),
 ("T09","Cimenlik Kalesi (kale grubu)","Çimenlik; Kale-i Sultaniye","Anadolu","kale","ilk_insa","1462","1915","orta","[1] (ayri karsilastirma grubu)"),
 ("T10","Nara Burnu mevzii (belgesel kayit)","Nara","Anadolu","mevzi","kullanim_1915","1915","1915","dusuk","[21] DVA haritalari (bolgesel kapsam kontrolu); [3]"),
 ("T11","Domuzdere / kuzey kiyi mevzileri","—","Avrupa","mevzi","kullanim_1915","1915","1915","dusuk","[21]; [3] (kapsam disi kalabilir)"),
 ("T12","Kayip/yeniden-yapilan yapi ORNEGI","—","belirlenecek","yapi_evresi","ilk_insa","","","dusuk","[1,2] ad-degisimine ornek satir; korunma yanliligi icin tutulur"),
]

hedef = ENV / "envanter.csv"
with open(hedef, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=ALANLAR); w.writeheader()
    for aid, ad, vary, kiyi, islev, evre, tb, te, tg, kay in ADLAR:
        w.writerow({"yapi_id": aid, "ad_standart": ad, "ad_varyantlari": vary,
          "kiyi": kiyi, "islev": islev, "evre": evre, "tarih_bas": tb, "tarih_bit": te,
          "tarih_guven": tg, "kaynak": kay, "ozgun_geometri": "nokta",
          "lon_wgs84": "", "lat_wgs84": "", "konum_guven": "dusuk",
          "hata_yaricapi_m": 1000, "durum": "dogrulanacak",
          "not": "On-envanter: koordinat bos; [18]+donem haritasi+[1,2] ile dogrulanacak."})

print(f"-> {hedef} ({len(ADLAR)} on-envanter satir, koordinatsiz)")
print("SONRAKI ADIM: [18] + donem haritalari + [1,2] ile doldur; konum_guven+hata_yaricapi bos birakilamaz.")

# GeoPackage uretimi 03 sonrasi koordinatlar girilince scripts/03 icinde degil,
# ayri dogrulama adiminda (08_saha_belge) yapilir — burada bilerek uretilmez.
