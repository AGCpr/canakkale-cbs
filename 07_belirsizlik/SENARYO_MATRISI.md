# Senaryo matrisi — belirsizlik ve yorum (rapor §09)

**"Uygun" ve "kararlı" aynı şey değildir.** İki çıktı: göreli uygunluk puanı + senaryolarda yüksek sınıfta kalma sıklığı.

## Dört aile (`scripts/07_belirsizlik.py`)

1. **Ağırlık ve puanlama:** eşit/uzman ağırlıkları; alternatif dönüşüm eğrileri; ilişkili ölçütü çıkarma.
2. **Arazi ve ölçek:** alternatif yükselti verisi; daha kaba ortak çözünürlük (60/90 m); değişmiş arazi maskesi.
3. **Görüş ve konum:** yapı yüksekliği senaryoları; tarihsel konum hata çevresi; sabit hedef alanı.
4. **Tarihsel kayıt:** dönem/işlev belirsizliği; belgeli kayıp yapılar; yalnız yüksek güvenli alt küme.

## Sonuç okuma matrisi (Şekil 2)

| | Kararlı | Değişken |
|---|---|---|
| **Yüksek puan** | Ek tarihsel inceleme için güçlü aday | Tek senaryodaki yüksek puana dayanma |
| **Düşük puan** | Ölçütlere göre sürekli düşük uygunluk | Veri ve model varsayımlarını gözden geçir |

Üst sıra daha kararlı; sağ sütun daha yüksek puan. Kararlılık seçilmiş senaryo kümesine koşulludur.

## Kural

Önce sınırlı senaryo matrisi; dağılımlar gerekçelendirilebiliyorsa Monte Carlo. Yakınsama izlenir, tekrar sayısı kaydedilir [10].

## Deniz-seviyesi notu (22)

Hedef −1 m senaryosu **dejenere protokoldür**: hedef su yüzeyinin altına indiği için geometri gereği ~0 görünürlük üretir; kıyı-değişimi vekili olarak KULLANILMAZ, kararlılığa katılmaz. Geçerli kıyı duyarlılığı: kara-eşik senaryosu (`kıyı_eşik_dışı` bayrağı) + konum hata çevresi. +1 m sonucu t0 ile özdeştir (değişim <0.002).
