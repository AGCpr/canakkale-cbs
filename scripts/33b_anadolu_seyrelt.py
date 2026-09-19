"""33b — Anadolu seyreltme: 16 kume-ici noktadan 4 tabakali nokta.

Gerekce: 16 noktanin tamami 900x720 m tek cepte (Nara); ayni gorus
penceresi -> fV ozdes (0.0043). 16 gozlem gibi saymak yalanci cogaltmadir
(rapor §08: yakinlik bagimsiz kanit sayilmaz). X'e gore sirala, 4'lu al.
Ham 16 satir olcut_anadolu_ek.csv'de korunur.
"""
import pandas as pd
import geopandas as gpd

ROOT = "."
t = pd.read_csv("05_olcut_model/olcut_tablosu.csv")
g = gpd.read_file("05_olcut_model/ornek_noktalar.gpkg")
mask = t["nok_id"].str.startswith("A")
havuz = t[mask].copy()
havuz["X"] = [p.x for p in g.set_index("nok_id").loc[havuz["nok_id"], "geometry"]]
havuz = havuz.sort_values("X").reset_index(drop=True)
tut = havuz.iloc[[1, 5, 9, 13]]
print(tut[["nok_id", "X", "fV", "R"]].to_string(index=False))
t = pd.concat([t[~mask], tut.drop(columns=["X"])], ignore_index=True)
t.to_csv("05_olcut_model/olcut_tablosu.csv", index=False)
g = pd.concat([g[~g["nok_id"].str.startswith("A")],
               g[g["nok_id"].isin(tut["nok_id"])]], ignore_index=True)
g.to_file("05_olcut_model/ornek_noktalar.gpkg", driver="GPKG")
print(f"-> kontroller: {len(t)} (48 Avrupa + 4 Anadolu-Nara)")
