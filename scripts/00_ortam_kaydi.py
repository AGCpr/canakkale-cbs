"""00 — Ortam kaydi: QGIS/GDAL/Python surumlerini logs/ altina yazar."""
import datetime, platform, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "logs"
LOG.mkdir(exist_ok=True)

def cmd(v):
    try:
        p = subprocess.run(v, capture_output=True, text=True, timeout=20)
        return (p.stdout or p.stderr or "").strip().splitlines()[:3]
    except Exception as e:
        return [f"yok ({e})"]

lines = [f"zaman_utc: {datetime.datetime.utcnow().isoformat()}Z",
         f"platform: {platform.platform()}",
         f"python: {sys.version.splitlines()[0]}"]
for pkg in ["numpy", "pandas", "rasterio", "geopandas", "scipy", "sklearn", "matplotlib", "yaml"]:
    try:
        m = __import__(pkg)
        lines.append(f"{pkg}: {getattr(m, '__version__', '?')}")
    except Exception as e:
        lines.append(f"{pkg}: KURULU_DEGIL ({e})")

qgis_gdal = Path(r"C:\Program Files\QGIS 4.2.2\bin")
for exe, args in [("gdalinfo.exe", ["--version"]), ("gdal_viewshed.exe", ["--version"]),
                  ("gdaldem.exe", ["--version"]), ("qgis-bin.exe", ["--version"])]:
    p = qgis_gdal / exe
    if p.exists():
        lines.append(f"{exe}: {' | '.join(cmd([str(p)] + args))}")
    else:
        lines.append(f"{exe}: bulunamadi")
lines.append(f"PATH gdalinfo: {shutil.which('gdalinfo') or 'yok'}")

out = LOG / "ortam.txt"
out.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
print(f"\n-> {out}")
