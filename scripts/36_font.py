"""36 — Self-host fontlar: Google Fonts woff2 indir + @font-face.

Aileler (OFL): Archivo 400,600,800 + Caveat 500,600 + IBM Plex Mono 400,500
(latin altkume). Dogrulama: wOF2 sihiri + >8 KB; basarisizsa HTML'deki
Google <link> korunur (cevrimdisi garantisi yok). Basariliysa link kaldirilir.
"""
from pathlib import Path
import re
import requests

ROOT = Path(__file__).resolve().parents[1]
F = ROOT / "web" / "fonts"
F.mkdir(exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

AILELER = {"Archivo": [400, 600, 800], "Caveat": [500, 600], "IBM Plex Mono": [400, 500]}
beklenen = [f"{a.replace(' ', '+')}-{w}.woff2" for a, agir in AILELER.items() for w in agir]
css_yolu = ROOT / "web" / "styles.css"
if all((F / fn).exists() for fn in beklenen) and "self-host OFL (36)" in css_yolu.read_text(encoding="utf-8"):
    print("zaten self-host; atlandi")
    raise SystemExit(0)
css_parca = []
ok = True
for ad, agir in AILELER.items():
    fam = ad.replace(" ", "+")
    for w in agir:
        url = f"https://fonts.googleapis.com/css2?family={fam}:wght@{w}&display=swap"
        css = requests.get(url, headers=UA, timeout=60).text
        m = re.search(r"/\* latin \*/\s*@font-face\s*{[^}]*url\((https://[^)]+\.woff2)\)", css)
        if not m:
            print("BULUNAMADI", ad, w); ok = False; continue
        b = requests.get(m.group(1), headers=UA, timeout=60).content
        if not (b[:4] == b"wOF2" and len(b) > 8000):
            print("BOZUK", ad, w); ok = False; continue
        fn = f"{fam}-{w}.woff2"
        (F / fn).write_bytes(b)
        css_parca.append(
            f"@font-face{{font-family:'{ad}';font-style:normal;font-weight:{w};"
            f"font-display:swap;src:url(fonts/{fn}) format('woff2');}}")
        print("OK", ad, w, len(b) // 1024, "KB")
(F / "OFL_NOTU.txt").write_text(
    "Fontlar OFL lisanslidir: Archivo, Caveat, IBM Plex Mono (Google Fonts).\n"
    "Lisans metinleri icin OFL (https://openfontlicense.org).", encoding="utf-8")

if ok:
    css_yolu = ROOT / "web" / "styles.css"
    txt = css_yolu.read_text(encoding="utf-8")
    txt = "/* self-host OFL (36) */\n" + "\n".join(css_parca) + "\n" + txt
    css_yolu.write_text(txt, encoding="utf-8")
    html = ROOT / "web" / "index.html"
    ht = html.read_text(encoding="utf-8")
    ht2 = re.sub(r'<link href="https://fonts\.googleapis[^>]*>\n', "", ht)
    assert ht2 != ht
    html.write_text(ht2, encoding="utf-8")
    print("-> @font-face eklendi, Google <link> kaldirildi (cevrimdisi hazir)")
else:
    print("EKSIK VAR: link korundu")
