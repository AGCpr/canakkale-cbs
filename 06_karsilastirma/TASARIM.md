# Karşılaştırma tasarımı (rapor §08) — bağımsız sınama

Ana değerlendirme: dönem ve kıyı bağlamı korunmuş **tarihsel–kontrol karşılaştırması**.

## Mantık

- Kontroller aynı kıyı kesimi + benzer kıyı uzaklıklarından; sınanan yükselti/eğim özelliklerine göre eşleştirme yapılmaz.
- Envanterde kayıt olmaması "orada hiç yapı yoktu" demek değildir.
- Ağırlıklar tarihsel veriden öğreniliyorsa geliştirme/sınama alanları coğrafi olarak ayrılır (mekânsal bloklama).
- Blok büyüklüğü sabit ezberle değil mekânsal bağımlılık + örnek dağılımıyla belirlenir. Az bağımsız küme varsa güçlü tahmin iddiası yok [8,9].
- Fiziksel yakınlık benzer puanları bağımsız kanıt gibi gösterir; rastgele eğitim–test bölmesi tek başına çözmez.

## Göstergeler (`scripts/06_karsilastirma.py`)

1. **Etki büyüklüğü:** tarihsel–kontrol medyan farkı + dağılım (Mann-Whitney + Hodges-Lehmann + Cliff's delta).
2. **Yoğunlaşma:** üst uygunluk alanındaki nokta payı / alan payı.
3. **Belirsizlik:** kıyı/küme yapısını koruyan tekrarlı örnekleme (blok/küme bootstrap).

Kontrol alanı ve eşikler analiz öncesi kaydedilir (`params/model.yaml`). Anlamlı ilişki tek başına yer-seçiminin nedeni olduğunu kanıtlamaz.
