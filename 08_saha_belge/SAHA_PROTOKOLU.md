# Saha / belge kontrolü (hafta 7) — çalışma listesi

Amaç: envanterdeki her `dogrulanacak` satırı `yuksek/orta` güvene taşımak ya da gerekçesiyle düşük bırakmak.

## Adım adım

1. `[18] Alan Başkanlığı envanteri`nden adı bul; özgün geometriyi (nokta/poligon) kaydet.
2. Dönem haritasını QGIS Georeferencer ile koordinatlandır (sabit kontrol noktaları + bağımsız RMSE, metre) [16].
3. `[1,2]` yayınlarındaki ad-varyantlarını eşleştir; taşınma/yeniden-yapım varsa **yeni satır** aç (tek ad=tek yapı yok).
4. `lon/lat + konum_guven + hata_yaricapi_m + durum` doldur; boş bırakmak yasak.
5. Kayıp/belgeli-yıkık yapıları silme — `durum=kayip_belgeli` olarak tut (korunma yanlılığı önlemi).
6. Her yapı-evresi için zaman zincirini kapat: ilk_inşa → yeniden_düzenleme → kullanim_1915 → bugunku_iz.
7. Bu klasöre tarama/Haritanın künyesini işle: `SAHA_LOG.md` (tarih, kaynak, hata, eksik).

## Çıktı

- Dolu `02_envanter/envanter.csv` → doğrulama sonrası `scripts/04` aynı protokolle gerçek noktalara da V/R/S hesaplar,
  `scripts/06` kip=GERCEK ile çalışır, K3 kapanır.
