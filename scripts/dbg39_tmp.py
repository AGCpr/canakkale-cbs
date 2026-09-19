"""Gecici: 39 serit tanisi."""
import numpy as np, rasterio, geopandas as gpd
from rasterio.features import rasterize
from scipy import ndimage
from pyproj import Transformer
with rasterio.open("05_olcut_model/koridor_dem.tif") as d:
    tr = d.transform; res = abs(tr.a); H, W = d.height, d.width
with rasterio.open("03_veri/islenmis/dem_30m_32635.tif") as d:
    trF = d.transform; HF, WF = d.height, d.width
with rasterio.open("03_veri/islenmis/kara_maske.tif") as d:
    karaF = d.read(1) == 1
kor = gpd.read_file("03_veri/islenmis/koridor.gpkg")
kg = kor.loc[kor["ad"] == "koridor_8km", "geometry"].iloc[0]
km = rasterize([(kg, 1)], out_shape=(HF, WF), transform=trF, fill=0, dtype="uint8") == 1
rows = np.where(km.any(axis=1))[0]; cols = np.where(km.any(axis=0))[0]
r0, r1, c0, c1 = rows.min(), rows.max() + 1, cols.min(), cols.max() + 1
kara_dar = karaF[r0:r1, c0:c1] & km[r0:r1, c0:c1]
print("kara_dar shape:", kara_dar.shape, "beklenen:", (H, W))
lab, n = ndimage.label(kara_dar)
print("bilesen:", n)
TT = Transformer.from_crs("EPSG:4326", "EPSG:32635", always_xy=True).transform
Xk, Yk = TT(26.3792, 40.1477)[:2]
rk, ck = int((tr.f - Yk) / res - 0.5), int((Xk - tr.c) / res - 0.5)
print("tohum hucre:", rk, ck, "aralik disinda mi:", not (0 <= rk < H and 0 <= ck < W))
print("AVRUPA id:", lab[rk, ck] if 0 <= rk < H and 0 <= ck < W else "YOK")
er2 = ndimage.binary_erosion(kara_dar, iterations=int(2000 / res))
serit = kara_dar & ~er2
print("serit toplam:", int(serit.sum()))
from collections import Counter
ys, xs = np.where(serit)
print("serit bilesen ilk 5:", Counter(int(lab[y, x]) for y, x in zip(ys[:20000], xs[:20000])).most_common(5))
