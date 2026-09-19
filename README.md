# Çanakkale Boğazı'nda Stratejik Mekân Seçimi — CBS Uygulama Projesi

> Coğrafya × Tarih × CBS | Araştırma ve uygulama raporu (16 Eylül 2026) yöntem önerisinin sahaya geçirilmiş, izlenebilir uygulaması.
> İlke: **Önce tarihsel bağlam. Sonra model. Ardından bağımsız sınama.**
> Statü notu: Bu depo bir **yöntem uygulaması + tekrar-üretim paketidir**. Gerçek uygunluk / başarı oranı iddiası, K3 kapısı (bağımsız kıyas) geçilmeden yazılmaz.

## Okuma rotası (raporla birebir)

| Rapor bölümü | Bu depodaki karşılığı |
|---|---|
| 01 Yönetici özeti | `00_yonetim/KARAR_KAYDI.md` + bu README |
| 02 Araştırma alanı + H1/H2/H3 | `01_kapsam_literatur/KAPSAM.md` |
| 03 Tarihsel kanıt + zaman zinciri | `02_envanter/` (şema + taslak envanter, güven bayraklı) |
| 04 Yöntem seçimi | `00_yonetim/KARAR_KAYDI.md` §Yöntem görevleri |
| 05 Veri mimarisi | `03_veri/VERI_KATALOGU.md` |
| 06 Önerilen model U(x) | `05_olcut_model/MODEL_KARTI.md` + `scripts/` |
| 07 CBS uygulama protokolü | `04_pilot_kalite/PILOT_PROTOKOL.md` + `scripts/` |
| 08 Karşılaştırma tasarımı | `06_karsilastirma/TASARIM.md` + `scripts/06_karsilastirma.py` |
| 09 Belirsizlik ve yorum | `07_belirsizlik/SENARYO_MATRISI.md` + `scripts/07_belirsizlik.py` |
| 10 Aşamalı ilerleyiş (8 hf / 4 kapı) | `00_yonetim/IS_PLANI.md` |
| 11 Teslim ve araştırma sınırı | `09_teslim/TESLIM_KONTROL.md` |
| 12 Kaynakça | `01_kapsam_literatur/KAYNAKCA.md` |

## Dört karar kapısı (takvim varsayımdır, kapı kriteri bağlayıcıdır)

- **K1 · Veri hazır (2. hf):** kaynak, dönem, hata ve eksikler görünür. Kanıt: `03_veri/VERI_KATALOGU.md` dolu + `logs/`.
- **K2 · Pilot geçerli (3. hf):** kara–deniz ve görüş ayarları sınanmış. Kanıt: `04_pilot_kalite/` pilot raporu.
- **K3 · Sonuç sınanmış (6. hf):** bağımsız kıyas + belirsizlik tamam. Kanıt: `06_karsilastirma/` + `07_belirsizlik/` çıktıları.
- **K4 · Teslim hazır (8. hf):** başka kullanıcı projeyi çalıştırabiliyor. Kanıt: `09_teslim/` + temiz `logs/run_*.log`.

Uzman rolleri ayrı personel olmak zorunda değildir; görev ve kontrol sorumlulukları `00_yonetim/IS_PLANI.md` içinde atanır.

## Hızlı başlat (QGIS 4.2.2 + GDAL ile test edildi)

```powershell
# 1) Python bağımlılıkları (hafif, GDAL QGIS içinden gelir)
pip install -r requirements.txt

# 2) Açık veriyi indir + envanter şemasını üret
python scripts/01_acik_veri_indir.py
python scripts/02_envanter_iskelet.py

# 3) Pilot: uyumlaştır → ölçüt üret → modeli çalıştır
python scripts/03_uyumlastir.py
python scripts/04_olcut_uret.py
python scripts/05_model_calistir.py

# 4) Sınama + belirsizlik (tasarım doğrulama)
python scripts/06_karsilastirma.py
python scripts/07_belirsizlik.py

# 5) Atlas + teslim paketi
python scripts/08_atlas_uret.py
python scripts/09_teslim_paketi.py

# 6) Pilot adaylar (OSM taslak) + K3 hükmü + tamamlayıcılar
python scripts/10_aday_nokta_derle.py
python scripts/11_aday_olcut.py
python scripts/12_pilot_kiyas.py
python scripts/13_k3_hukum_atlas.py
python scripts/14_tamamlayici.py  # kümülatif görüş + OWA

# 7) QGIS projesi + doğrulama + bağımsız denetim
python scripts/15_qgis_proje.py
python scripts/16_dogrula.py
python scripts/17_denetim.py

# Tek komutla tüm hat (önerilen): python scripts/run_all.py
# Hızlı kip (ağır viewshed adımlarını atlar): python scripts/run_all.py --hizli

## Web arayüzü (amiral gemisi)

`web/index.html` — sinematik hero, interaktif koyu harita (5 yüzey + filtre + liste),
sonuç grafikleri, veri kaşifi ve paket indirme. Çalıştırma:
`Set-Location web; python -m http.server 8765` → http://localhost:8765/index.html

Yayın: site `web/` klasörü GitHub'da — https://github.com/AGCpr/bogaz-atlasi
(Cloudflare Pages: repo'yu bağla, root `/`, build komutu boş).
```

QGIS ana çalışma ortamıdır: `qgis/canakkale_vrs.qgz` (üretilecek) + GeoPackage + rasterlar `09_teslim/` altında toplanır.
İstatistik ve senaryo tekrarları R/Python ile yürütülür. İlk yatırım lisansa değil veri kalitesi ve tarihsel doğrulamaya yapılır.

## Sonuç cümlesi şablonu (rapor §11 — aynen kullanılır)

> "Tarihsel noktalar, tanımlanan fiziki ölçütler bakımından karşılaştırma alanlarından ayrışıyor / ayrışmıyor; bu sonuç belirtilen veri ve senaryo sınırları içinde geçerli."

## Üç kritik veri kararı (rapor §05 — ihlal edilmez)

1. FABDEM Copernicus'tan türetilir; bağımsız doğrulama sayılmaz.
2. Deniz tabanı görüş yüzeyi değildir; görüşte deniz seviyesi kullanılır.
3. 30 m veriyi 5 m'ye örneklemek yeni arazi ayrıntısı üretmez.

## Dizin ağacı

```
00_yonetim/ 01_kapsam_literatur/ 02_envanter/ 03_veri/ 04_pilot_kalite/
05_olcut_model/ 06_karsilastirma/ 07_belirsizlik/ 08_saha_belge/ 09_teslim/
scripts/ qgis/ params/ logs/
```
