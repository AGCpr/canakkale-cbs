"""24 — HTML yonetici raporu: sayilari CSV'lerden otomatik doldurur.

Cikti: 09_teslim/yonetici_raporu.html (PNG'ler gorece yolla gomulu).
"""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "09_teslim"
k = pd.read_csv(ROOT / "06_karsilastirma" / "karsilastirma_tablosu__PILOT_ADAY.csv")
h1 = k[k["etiket"] == "H1_tabya_M1_esit"].iloc[0]
h1v = k[k["etiket"] == "H1_tabya_fV"].iloc[0]
ad = pd.read_csv(ROOT / "05_olcut_model" / "aday_olcut_tablosu.csv")
og = json.load(open(ROOT / "06_karsilastirma" / "ogrenen_model.json", encoding="utf-8"))
satir = "".join(
    f"<tr><td>{r.yapi_id}</td><td>{r.ad_standart}</td><td>{r.fV:.4f}</td>"
    f"<td>{r.U_esit:.3f}</td><td>{r.kararlilik:.2f}</td><td>{r.okuma_sinifi}</td></tr>"
    for r in ad.itertuples())

(T / "yonetici_raporu.html").write_text(f"""<!DOCTYPE html><html lang="tr"><head><meta charset="utf-8">
<title>Çanakkale CBS — Yönetici Raporu (pilot)</title>
<style>body{{font-family:sans-serif;max-width:900px;margin:auto;padding:16px;color:#123}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #bbb;padding:4px 8px;font-size:14px}}
img{{max-width:100%}}.uyari{{background:#fff7e6;padding:8px;border-left:4px solid #d90}}</style></head><body>
<h1>Çanakkale Boğazı CBS — Yönetici Raporu (pilot)</h1>
<p>Yöntem önerisinin uygulaması. İlke: önce tarihsel bağlam, sonra model, ardından bağımsız sınama.</p>
<div class="uyari"><b>Sınır:</b> Aday koordinatlar OSM taslak (düşük güven); bu rapor yöntem gösterimidir,
tarihsel yargı değildir. Hüküm cümlesi: <b>"Tarihsel noktalar ... ayrışmıyor; bu sonuç belirtilen
veri ve senaryo sınırları içinde geçerli."</b></div>
<h2>H1 — Tabya (n={int(h1.n_t)}) vs eşleşmiş kontrol (n={int(h1.n_k)})</h2>
<ul><li>M1: fark {h1.medyan_fark:+.4f}, p={h1.p:.3g}, delta {h1.cliffs_d:+.2f}, CI [{h1.ci_lo:+.4f},{h1.ci_hi:+.4f}]</li>
<li>Yalnız-görüş: fark {h1v.medyan_fark:+.4f}, p={h1v.p:.3g}</li></ul>
<h2>Adaylar</h2><table><tr><th>ID</th><th>Ad</th><th>fV</th><th>U</th><th>Karar.</th><th>Sınıf</th></tr>{satir}</table>
<h2>Öğrenen model (düşük güç)</h2><p>RF önem: {og["degisken_onem_RF"]} ·
2-katman CV AUC: {og.get("CV2_AUC_logit")} · Blok CV: tek-sınıf (hesaplanamaz).</p>
<h2>Haritalar</h2>
<img src="harita_dem.png"><img src="harita_U_esit.png"><img src="harita_noktalar.png">
<img src="../07_belirsizlik/belirsizlik_matrisi.png">
<p><a href="../web/index.html">İnteraktif atlas (v2)</a> · <a href="NIHAI_RAPOR.md">Nihai rapor</a></p>
</body></html>""", encoding="utf-8")
print("-> yonetici_raporu.html")
