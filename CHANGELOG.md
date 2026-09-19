# Değişiklik günlüğü

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
