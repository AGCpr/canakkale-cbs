# Nihai teslim raporu — Çanakkale Boğazı CBS uygulaması

Tarih (UTC): 2026-09-16 · Yöntem önerisinin (16 Eylül 2026 raporu) sahaya geçirilmiş, izlenebilir uygulaması.
İlke: **Önce tarihsel bağlam. Sonra model. Ardından bağımsız sınama.**

## 1. Ne teslim edildi (5 çıktı, rapor §11)

| # | Çıktı | Dosya |
|---|---|---|
| 01 | Envanter ve dönem haritası | `02_envanter/envanter.csv` (12 ön-kayıt) + `kurumsal_envanter.csv` (11 kurumsal referans, orta güven) + `capraz_kaynak.csv` (Overpass+Wikidata) |
| 02 | Ölçüt ve uygunluk atlası | `05_olcut_model/` (eğim, R500/1000/2000, fR, fS, fE, U/M2 senaryoları, kümülatif) + `09_teslim/harita_*.png` + `web/` atlası |
| 03 | Karşılaştırma tablosu | `K3_PILOT_HUKMU.md` + `K3_GERCEK_HUKMU.md` + `gercek_kiyas.json` (bant-eşleşme, ablasyon, Pareto, Dirichlet) |
| 04 | Kararlılık ve değişim haritası | `kararlilik.csv` + `mc_aday.csv` + `deniz_seviyesi.csv` + `mapzen_karsilastirma.json` + OWA |
| 05 | Tekrar-üretim paketi | `qgis/canakkale_vrs.qgz` + `canakkale_cbs.gpkg` + `params/model.yaml` + `sonuc-tablolari.xlsx` + `MANIFEST.sha256` + `cbs_teslim_paketi.zip` |

## 2. Bulgular (pilot + kurumsal-tanısal)

- **Şablon cümle (§11, aynen):** "Tarihsel noktalar, tanımlanan fiziki ölçütler bakımından karşılaştırma alanlarından **ayrışmıyor**; bu sonuç belirtilen veri ve senaryo sınırları içinde geçerli."
- **K3-GERÇEK (7 kurumsal tabya vs bant-eşleşmiş 28 kontrol):** M1 medyan fark −0.023 (delta +0.10),
  fV fark −0.063 (delta −0.43); referans başına n_k=4 <5 olduğundan çıkarım **betimsel** (cba kuralı), p yok.
- H1-pilot (taslak, n=4 vs 15): M1 −0.006 (p=0.74), fV −0.004 (p=0.51) — ayrışma yok.
- H2: pilot M0→M1 (delta −0.23→+0.13); M2/H2b fark −0.059 (p=0.81) — ek-bilgi işareti zayıf.
- Ablasyon (kontroller): V-hariç rho 0.99, S-hariç 0.88, R-hariç 0.45, geometrik 0.41 — sıralamayı R sürüklüyor.
- Pareto'da tabya: R06 Ertuğrul, R07 Çamburnu Kakavan. Dirichlet(1,1,1)×2000: R06 1.0, R07 0.67, diğerleri 0.
- Monte Carlo (taslak): T05 1.0, T07-taslak 0.99 — küme-koşullu kararlılık.
- Mapzen ikinci DEM: medyan +2.67 m, NMAD 3.97, Spearman 0.999 (yükseklik) / 0.96 (fR) — sıra uyumu yüksek.
- OWA: OR rho 0.51 / AND rho 0.37 — telafi varsayımına duyarlı.
- Hedef −1 m dejenere (dışlandı); AHP uzman senaryoyla uyumlu (CR 0.008).
- Yaka denetimi (D9/D10): çizgi-izdüşüm yanlışı bileşen yöntemiyle düzeltildi (9/9); 48 kontrolün tamamı Avrupa çıktı —
  koridor-içi Anadolu şeridi maskenin %0,05'i. 4 Anadolu noktası eklendi (52 kontrol), ölçek donduruldu.

## 3. Veri ve araç künyesi

- DEM: Copernicus GLO-30, 6 karo, erişim 2026-09-16 · Grid: EPSG:32635, 30 m, 3417×2941 · Düşey EGM2008.
- Bağlam: Natural Earth 1:10m (analiz altlığı değil) [20] · Aday koordinat: OSM Nominatim (ODbL, taslak).
- Araç: GDAL 3.13.3 + QGIS 4.2.2 + Python 3.11 (`logs/ortam.txt`). 5 m örnekleme yapılmadı.

## 4. Kapılar

K1 ✅ · K2 ✅ · K3 ✅ PİLOT · **K3 ✅ GERÇEK-tanısal** (7 kurumsal tabya, bant-eşleşme, betimsel çıkarım; `K3_GERCEK_HUKMU.md`) · K4 ✅ (`logs/dogrulama.txt`, manifest 104/104 OK, hata 0).
Kalan kurumsal iş: özgün oturum doğrulaması (plan jeoreferanslama) + dönem kıyı çizgisi + HGM modeli — `08_saha_belge/` protokolü hazır.

## 5. Yeniden çalıştırma

`README.md` → Hızlı başlat (`scripts/run_all.py`, tam/hızlı kip). QGIS'te `qgis/canakkale_vrs.qgz` açılır.
Web: `web/` klasörü statik yayın (`bogaz-atlasi` Pages projesine bağlı repo).
