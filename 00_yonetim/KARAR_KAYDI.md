# Karar Kaydı — yöntem önerisinden uygulamaya

Tarih: 16 Eylül 2026 sonrası uygulama. Her karar: rapor dayanağı + uygulama karşılığı + ihlal koşulu.

## D1. Ana çalışma ortamı: QGIS + GRASS, istatistik R/Python

- Dayanak: Rapor §01 Karar kutusu.
- Uygulama: CRS ve raster işlemleri GDAL (`gdalwarp`, `gdaldem`, `gdal_viewshed`) ile; QGIS proje dosyası `qgis/` altında; istatistik `scripts/06-07`.
- Sürüm kaydı zorunlu: `logs/run_*.log` içine QGIS/GDAL/Python sürümü yazılır (`scripts/00_ortam_kaydi.py`).

## D2. Ana model: ağırlıklı toplam + sürekli/bulanık puan [4]

- Formül: `U(x) = wV·fV(x) + wR·fR(x) + wS·fS(x)`, w≥0, Σw=1, x geçerli kara hücresi.
- Eşik/dönüşüm önceden kaydedilir (`params/model.yaml`); tarihsel nokta puanını yükseltmek için ayarlanmaz.
- Karşılaştırma: M0=yalnız görüş, M1=üç ölçüt, M2=gerekçeli ekler. H2, aynı sınama gruplarında M0–M1 ile değerlendirilir.

## D3. Yöntemlere açık görev (tek "en iyi" yok)

| Yöntem | Görev | Durum |
|---|---|---|
| Ağırlıklı toplam | Ana model | Uygulanır |
| AHP / uzman ağırlıkları | Ağırlık senaryosu; tutarlılık + uzman ayrışması raporlanır [4] | Senaryo olarak |
| Kümülatif görüş / görünürlük ağı | Tamamlayıcı; görsel bağlantı ≠ haberleşme kanıtı [5,7] | Tamamlayıcı |
| Maliyetli mesafe (r.walk) | Dönem yolu/iskele varsa; yoksa ayrı senaryo [6] | Veriye bağlı |
| Lojistik/GAM/RF | İkinci aşama; yeterli bağımsız örnek + mekânsal sınama şart [8,9] | K3 sonrası, yeterli örnekte |
| OWA | İsteğe bağlı sağlamlık; uyuşmazlık açıklanır [4,10] | İsteğe bağlı |

## D4. Gözlenmeyen yer ≠ yokluk

- Envanterde kayıt olmaması "orada hiç yapı yoktu" demek değildir. Öğrenen model çıktısı tarihsel seçilme olasılığı diye yorumlanmaz.

## D5. CRS ve ortak grid

- Kaynak CRS: EPSG:4326. Çalışma CRS: EPSG:32635 (UTM 35N, metre tabanlı; raporun önerdiği seçenek).
- Ortak çözünürlük: 30 m (DEM yerli çözünürlüğü). 5 m'ye örnekleme yasaktır (D-kritik-3).
- Deniz/kara/boş veri ayrı tutulur; düşey referans ve datum `03_veri/VERI_KATALOGU.md` içinde kayıtlı.

## D6. Görüş protokolü (tüm adaylarda sabit)

- Gözlemci yüksekliği: senaryo (varsayılan 4 m + yapı senaryoları 2/6/10 m).
- Hedef yüksekliği: deniz seviyesi 0 m (deniz tabanı değil).
- Eğrilik + kırılma (refraksiyon katsayısı 0.13), mesafe sınırı (varsayılan 15 km, boğaz ölçeğine uygun), arazi tamponu.
- Hedef alan: ortak su poligonu (tarihi belli kıyı çizgisinden türetilir; dönem farkları ayrı).
- fV = görülen su hücresi / toplam su hedef hücresi.

## D7. Göreli yükselti ve eğim

- R = z − çevre ortalaması; yarıçaplar {500, 1000, 2000} m ile sınanır (pilot).
- S puanı: yapı oturumu ile ilişkili eğim; "az eğim her zaman iyi" varsayımı `params/model.yaml` içinde belgelenir veya değiştirilir.
- Görüş–yükselti ilişkili ise birini çıkaran model de çalıştırılır.

## D9. Yaka teşhisi: çizgi değil kara bileşeni

- İlk uygulama hat çizgisine izdüşümdü; kaba 4-köşe hat karaya oturduğu için yanlış yaka üretti (9 noktalı testte 3 hata).
- Kural: koridor DEM kara maskesinin bağlantılı bileşenleri; tohumlar Kilitbahir=Avrupa, Çanakkale-şehir=Anadolu. 9/9 doğrulandı.
- Sayısal etki: eşleşme yalnızca eşitliğe dayandığından eski H sonuçları değişmedi (12 yeniden koşuldu, n_k 12→11); etiketler düzeltildi.

## D10. Tek-yaka denetimi ve düzeltme

- 48 kontrolün tamamı Avrupa çıktı. Örnekleme hatası değil: koridor-içi Anadolu şeridi maskenin %0,05'i (577 hücre) — beklenen sonuç.
- Düzeltme: aynı dar-maske kuralıyla 16 Anadolu noktası örneklendi; 900×720 m tek cepte yığıldıkları için yalancı çoğaltmayı önlemek adına 4 tabakalı nokta tutuldu (A002,A005,A006,A010 → raporda A-kümesi). Ölçek donduruldu (p5/p95 ilk 48'den).
- Sonuç: 52 kontrol (48+4); R04 artık eşleşebilir. Etki: 12/26/32 yeniden koşuldu.

## D8. Karşılaştırma ve belirsizlik dili

- Kontroller aynı kıyı kesimi + benzer kıyı uzaklığından; sınanan özelliklere göre eşleştirme yok.
- Blok büyüklüğü ezber mesafeyle değil mekânsal bağımlılık + örnek dağılımıyla belirlenir.
- Çıktılar daima çift: (1) göreli uygunluk puanı, (2) senaryolarda üst-sınıfta kalma sıklığı (kararlılık).
- Kararlılık = seçilmiş senaryo kümesine koşullu; istatistiksel güven veya seçilme olasılığı değildir.
