"""37 — Bogaz genislik kesitleri: hat boyunca 1 km'de su genisligi.

Yontem: hat cizgisi uzerinde her 1 km'de dik dogrultuda ±6 km tara;
kesintisiz su parcasi genisligi. Tarihsel islev belgesiz "stratejik ustunluk"
puani uretilmez; yalnizca baglam katmani.
Cikti: 03_veri/islenmis/genislik_kesitleri.csv
"""
from pathlib import Path
import numpy as np, pandas as pd
import rasterio
from shapely.geometry import LineString
from pyproj import Transformer
from shapely.ops import transform as _t

ROOT = Path(__file__).resolve().parents[1]
ISL = ROOT / "03_veri" / "islenmis"
with rasterio.open(ISL / "su_maske.tif") as d:
    su = d.read(1) == 1
    trF = d.transform; res = abs(trF.a)
hat = LineString([(26.05, 39.95), (26.35, 40.25), (26.65, 40.45), (26.95, 40.62)])
# Duzeltme: ham 4-kose hat karaya oturur (D9). cba su-ici ekseni kullanilir (kaynakli).
import json as _js
_cba = _js.load(open(r"C:\Users\AGC\OneDrive\Masaüstü\cba\02_Arastirma\04_kayitlar\bolgesel_geometri.json",
                     encoding="utf-8"))
_hat = _cba.get("axis_lonlat")
if _hat and len(_hat) > 4:
    hat = LineString(_hat)
    print(f"cba ekseni kullanildi ({len(_hat)} nokta)")
else:
    print("UYARI: ham hat kullanildi (eksik cba ekseni)")
T = Transformer.from_crs("EPSG:4326", "EPSG:32635", always_xy=True).transform
hatm = _t(lambda x, y: T(x, y)[:2], hat)
Tg = Transformer.from_crs("EPSG:32635", "EPSG:4326", always_xy=True).transform

def hucren(X, Y):
    return int((trF.f - Y) / res - 0.5), int((X - trF.c) / res - 0.5)

sat = []
d = 0.0
while d <= hatm.length:
    p = hatm.interpolate(d)
    p0 = hatm.interpolate(max(d - 100, 0)); p1 = hatm.interpolate(min(d + 100, hatm.length))
    dx, dy = p1.x - p0.x, p1.y - p0.y
    L = max(np.hypot(dx, dy), 1e-9)
    nx, ny = -dy / L, dx / L
    gen = []
    for s in np.arange(-6000, 6001, 30):
        X, Y = p.x + nx * s, p.y + ny * s
        r, c = hucren(X, Y)
        if 0 <= r < su.shape[0] and 0 <= c < su.shape[1] and su[r, c]:
            gen.append(s)
    if gen:
        gen = np.array(gen)
        # hat noktasini iceren kesintisiz parcayi al
        su_dolu = np.zeros(401, bool)
        su_dolu[((gen + 6000) / 30).astype(int)] = True
        i0 = 200
        a = i0
        while a > 0 and su_dolu[a - 1]:
            a -= 1
        b = i0
        while b < 400 and su_dolu[b + 1]:
            b += 1
        genis = (b - a + 1) * 30 if su_dolu[i0] else 0
    else:
        genis = 0
    lo, la = Tg(p.x, p.y)[:2]
    sat.append({"km": round(d / 1000, 1), "lon": round(lo, 4), "lat": round(la, 4),
                "genislik_m": int(genis)})
    d += 1000
df = pd.DataFrame(sat)
df.to_csv(ISL / "genislik_kesitleri.csv", index=False)
print(f"kesit: {len(df)}, min/med/maks: {df.genislik_m.min()}/{int(df.genislik_m.median())}/{df.genislik_m.max()} m")
