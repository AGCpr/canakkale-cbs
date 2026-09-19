# Teslim kontrolü — beş temel çıktı (rapor §11)

Başarı ölçütü güzel harita değil izlenebilir kanıttır.

- [x] 01 Envanter ve dönem haritası — şema + 12 satır ön-envanter (koordinatsız, `dogrulanacak`); zaman zinciri rehberi.
- [x] 02 Ölçüt ve uygunluk atlası — eğim, R(500/1000/2000), fR, fS rasterları + U senaryoları + 5 PNG harita.
- [x] 03 Karşılaştırma tablosu — PILOT_ADAY kipinde (8 OSM taslak; H1/H2/H3 + M2/H2b + öğrenen model); GERÇEK kip K3'te envanter dolunca.
- [x] 04 Kararlılık ve değişim haritası — senaryo matrisi + okuma-sınıfı + belirsizlik_matrisi.png.
- [x] 05 Tekrar-üretim paketi — `canakkale_cbs.gpkg` + rasterlar + `params/model.yaml` + kullanım notu + MANIFEST.sha256 + `cbs_teslim_paketi.zip`.

Kapılar: K1 ✅ Veri hazır (Copernicus GLO-30, 6 karo, 2026-09-16) · K2 ✅ Pilot geçerli (teknik hat) ·
K3 ✅ PİLOT (PILOT_ADAY: H1/H2/H3 taslak adaylarla sınandı, hüküm `06_karsilastirma/K3_PILOT_HUKMU.md`) ·
K3-GERÇEK ⏳ (envanter doğrulamasıyla aynı zincirin tekrarı) · K4 ✅ Teslim paketi üretildi + doğrulandı
(`logs/dogrulama.txt`: 40/40 dosya, manifest 105/105 OK, hata 0; nihai rapor: `09_teslim/NIHAI_RAPOR.md`).

Bu rapor bir uygulama tasarımıdır; gerçek uygunluk/başarı oranı/yeni stratejik alan sonucu K3 geçilmeden yazılmaz.
Başlangıç kararı: dönemi ve kıyı tabyası grubunu kesinleştirin; küçük pilotta veri yeterliliğini sınayın.
