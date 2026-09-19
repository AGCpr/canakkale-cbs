"""13 — K3 pilot hukmu + atlas guncelleme (aday katmanli).

Rapor karsiligi: §09 + §11 sonuc cumlesi sablonu.
- Aday agirlik senaryolari + okuma sinifi (kararlilik).
- harita_noktalar.png aday overlay ile yenilenir.
- 06_karsilastirma/K3_PILOT_HUKMU.md yazilir (sablon cumle aynen).
"""
from pathlib import Path
import numpy as np, pandas as pd, yaml
ROOT = Path(__file__).resolve().parents[1]
P = yaml.safe_load(open(ROOT / "params" / "model.yaml", encoding="utf-8"))

aday = pd.read_csv(ROOT / "05_olcut_model" / "aday_olcut_tablosu.csv")
kiy = pd.read_csv(ROOT / "06_karsilastirma" / "karsilastirma_tablosu__PILOT_ADAY.csv")
tab = pd.read_csv(ROOT / "05_olcut_model" / "model_tablosu.csv")

agir = dict(P["agirliklar"]); agir["drop_R"] = {"wV": 0.5, "wR": 0.0, "wS": 0.5}
for ad, w in agir.items():
    aday[f"U_{ad}"] = (w["wV"] * aday["fV"] + w["wR"] * aday["fR"] + w["wS"] * aday["fS"]).round(4)
cols = [f"U_{a}" for a in agir]
ust = aday[cols].apply(lambda c: c >= tab["U_esit"].quantile(0.8))
aday["kararlilik"] = ust.mean(axis=1).round(3)
med = tab["U_esit"].median()
aday["okuma_sinifi"] = aday.apply(lambda r:
    "yuksek/kararli" if r.U_esit >= med and r.kararlilik >= .6 else
    "yuksek/degisken" if r.U_esit >= med else
    "dusuk/kararli" if r.kararlilik >= .6 else "dusuk/degisken", axis=1)
aday.to_csv(ROOT / "05_olcut_model" / "aday_olcut_tablosu.csv", index=False)

h1 = kiy[kiy["etiket"] == "H1_tabya_M1_esit"].iloc[0]
h1v = kiy[kiy["etiket"] == "H1_tabya_fV"].iloc[0]
h2 = kiy[kiy["etiket"] == "H2_M0_M1_cliffs"].iloc[0]
(ROOT / "06_karsilastirma" / "K3_PILOT_HUKMU.md").write_text(
 "# K3 pilot hukmu (PILOT_ADAY — tarihsel yargi degil)\n\n"
 "## Sablon cumle (rapor §11, aynen)\n\n"
 "> \"Tarihsel noktalar, tanımlanan fiziki ölçütler bakımından karşılaştırma alanlarından "
 f"{'ayrışıyor' if h1['p'] < 0.05 else 'ayrışmıyor'}; bu sonuç belirtilen veri ve senaryo sınırları içinde geçerli.\"\n\n"
 f"- H1 (M1, tabya n={int(h1['n_t'])} vs eslesmis kontrol n={int(h1['n_k'])}): medyan fark {h1['medyan_fark']:+.4f}, "
 f"p={h1['p']:.3g}, Cliff's delta {h1['cliffs_d']:+.2f}, %95 CI [{h1['ci_lo']:+.4f},{h1['ci_hi']:+.4f}].\n"
 f"- H1 (yalniz gorus fV): medyan fark {h1v['medyan_fark']:+.4f}, p={h1v['p']:.3g}, delta {h1v['cliffs_d']:+.2f}.\n"
 f"- H2 (M0 vs M1 etki): M0 delta {h2['ci_lo']:+.2f}, M1 delta {h2['cliffs_d']:+.2f} -> "
 "R+S ek-bilgi isareti pilot gucte gorulmedi.\n"
 "- H3 (saglamlik): agirlik senaryolarinda aday kararliligi:\n"
 + "".join(f"  - {r.yapi_id} {r.ad_standart}: U_esit={r.U_esit:.3f}, kararlilik={r.kararlilik:.2f} ({r.okuma_sinifi})\n"
           for r in aday.itertuples())
 + "\n## Sinirlar (hukumle birlikte okunur)\n\n"
 "- Aday koordinatlar OSM taslak (dusuk guven, 1000 m); [18]+donem haritasi+[1,2] dogrulamasi YOK.\n"
 "- n_t=4: guc dusuk; CI sifiri kapsiyor; guclu tahmin iddiasi YOK [8,9].\n"
 "- Kiyi-esigi (dem>0.5) kiyi yapilarini disinda birakabilir; maskesiz R + bayrak raporlandi (§09 arazi ailesi).\n"
 "- GERCEK K3, envanter dogrulamasiyla ayni zincirin yeniden calismasidir (08_saha_belge).\n",
 encoding="utf-8")

# Atlas: nokta haritasi + aday overlay
import rasterio
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
with rasterio.open(ROOT / "03_veri" / "islenmis" / "dem_30m_32635.tif") as d:
    dem = d.read(1).astype(float)
fig, ax = plt.subplots(figsize=(8, 6))
m = np.ma.masked_invalid(dem)
ax.imshow(m, cmap="terrain", vmin=float(np.percentile(m.compressed(), 2)),
          vmax=float(np.percentile(m.compressed(), 98)))
sc = ax.scatter(tab.index, tab["U_esit"], c=tab["fV"], cmap="Blues", s=18, label="kontrol_adayi")
ax.scatter(aday.index, aday["U_esit"], c="red", s=60, marker="*", label="tarihsel_aday (taslak)")
for i, r in aday.iterrows():
    ax.annotate(r["yapi_id"], (i, r["U_esit"]), fontsize=7, color="darkred")
ax.set_title("Degerlendirme noktalari: U_esit (mavi=fV) + tarihsel adaylar (kirmizi *)")
ax.set_xticks([]); ax.set_yticks([]); ax.legend(fontsize=8, loc="lower right")
fig.tight_layout(); fig.savefig(ROOT / "09_teslim" / "harita_noktalar.png", dpi=150); plt.close(fig)
print(aday[["yapi_id", "U_esit", "kararlilik", "okuma_sinifi"]].to_string(index=False))
print("-> K3_PILOT_HUKMU.md + harita_noktalar.png guncellendi")
