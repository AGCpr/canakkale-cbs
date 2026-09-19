"""08 — Atlas: baglam + olcut + uygunluk + kararlilik haritalari (PNG) + GPKG.

Rapor karsiligi: §11 cikti 01/02/04. QGIS duzeni icin katmanlar ayrica
09_teslim/canakkale_cbs.gpkg icinde toplanir (betik 09).
"""
from pathlib import Path
import numpy as np, pandas as pd, yaml
ROOT = Path(__file__).resolve().parents[1]
AT = ROOT / "09_teslim"; AT.mkdir(exist_ok=True)
import rasterio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

P = yaml.safe_load(open(ROOT / "params" / "model.yaml", encoding="utf-8"))
def oku(p):
    with rasterio.open(p) as d:
        return d.read(1).astype(float), d.transform
dem, tr = oku(ROOT / "03_veri" / "islenmis" / "dem_30m_32635.tif")
egim, _ = oku(ROOT / "05_olcut_model" / "egim_derece.tif")
fR, _ = oku(ROOT / "05_olcut_model" / "fR.tif")
U = {}
for k in ("esit", "uzman_gorus_agirlikli"):
    try: U[k], _ = oku(ROOT / "05_olcut_model" / f"U_raster_{k}.tif")
    except Exception: pass
tab = pd.read_csv(ROOT / "05_olcut_model" / "model_tablosu.csv")
kar = pd.read_csv(ROOT / "07_belirsizlik" / "kararlilik.csv") if (ROOT/"07_belirsizlik"/"kararlilik.csv").exists() else None

def harita(arr, ad, baslik, vmin=None, vmax=None, c="terrain"):
    fig, ax = plt.subplots(figsize=(8, 6))
    m = np.ma.masked_invalid(np.asarray(arr, dtype=float))
    fin = m.compressed()
    if vmin is None: vmin = float(np.percentile(fin, 2))
    if vmax is None: vmax = float(np.percentile(fin, 98))
    im = ax.imshow(m, cmap=c, vmin=vmin, vmax=vmax)
    fig.colorbar(im, ax=ax, shrink=.7)
    ax.set_title(f"{baslik}\n(EPSG:32635 · 30 m · {Path(ad).name})", fontsize=10)
    ax.set_xticks([]); ax.set_yticks([])
    fig.tight_layout(); fig.savefig(AT / ad, dpi=150); plt.close(fig)

harita(dem, "harita_dem.png", "Arazi yukseltisi + su hedef alani (pilot)")
harita(egim, "harita_egim.png", "Yerel egim (derece)", c="YlOrBr")
harita(fR, "harita_fR.png", "Goreli yukselti puani fR", vmin=0, vmax=1, c="RdYlGn")
if "esit" in U:
    harita(U["esit"], "harita_U_esit.png", "Uygunluk bileseni (fR+fS, esit) + nokta fV tabloda", vmin=0, vmax=1, c="viridis")
fig, ax = plt.subplots(figsize=(8, 6))
m = np.ma.masked_invalid(np.asarray(dem, dtype=float)); ax.imshow(m, cmap="terrain",
    vmin=np.nanpercentile(m,2), vmax=np.nanpercentile(m,98))
sc = ax.scatter(tab.index, tab["U_esit"], c=tab["fV"], cmap="Blues", s=18)
fig.colorbar(sc, ax=ax, label="fV"); ax.set_title("Degerlendirme noktalari: U_esit (renk=fV)")
ax.set_xticks([]); ax.set_yticks([]); fig.tight_layout()
fig.savefig(AT / "harita_noktalar.png", dpi=150); plt.close(fig)
print("-> 09_teslim/harita_*.png")
