# QGIS katman listesi (ana çalışma ortamı)

QGIS 4.2.2'de yeni proje açıp şu sırayla ekleyin (CRS: EPSG:32635):

1. `03_veri/islenmis/dem_30m_32635.tif` (araZi)
2. `05_olcut_model/egim_derece.tif`, `r_1000m.tif`, `fR.tif`, `fS.tif`
3. `05_olcut_model/U_raster_esit.tif` (+ uzman senaryoları)
4. `09_teslim/canakkale_cbs.gpkg` → katmanlar: `su_hedef`, `koridor`, `ornek_noktalar`
   (+ K3 sonrası `05_olcut_model/aday_noktalar.gpkg` → kırmızı yıldız; etiketi `yapi_id`)
5. `03_veri/ham/ne_10m_land/ne_10m_land.shp` (yalnızca bağlam altlığı — analiz değil) [20]

Stil önerisi: U için tek-bant sözde-renk (viridis, %2–98 gerilim); kararlılık noktaları
`07_belirsizlik/kararlilik.csv` → `ornek_noktalar` ile `nok_id` üzerinden birleştirilip
sınıf (yüksek/kararlı vb.) ile sembolize edilir (Şekil 2 okuma matrisi).
Proje dosyası `canakkale_vrs.qgz` adıyla bu klasöre kaydedilir (K4).
