"""run_all — tek komutla tum hat: python scripts/run_all.py [--hizli].

--hizli: agir adimlari (01 indirme, 03-04, 11, 22 viewshed) atlar; mevcut
ara ciktiyla hizli zinciri (05+) calistirir. Varsayilan: tam calisma.
Her adim suresi + durumu logs/run_all.txt icine islenir.
"""
import subprocess, sys, time, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HIZLI_ATLA = {"01_acik_veri_indir.py", "03_uyumlastir.py", "04_olcut_uret.py",
              "11_aday_olcut.py", "22_deniz_seviyesi.py"}
SIRA = ["00_ortam_kaydi.py", "01_acik_veri_indir.py", "02_envanter_iskelet.py",
        "03_uyumlastir.py", "04_olcut_uret.py", "33_anadolu_kontrol.py",
        "33b_anadolu_seyrelt.py", "05_model_calistir.py",
        "06_karsilastirma.py", "07_belirsizlik.py", "08_atlas_uret.py",
        "10_aday_nokta_derle.py", "11_aday_olcut.py", "12_pilot_kiyas.py",
        "13_k3_hukum_atlas.py", "14_tamamlayici.py", "25_web_veri.py",
        "26_ayrisma.py", "27_montecarlo.py", "28_capraz_kaynak.py",
        "29_kurumsal_envanter.py", "30_kurumsal_olcut.py", "32_gercek_kiyas.py",
        "34_mapzen.py",
        "35_excel.py", "36_font.py", "37_genislik.py", "18_wiki_capraz.py",
        "19_ahp.py", "20_erisim.py", "21_ogrenen.py", "22_deniz_seviyesi.py",
        "23_web_atlas.py", "24_rapor_html.py", "09_teslim_paketi.py",
        "15_qgis_proje.py", "16_dogrula.py", "17_denetim.py"]
hizli = "--hizli" in sys.argv
log = [f"baslangic_utc: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
       f"kip: {'hizli' if hizli else 'tam'}"]
for s in SIRA:
    if hizli and s in HIZLI_ATLA:
        log.append(f"ATLA {s}"); print(f"ATLA {s}"); continue
    t0 = time.time()
    p = subprocess.run([sys.executable, f"scripts/{s}"], cwd=ROOT,
                       capture_output=True, text=True)
    dt = time.time() - t0
    durum = "OK" if p.returncode == 0 else "HATA"
    log.append(f"{durum} {s} ({dt:.0f} sn)")
    print(f"{durum} {s} ({dt:.0f} sn)")
    if p.returncode != 0:
        log.append("STDERR: " + (p.stderr or "")[-1500:])
        break
(ROOT / "logs" / "run_all.txt").write_text("\n".join(log), encoding="utf-8")
print("-> logs/run_all.txt")
