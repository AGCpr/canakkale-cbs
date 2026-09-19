"""41 — PDF rapor: bulgular + haritalar tek belgede (teslim kitle icin).

Kaynak: mevcut CSV/JSON/PNG ciktilari (yeniden hesap yok). Turkce glifler icin
matplotlib DejaVuSans. Cikti: 09_teslim/bulgular.pdf
"""
from pathlib import Path
import json
import pandas as pd
import matplotlib

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "09_teslim"
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image,
                                Table, TableStyle, PageBreak)
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

dej = Path(matplotlib.matplotlib_fname()).parent / "fonts" / "ttf" / "DejaVuSans.ttf"
dejb = Path(matplotlib.matplotlib_fname()).parent / "fonts" / "ttf" / "DejaVuSans-Bold.ttf"
pdfmetrics.registerFont(TTFont("Deja", str(dej)))
pdfmetrics.registerFont(TTFont("DejaB", str(dejb)))
BAS = ParagraphStyle("bas", fontName="Deja", fontSize=10, leading=14, alignment=TA_LEFT)
H1 = ParagraphStyle("h1", fontName="DejaB", fontSize=17, leading=21, spaceAfter=8)
H2 = ParagraphStyle("h2", fontName="DejaB", fontSize=12, leading=15, spaceBefore=12, spaceAfter=6)
KUCUK = ParagraphStyle("k", fontName="Deja", fontSize=8.5, leading=11, textColor=colors.HexColor("#444444"))

doc = SimpleDocTemplate(str(T / "bulgular.pdf"), pagesize=A4,
                        leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm)
o = [Paragraph("Çanakkale Boğazı CBS — Bulgular (pilot + kurumsal-tanısal)", H1),
     Paragraph("Yöntem önerisinin uygulaması · Önce tarihsel bağlam, sonra model, ardından bağımsız sınama.", BAS),
     Spacer(1, 6)]

gk = json.load(open(ROOT / "06_karsilastirma" / "gercek_kiyas.json", encoding="utf-8"))
h1, h1v = gk["H1_M1"], gk["H1_fV"]
o += [Paragraph("Hüküm (K3-GERÇEK)", H2),
      Paragraph("“Tarihsel noktalar, tanımlanan fiziki ölçütler bakımından karşılaştırma "
                "alanlarından ayrışmıyor; bu sonuç belirtilen veri ve senaryo sınırları içinde geçerli.”", BAS),
      Paragraph(f"7 kurumsal tabya vs bant-eşleşmiş {h1['n_k']} kontrol (R04 betimsel): "
                f"M1 fark {h1['fark']:+.4f} (p={h1['p']}, delta {h1['delta']:+.2f}); "
                f"fV fark {h1v['fark']:+.4f} (p={h1v['p']}, delta {h1v['delta']:+.2f}). "
                f"Pareto tabya: {', '.join(gk['pareto_tabya']) if gk['pareto_tabya'] else 'yok'}.", BAS),
      Paragraph("Adaylar (U, kararlılık, sınıf)", H2)]
kur = pd.read_csv(ROOT / "05_olcut_model" / "kurumsal_olcut.csv")
tab = [["ID", "Ad", "fV", "U", "Karar.", "Sınıf"]]
for _, r in kur.iterrows():
    tab.append([r["kayit_id"], r["ad_standart"][:26], f"{r['fV']:.4f}", f"{r['U_esit']:.3f}",
                f"{r['kararlilik']:.2f}", r["okuma_sinifi"]])
t = Table(tab, colWidths=[3 * cm, 5.5 * cm, 2 * cm, 2 * cm, 2 * cm, 3 * cm], repeatRows=1)
t.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, 0), "DejaB"), ("FONTSIZE", (0, 0), (-1, -1), 8),
                       ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                       ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")])]))
o += [t, Paragraph("Koordinatlar kurumsal ziyaret referansıdır (orta güven); özgün oturum doğrulanmadı.", KUCUK),
      PageBreak(), Paragraph("Haritalar", H2)]
for img in ["harita_dem.png", "harita_U_esit.png", "harita_noktalar.png"]:
    p = T / img
    if p.exists():
        o += [Image(str(p), width=15 * cm, height=11 * cm), Spacer(1, 4)]
o += [Paragraph("Sınırlar: ziyaret koordinatı özgün platform değildir; −1 m hedef dejenere bulunup dışlandı; "
                "tek-yaka yanlılığı 4 Anadolu kontrolüyle kapatıldı; detay NIHAI_RAPOR.md ve K3_*.md dosyalarındadır.", KUCUK)]
doc.build(o)
print("-> bulgular.pdf")
