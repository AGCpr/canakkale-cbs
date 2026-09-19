"""19 — AHP agirlik turetimi: uzman senaryosunun gerekcesi (DUZELTILMIS).

Rapor karsiligi: §04 (AHP agirlik senaryosu [4]). Matris params/model.yaml
'ahp' bolumunden okunur; ASIL ozvektor (en buyuk ozdegere ait) normalize
edilir; lamda/CI/CR hesaplanir; CR<=0.10 sarti aranir. Sonuc yalnizca
logs/ahp.txt + 05_olcut_model/AHP_NOTU.md icine yazilir; model.yaml
DEGISTIRILMEZ (uzman senaryo karsilastirmasi raporda).
"""
from pathlib import Path
import numpy as np, yaml

ROOT = Path(__file__).resolve().parents[1]
P = yaml.safe_load(open(ROOT / "params" / "model.yaml", encoding="utf-8"))
A = np.array(P["ahp"]["matris"], dtype=float)

deger, vektor = np.linalg.eig(A)
i = int(np.argmax(np.real(deger)))
w = np.real(vektor[:, i])
w = w / w.sum()
assert bool((w > 0).all()), f"pozitiflik ihlali: {w}"
lam = float(((A @ w) / w).mean())
n = A.shape[0]
CI = (lam - n) / (n - 1)
CR = CI / 0.58
print(f"AHP agirlik: wV={w[0]:.4f} wR={w[1]:.4f} wS={w[2]:.4f} lam={lam:.4f} CR={CR:.4f}")
assert CR <= P["ahp"]["CR_esik"], f"CR asimi: {CR}"

mevcut = P["agirliklar"]["uzman_gorus_agirlikli"]
sapma = max(abs(mevcut["wV"] - w[0]), abs(mevcut["wR"] - w[1]), abs(mevcut["wS"] - w[2]))
print(f"mevcut uzman senaryo: {mevcut} | AHP sapmasi: {sapma:.4f} "
      f"-> {'UYUMLU' if sapma <= 0.05 else 'FARKLI (her ikisi de senaryo olarak korunur)'}")
open(ROOT / "logs" / "ahp.txt", "w", encoding="utf-8").write(
    f"wV={w[0]:.4f} wR={w[1]:.4f} wS={w[2]:.4f} lam={lam:.4f} CR={CR:.4f} sapma={sapma:.4f}\n")
open(ROOT / "05_olcut_model" / "AHP_NOTU.md", "w", encoding="utf-8").write(
 "# AHP notu (§04)\n\n- Matris params/model.yaml 'ahp' bolumunde; "
 "gerekce: gozetleme birincil, hâkimiyet ikincil, yerlesim ucuncu.\n"
 f"- Asil ozvektor agirlik: {[round(float(x), 4) for x in w]}, CR={CR:.4f} (esik 0.10).\n"
 f"- Mevcut uzman senaryoyla sapma {sapma:.4f}.\n"
 "- Uzmanlar arasi ayrisma: tek matris = tek gorus; ikinci uzman matrisi eklendiginde geometrik ortalama + ayrisma raporlanir.\n")
