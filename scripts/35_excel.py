"""35 — Excel calisma kitabi: tum sonuclar tek dosyada (teslim kitlesi icin).

Cikti: 09_teslim/sonuc-tablolari.xlsx (sayfalar: README, noktalar, tarihsel,
H1, ayrisma, MC, OWA, denizsv, okuma). openpyxl gerekir.
"""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "09_teslim"
CIK = ROOT / "05_olcut_model"
CIKM = ROOT / "06_karsilastirma"
BEL = ROOT / "07_belirsizlik"

with pd.ExcelWriter(T / "sonuc-tablolari.xlsx", engine="openpyxl") as w:
    pd.DataFrame([{"not": "Canakkale CBS pilot sonuclari (pilot; kanit degil). "
                          "Hukum: K3_GERCEK_HUKMU.md. Uretim: scripts/35_excel.py"}]
                 ).to_excel(w, sheet_name="README", index=False)
    pd.read_csv(CIK / "model_tablosu.csv").to_excel(w, sheet_name="noktalar", index=False)
    pd.read_csv(CIK / "kurumsal_olcut.csv").to_excel(w, sheet_name="tarihsel", index=False)
    pd.read_csv(CIKM / "karsilastirma_tablosu__PILOT_ADAY.csv").to_excel(w, sheet_name="H1_pilot", index=False)
    j = json.load(open(CIKM / "gercek_kiyas.json", encoding="utf-8"))
    pd.DataFrame([{"H1_M1_fark": j["H1_M1"]["fark"], "H1_M1_p": j["H1_M1"]["p"],
                   "H1_fV_fark": j["H1_fV"]["fark"], "H1_fV_p": j["H1_fV"]["p"],
                   "pareto_n": j["pareto_n"],
                   "pareto_tabya": ",".join(j["pareto_tabya"])}]).to_excel(w, sheet_name="H1_gercek", index=False)
    pd.DataFrame(j["ablasyon"]).to_excel(w, sheet_name="ablasyon", index=False)
    pd.read_csv(BEL / "mc_aday.csv").to_excel(w, sheet_name="MC", index=False)
    pd.read_csv(CIK / "owa_tablosu.csv").to_excel(w, sheet_name="OWA", index=False)
    pd.read_csv(BEL / "deniz_seviyesi.csv").to_excel(w, sheet_name="denizsv", index=False)
    pd.read_csv(BEL / "kararlilik.csv").to_excel(w, sheet_name="okuma", index=False)
    pd.read_csv(CIK / "aday_olcut_tablosu.csv").to_excel(w, sheet_name="aday_taslak", index=False)
print("-> sonuc-tablolari.xlsx")
