# Değişiklik günlüğü

## v3.2.0 — sağlamlık turu (2026-09-18)

- Eşleşmiş-çift Wilcoxon (p=0.84) + dönem kırılımı (geç 0.48 vs çok evreli 0.34, betimsel).
- Web'de GERÇEK birincil (pilot ikincil); PDF/Excel indirme kartları; swipe + hikaye.
- `--hizli` ucu test edildi: 4 idempotens hatası düzeltildi (05 fE koruma, 36/02/10/18/28),
  deterministik qgz, öz-referans loglar manifest dışı.
- Denetim 44/44, paket 105 dosya, hızlı kip tam yeşil.

## v3.1.0 — çıkarım turu (2026-09-18)

- Gözlemci yüksekliği duyarlılığı (2/4/10 m, 11 kurumsal): R06 0.22→0.47,
  Kilitbahir kümesi 10 m'de bile ~0 (yapısal kapalılık).
- Kontrol sıklaştırma: 100 kontrol (48+4+48); fR ölçeği ilk-48 çapasında birleştirildi.
- K3-GERÇEK çıkarımsal havuz (n_t=6, n_k=36): M1 p=0.53, fV p=0.19 — ayrışmıyor; R04 betimsel.
- PDF bulgular raporu, Excel kitabı, full-repo GitHub (`canakkale-cbs`).
- Yaka teşhisi düzeltmesi (D9), tek-yaka denetimi (D10) kayıt altında.
- Denetim 44/44, paket 105 dosya.

## v3.0.0 — cba birleşimi (2026-09-18)

- 11 kurumsal ziyaret referansı ithal edildi (çapraz doğrulamalı, orta güven);
  K3-GERÇEK tanısal hüküm yazıldı (7 tabya vs 28 bant-eşleşmiş kontrol, betimsel).
- Yaka teşhisi düzeltildi (çizgi→kara bileşeni, 9/9); tek-yaka denetimi sonrası
  4 Anadolu kontrolü eklendi (52 kontrol, ölçek donduruldu).
- Mapzen Terrarium ikinci DEM (medyan +2.67 m, NMAD 3.97, Spearman 0.999).
- 162-senaryo ruhu: ablasyon (Spearman/Jaccard) + Pareto + Dirichlet(1,1,1)×2000.
- Excel çalışma kitabı, self-host fontlar (çevrimdışı site), genişlik kesitleri.
- Web: 71 nokta (11 kurumsal rozetli), tur tüm tarihsel noktaları gezer.
- Denetim 44/44, paket 104 dosya.

## v2.0.0 — 100x turu 2 (2026-09-17)

- Çok-kaynak zenginleştirme: Overpass (78 geometri) + Wikidata çapraz kontrolü;
  5 aday orta güvene yükseldi (11–49 m uyum), `capraz_kaynak.csv`.
- Monte Carlo: Dirichlet(6,6,6) + R yarıçapı, 1000 çekimde yakınsama;
  T05 P=1.0, T07 P=0.985, diğerleri 0 (`mc_aday.csv`, `mc_yakinsama.png`).
- Web: Eşit/Uzman swipe karşılaştırma + 5 sahnelik hikaye modu + ayrışma bölümü.
- Tur: 180 m spot halka, piksel-hassas odak (moveend+panBy), diğer nokta dimleme, jeton koruması.
- Denetim 44/44, paket 95 dosya.

## v1.0.0 — pilot teslim (2026-09-16)

- V-R-S çekirdek model, 48 kontrol + 8 OSM taslak aday, H1/H2/H3 pilot hükmü.
- AHP gerekçesi (CR 0.008), M2 erişim, OWA, kümülatif görüş, deniz-seviyesi notu.
- QGIS projesi, web atlası v1, tekrar-üretim paketi, 39/39 denetim.
