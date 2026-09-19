"""07 — Belirsizlik: sinirli senaryo matrisi + kararli/yuksek okuma sinifi.

Rapor karsiligi: §09, [10]. Ciktilar: senaryo_tablosu.csv, kararlilik.csv,
belirsizlik_matrisi.png. Once matris; dagilim gerekceliyse Monte Carlo (izlenir).
"""
from pathlib import Path
import itertools
import numpy as np, pandas as pd, yaml
ROOT = Path(__file__).resolve().parents[1]
BEL = ROOT / "07_belirsizlik"; BEL.mkdir(exist_ok=True)
P = yaml.safe_load(open(ROOT / "params" / "model.yaml", encoding="utf-8"))
tab = pd.read_csv(ROOT / "05_olcut_model" / "model_tablosu.csv")

sen = []
agir = dict(P["agirliklar"]); agir["drop_R"] = {"wV": 0.5, "wR": 0.0, "wS": 0.5}
for ad, w in agir.items():
    tab[f"tmp_{ad}"] = w["wV"] * tab["fV"] + w["wR"] * tab["fR"] + w["wS"] * tab["fS"]
senaryolar = list(agir)
# Gozlemci yuksekligi etkisi: fV'ye kucuk deterministik duzeltme (protokol senaryosu;
# tam yeniden-hesap K3'te gdal_viewshed ile yapilir, burada yaklasik band)
for h in P["gorus"]["yapı_senaryolari_m"]:
    tab[f"tmp_h{h:g}"] = tab["tmp_esit"] + 0.01 * (h - P["gorus"]["gozlemci_yuksekligi_m"])
    senaryolar.append(f"h{h:g}")
S = tab[[f"tmp_{s}" if not s.startswith("h") else f"tmp_{s}" for s in senaryolar]]
S.columns = senaryolar
S.to_csv(BEL / "senaryo_tablosu.csv", index=False)

ust = S.apply(lambda c: c >= c.quantile(0.8))
karar = pd.DataFrame({"nok_id": tab["nok_id"], "U_esit": tab["U_esit"].round(4),
    "kararlilik": ust.mean(axis=1).round(3)})
med = tab["U_esit"].median()
def sinif(r):
    return ("yuksek/kararli" if r.U_esit >= med and r.kararlilik >= .6 else
            "yuksek/degisken" if r.U_esit >= med else
            "dusuk/kararli" if r.kararlilik >= .6 else "dusuk/degisken")
karar["okuma_sinifi"] = karar.apply(sinif, axis=1)
karar.to_csv(BEL / "kararlilik.csv", index=False)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(7, 5))
for k, g in karar.groupby("okuma_sinifi"):
    ax.scatter(g["U_esit"], g["kararlilik"], label=k)
ax.set_xlabel("Uygunluk puani (U_esit)"); ax.set_ylabel("Kararlilik (ust-sinifta kalma sikligi)")
ax.set_title("Sonuclari okuma matrisi (Sekil 2 uygulamasi)")
ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(BEL / "belirsizlik_matrisi.png", dpi=150)
print(karar["okuma_sinifi"].value_counts().to_string())
print("-> senaryo_tablosu.csv + kararlilik.csv + belirsizlik_matrisi.png")
