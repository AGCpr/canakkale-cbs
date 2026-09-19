# Tarihsel envanter — şema ve kurallar (rapor §03)

Karşılaştırma birimi: yalnız "yer" değil, belgelenmiş bir dönemdeki **"yer + yapı evresi"**dir.
Tek ad = tek yapı varsayımı kurulmaz [2]. Bugünkü anma peyzajı savaş dönemi arazisiyle aynı kabul edilmez [3].
Yalnızca ayakta kalmış yapılar seçilirse korunma yanlılığı doğar; belgeli kayıp yapılar da alınır.

## Zaman zinciri (her yapı-evresi için)

İlk yer seçimi (ilk inşa / en erken güvenilir kayıt) → Yeniden düzenleme (taşınma, ek yapı, ad/işlev değişimi)
→ Kullanım kesiti (örn. 1915 belgelenmiş durum) → Bugünkü iz (kalıntı, anıt, dolgu, yol, yapılaşma)

## Alanlar (`02_envanter/envanter.csv`)

`yapi_id, ad_standart, ad_varyantlari, kiyi (Gelibolu/Anadolu), islev (kıyı tabyası/kale/diğer),
evren (ilk_insa/yeniden_duzenleme/kullanim_1915/bugunku_iz), tarih_bas, tarih_bit, tarih_guven (yüksek/orta/düşük),
kaynak (kısa künye + [n]), ozgun_geometri (nokta/poligon), lon_wgs84, lat_wgs84, konum_guven (yüksek/orta/düşük),
hata_yaricapi_m, durum (mevcut/kayıp_belgeli/tartışmalı), not`

## Konum güveni kuralı

- yüksek: kurum envanteri + dönem haritası + yayın üçgeni tutarlı, hata ≤100 m.
- orta: iki kaynak tutarlı veya tek güvenilir dönem haritası, hata 100–500 m.
- düşük: yalnızca tanımlı tarif / çakışan adlar, hata >500 m veya taslak (OSM-türevi aday).
- `hata_yaricapi_m` boş bırakılamaz; bilinmiyorsa güven=düşük + 1000 m yazılır ve `not` içine gerekçe işlenir.

## Görsel çevre kuralı [7]

Puan yalnızca yapı hücresinden okunmaz; yapı oturumu veya konum hata çevresindeki puan dağılımı (medyan + IQR) da kaydedilir.
