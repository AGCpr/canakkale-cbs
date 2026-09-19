# Veri kataloğu (canlı — her veri girişinde güncellenir)

## Katmanlar

| Katman | Tercih / alternatif | Dosya (depoda) | Datum / CRS | Tarih / sürüm | Boşluk / hata | Lisans | Kabul |
|---|---|---|---|---|---|---|---|
| Arazi yüksekliği (ana) | Copernicus GLO-30 → proje gridine | `03_veri/ham/dem_30m.tif` (indirilecek) | EGM2008 düşey; yatay WGS84 → işlik EPSG:32635 | Sürüm + erişim tarihi loglanır | Boşluk maskesi + yerel hata notu | Copernicus lisansı | Arazi–yüzey ayrımı kayıtlı |
| Arazi yüksekliği (duyarlılık) | SRTM 1-arcsec | `03_veri/ham/dem_srtm.tif` | WGS84 / EGM96 | Sürüm + erişim tarihi | — | Kamu | Yalnız duyarlılık |
| Arazi yüksekliği (alternatif) | FABDEM V1-2 |_opsiyonel_| — | CC BY-NC-SA 4.0 [13] | Copernicus türevi → bağımsız doğrulama sayılmaz | Kısıtlı paylaşım | Not düşülür |
| Kıyı / su hedef alanı | OSM su poligonu + NE bağlam | `03_veri/islenmis/su_hedef.gpkg` | EPSG:32635 | Tarihi belli; dönem farkları ayrı | 1 baskın boğaz poligonu (3.971 km²) + 45 hücre-altı leke toplam 0,126 km² (%0,003; vektörleştirme artığı, analiz raster maskeyi kullanır) | ODbL (OSM) / Kamu (NE) | Ortak su tanımı |
| Tarihsel envanter | Kurum + dönem haritaları + yayınlar [1–3,18,21] | `02_envanter/envanter.csv` + `.gpkg` | EPSG:4326 kaynak → 32635 işlik | Yapı-evresi aralığı | Konum güveni + hata çevresi | Kaynak belirtilir | Kayıp yapılar dahil |
| Pilot aday noktalar (TASLAK) | OSM Nominatim, 8/10 bulundu, 2026-09-16 | `02_envanter/aday_noktalar_taslak.csv`, `05_olcut_model/aday_noktalar.gpkg` | EPSG:4326 → 32635 | 2026-09-16 | düşük güven + 1000 m (2 noktada kara-oturtma: 30/210 m) | ODbL (OSM) | Kanıt değil; zincir testi |
| Bağlam (yol/iskele) | Dönem bilgisi varsa | `03_veri/islenmis/baglam_*` | — | Tarih+ölçek uyumu | — | — | Soruya bağlı eklenir |

## Üç kritik veri kararı (uygulamada denetlenir)

1. FABDEM ↔ Copernicus bağımsız kıyas değildir (`scripts/07_belirsizlik.py` içinde ayrı bayrak).
2. Görüş hedefi deniz seviyesidir; EMODnet batimetrisi görüş yüzeyine karıştırılmaz.
3. Ortak grid 30 m'dir; `gdalwarp -tr 5 5` gibi keskinleştirme yasaktır — kontrol `scripts/03_uyumlastir.py` içindedir.
