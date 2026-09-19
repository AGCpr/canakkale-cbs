"""05 — Model calistir: U(x) agirlikli toplam; M0/M1; esit+uzman senaryolari.

Rapor karsiligi: §06. Cikti: 05_olcut_model/uygunluk_*.tif + model_tablosu.csv.
Eksik veri 0 kodlanmaz (maske korunur). Esikler tarihsel puana gore ayarlanmaz.
"""
from pathlib import Path
import numpy as np, yaml
ROOT = Path(__file__).resolve().parents[1]
CIK = ROOT / "05_olcut_model"
P = yaml.safe_load(open(ROOT / "params" / "model.yaml", encoding="utf-8"))
import rasterio, pandas as pd

def oku(a):
    with rasterio.open(CIK / a) as d:
        return d.read(1).astype(float), d.meta
fR, meta = oku("fR.tif"); fS, _ = oku("fS.tif")
kara = np.isfinite(fR)  # koridor kirpigi maskesi (fR ile ayni grid)

def yaz(ad, arr):
    m = dict(meta); m.update(dtype="float32", nodata=np.nan, compress="deflate", tiled=True)
    arr = np.where(kara, arr, np.nan).astype(np.float32)
    with rasterio.open(CIK / ad, "w", **m) as d:
        d.write(arr, 1)

tab = pd.read_csv(CIK / "olcut_tablosu.csv")
outs = {}
for ad, w in P["agirliklar"].items():
    U = w["wV"] * tab["fV"] + w["wR"] * tab["fR"] + w["wS"] * tab["fS"]
    tab[f"U_{ad}"] = U.round(4)
    # Raster M1 yaklasimi: fV rastersiz oldugundan fV'nin nokta medyani sabitlenemez;
    # raster U, fR+fS bileseni + nokta fV dagilimi notuyla uretilir (rapor uyarisi korunur).
    Ur = w["wR"] * np.nan_to_num(fR) + w["wS"] * np.nan_to_num(fS)
    Ur = Ur / max(w["wR"] + w["wS"], 1e-9)
    yaz(f"U_raster_{ad}.tif", Ur)
    outs[ad] = w
# M0 (yalniz gorus) vs M1 (uc olcut, esit) nokta kiyasi — H2 girdisi
tab["M0"] = tab["fV"]; tab["M1_esit"] = tab["U_esit"]
tab.to_csv(CIK / "model_tablosu.csv", index=False)
open(CIK / "MODEL_CALISMA_NOTU.md", "w", encoding="utf-8").write(
 "# Model calisma notu\n\n- U(x)=wV·fV+wR·fR+wS·fS; agirliklar params/model.yaml (toplam 1).\n"
 "- Raster U, fR+fS bilesenidir; fV nokta-bazlidir — tam U yuzeyi, seyrek V orneklerinden "
 "enterpole edilmemistir (rapor §07 uyarisi).\n- M0-M1 kiyasi ayni nokta kumesinde yapilir (H2).\n"
 f"- Ogretici kontrol: fV=.8,fR=.6,fS=.4 esit U=.60 (saha verisi degil).\n")
print(tab[[c for c in tab.columns if c.startswith(("M0","M1","U_"))]].describe().to_string())
print("-> model_tablosu.csv + U_raster_*.tif")
