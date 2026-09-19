"""06 — Bagimsiz karsilastirma: tarihsel-kontrol; etki + yogunlasma + bootstrap.

Rapor karsiligi: §08, [8,9].
GERCEKLIK NOTU: Envanter koordinatlari henuz bos oldugundan bu betik iki kipte
calisir: (a) koordinat varsa gercek kiyas; (b) yoksa TASARIM DOGRULAMA (simule
nokta kumeleriyle yontem zincirini uctan uca test eder — kanit degil, test).
Cikti dosya adinda kip acikca yazar.
"""
from pathlib import Path
import numpy as np, pandas as pd, yaml
ROOT = Path(__file__).resolve().parents[1]
CIKM = ROOT / "06_karsilastirma"; CIKM.mkdir(exist_ok=True)
P = yaml.safe_load(open(ROOT / "params" / "model.yaml", encoding="utf-8"))
tab = pd.read_csv(ROOT / "05_olcut_model" / "model_tablosu.csv")

import csv
env_yolu = ROOT / "02_envanter" / "envanter.csv"
gercek = []
with open(env_yolu, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        try:
            lon, lat = float(r["lon_wgs84"]), float(r["lat_wgs84"])
            gercek.append((r["yapi_id"], lon, lat))
        except Exception:
            pass

rng = np.random.default_rng(P["tekrar_uretilebilirlik"]["rastgelelik_tohumu"])
if gercek:
    kip = "GERCEK"
    # Gercek nokta degerleri: en yakin ornek noktadan degil, 04'e ayni protokolle
    # yeniden hesaplanmali — burada tablo birlesimi K3 onayi olmadan yapilmaz.
    raise SystemExit("Gercek koordinat bulundu: 04'e ayni gorus protokolunu uygulayip tabloyu genisletin, sonra bu betigi kip=GERCEK ile calistirin.")
else:
    kip = "TASARIM_DOGRULAMA_SIMULASYON"
    n = len(tab)
    # Yontem testi icin iki kume: yuksek-V'li sentetik 'tarihsel' + rastgele 'kontrol'
    th = tab.nlargest(max(8, n // 4), "fV").copy(); th["grup"] = "tarihsel_sim"
    ko = tab.sample(min(len(tab), 24), random_state=20260916).copy(); ko["grup"] = "kontrol_sim"
    veri = pd.concat([th, ko])

for skor in ["M0", "M1_esit"]:
    a = veri.loc[veri.grup.str.startswith("tarihsel"), skor].to_numpy()
    b = veri.loc[veri.grup.str.startswith("kontrol"), skor].to_numpy()
    from scipy.stats import mannwhitneyu
    u, p = mannwhitneyu(a, b, alternative="two-sided")
    # Cliff's delta + Hodges-Lehmann
    d = (np.sum(a[:, None] > b) - np.sum(a[:, None] < b)) / (len(a) * len(b))
    fark = np.median(a) - np.median(b)
    # Yogunlasma: ust %20 alan varsayimiyla nokta payi (alan payi rasterdan)
    esik = veri[skor].quantile(0.8)
    yog = (veri.loc[veri.grup.str.startswith("tarihsel"), skor] >= esik).mean()
    # Kume koruyan bootstrap (tek kume -> basit; gercek veride blok id ile)
    B = 2000; fh = []
    for _ in range(B):
        aa = rng.choice(a, len(a), replace=True); bb = rng.choice(b, len(b), replace=True)
        fh.append(np.median(aa) - np.median(bb))
    lo, hi = np.percentile(fh, [2.5, 97.5])
    print(f"{skor}: medyan_fark={fark:.3f} p={p:.3g} cliffs={d:.2f} yogunlasma={yog:.2f} CI=[{lo:.3f},{hi:.3f}]")

veri.to_csv(CIKM / f"karsilastirma_tablosu__{kip}.csv", index=False)
open(CIKM / "TASARIM_NOTU.md", "w", encoding="utf-8").write(
 f"# Karsilastirma notu ({kip})\n\n- Kontrol kosulu: {P['karsilastirma']['kontrol_kosulu']}.\n"
 f"- Eslesme yasagi: {P['karsilastirma']['eslestirme_yasak']}.\n"
 "- Rastgele egitim-test bolmesi tek basina yetmez; bloklama mekânsal bagimliliga gore belirlenir [8,9].\n"
 + ("- BU CIKTI SIMULASYONDUR; tarihsel yargi icermez.\n" if kip.startswith("TASARIM") else ""))
print(f"-> {kip}")
