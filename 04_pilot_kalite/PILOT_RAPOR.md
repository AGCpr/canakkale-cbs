# Pilot ve veri kalite kontrol raporu (K2 kanıtı)

Tarih (UTC): 2026-09-16. Statü: **K2 GEÇTİ (teknik hat)** — kara–deniz ve görüş ayarları sınandı.
Not: envanter koordinatları henüz boş olduğundan tarihsel yargı içermez (K3 açık).

## Veri

- DEM: Copernicus GLO-30, 6 karo (N39-40/E025-027), erişim 2026-09-16, `03_veri/ham/`.
- Çalışma gridi: EPSG:32635, 30 m, 3417×2941 (10,05 M hücre); işlem penceresi 8 km koridor kırpığı.
- Kara piksel 5.628.373 / su 4.421.024; hedef su (5 km koridor içi) paydası sabitlendi.
- Düşey: EGM2008 (Copernicus varsayılanı); yatay WGS84 → 32635 bilineer.
- 5 m örnekleme yapılmadı (yasak denetimi `params/model.yaml`).

## Görüş protokolü doğrulaması

- Birincil: `gdal_viewshed` (GDAL 3.13.3, QGIS 4.2.2 paketi) — gözlemci 4 m, hedef 0 m (deniz seviyesi),
  mesafe 15 km, refraksiyon 0,13, eğrilik açık.
- Ham hata bulundu ve düzeltildi: görünür değer 255 (1 değil); çıktı penceresi kendi transformunu taşır
  (tam-grid varsayımı yanlıştı). Düzeltme sonrası 48 kıyı-şeridi noktasında fV: 25/48 sıfır-üstü,
  medyan 0,0018, maks 0,1404 — kıyı-içi noktaların düşük, kıyı-açıklarının yüksek skor alması beklenen yöndedir.
- El kontrolü: tek nokta (446055, 4450995) bağımsız çağrıda görünür oran ≈ %10,3 (1001×1001 pencere içi) —
  tablo değeriyle tutarlı.

## Ölçütler

- Eğim (Horn, derece): medyan ≈ 3,9 (kıyı şeridi örneklemi).
- R yarıçap duyarlılığı (koridor medyanı): r500 ≈ 0,0 / r1000 ≈ −1,2 / r2000 ≈ 0,0 m;
  p5–p95 bantları yarıçapla genişler (±23 → ±57 m) — H3 girdisi olarak `r_duyarlilik.npz` arşivli.
- Dönüşümler ön-kayıtlı (winsorize p5–p95; eğim ters-doğrusal 5–30°); tarihsel puana göre ayar yok.

## K2 kapı hükmü

Kara–deniz maskesi + görüş protokolü teknik olarak geçerli. K3 (bağımsız kıyas) için
envanter koordinatlarının `[18]+dönem haritası+[1,2]` ile doldurulması gerekir — bkz. `08_saha_belge/`.
