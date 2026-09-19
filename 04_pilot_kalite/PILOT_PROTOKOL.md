# CBS uygulama protokolü (rapor §07) — denetlenebilir yol

Her işlem için girdi, parametre, çıktı, yazılım sürümü ve kalite notu `logs/` içine kaydedilir.

## 01 Koordinatlandır

Tarihsel haritalarda sabit kontrol noktaları; bağımsız kontrol noktalarında metre cinsinden hata; yalnız dönüşüm artıklarına güvenilmez [16].
Uygulama: `qgis/` içinde GCP listesi + RMSE raporu (`08_saha_belge/`).

## 02 Uyumlaştır

Metre tabanlı projeksiyon (EPSG:32635); ortak raster boyutu, hizası ve düşey referans; deniz/kara/boş ayrı.
Uygulama: `scripts/03_uyumlastir.py` (gdalwarp, -tr 30 30, -tap hizalama, kara maskesi).

## 03 Ölçüt üret

Eğim + göreli yükselti; aday konumlarda görüş aynı su hedef alanına göre; konum hata çevresiyle özet [5,17].
Uygulama: `scripts/04_olcut_uret.py` (gdaldem slope, focal-mean R, gdal_viewshed tabanlı V).

## 04 Tekrar çalıştır

Puanlama + ağırlık senaryoları işlem modeliyle; sürüm + tohum + parametre arşivi.
Uygulama: `scripts/05_model_calistir.py` + `scripts/07_belirsizlik.py`.

## Görüş kontrol listesi

Gözlemci/hedef yüksekliği, eğrilik/kırılma, mesafe sınırı, arazi tamponu aynı protokole bağlı.
Örnekleme aralığı ≠ çıktı çözünürlüğü: seyrek görüş örneklerinden kesintisiz hassas yüzey varmış gibi sonuç üretilmez.
