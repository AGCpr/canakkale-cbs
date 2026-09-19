# Model kartı — U(x) çekirdek model (rapor §06)

**Uygunluk puanı bir sıralama aracıdır. Nedensel açıklama veya tarihsel seçim olasılığı değildir.**

## Ölçütler

- **V · Boğaz görünürlüğü:** görülen su alanı / sabit toplam hedef alanı. Tüm adaylarda aynı hedef yüksekliği ve görüş protokolü.
- **R · Göreli yükselti:** R = nokta yüksekliği − çevre ortalaması. Yarıçap pilotta {500, 1000, 2000} m ile sınanır.
- **S · Yerel eğim:** yapı oturumu ile ilişkili eğim puanı. "Daha az eğim her zaman daha iyi" varsayımı belgelenir veya değiştirilir.

## Formül

`U(x) = wV·fV(x) + wR·fR(x) + wS·fS(x)` — f: 0–1 dönüşüm; ağırlıklar ≥0 toplam 1; x: geçerli kara hücresi/aday.

## Geliştirme kuralları

1. Eşit ağırlık temel karşılaştırmadır; uzman ağırlığı ikinci senaryodur.
2. Dönüşüm eşikleri literatür + işlev bilgisiyle belirlenir; tarihsel nokta puanını yükseltmek için ayarlanmaz.
3. Görüş–yükselti ilişkili ise birini çıkaran model de çalıştırılır [4,10].
4. Eksik veri 0 puan kodlanmaz (maskelenir).
5. Öğretici hesap (saha verisi değildir): fV=0.80, fR=0.60, fS=0.40 → eşit ağırlık U=0.60; bu "%60 seçilme olasılığı" demek değildir.

## Model kıyası

M0 = yalnız görüş; M1 = üç ölçüt; M2 = gerekçeli ekler. H2, aynı sınama gruplarında M0–M1 karşılaştırmasıyla değerlendirilir.
