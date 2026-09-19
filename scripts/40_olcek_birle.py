"""40 — fR olcek birlestirme: tum satirlar ilk-48 (K) p5/p95 olceginde.

Gerekce: A (33b) 48-olcegiyle, B (39) 52-olcegiyle hesaplanmisti; tek capaya
cekilir (K48: p5/p95). Mevcut 48 K satirinin fR'si degismez (ayni olcek).
Sonrasi: 05-sonrasi zincir yeniden kosar.
"""
import pandas as pd
from pathlib import Path
CIK = Path("05_olcut_model")
t = pd.read_csv(CIK / "olcut_tablosu.csv")
once_fR = t["fR"].copy()
v0 = t.loc[t["nok_id"].str.startswith("K"), "R"].to_numpy(float)
assert len(v0) == 48, len(v0)
lo, hi = float(__import__("numpy").percentile(v0, 5)), float(__import__("numpy").percentile(v0, 95))
t["fR"] = pd.Series(__import__("numpy").clip((t["R"].to_numpy(float) - lo) / max(hi - lo, 1e-9), 0, 1)).round(4)
t.to_csv(CIK / "olcut_tablosu.csv", index=False)
print(f"capa: p5={lo:.2f} p95={hi:.2f}; maks degisim:",
      float((t["fR"] - once_fR).abs().max()))
print("-> fR birlesti")
