import re
from pathlib import Path

VAULT = Path(r'D:\GURKANUS27 Yapay Zeka\GURKAN_AI_Bilgi_Bankasi')
HEDEF = 25000
KAYNAKLI = VAULT / '10 - Kaynak Kontrollu Bilgiler'


def say(k):
    return sum(1 for _ in k.rglob('*.md')) if k.is_dir() else 0


not_sayisi = iddia = 0
siteler = {}
if KAYNAKLI.is_dir():
    for p in KAYNAKLI.rglob('*.md'):
        t = p.read_text(encoding='utf-8', errors='replace')
        if 'model_hakem_onayli' not in t:
            continue
        not_sayisi += 1
        m = re.search(r'onayli_iddia_sayisi:\s*(\d+)', t)
        iddia += int(m.group(1)) if m else 0
        h = re.search(r'kaynak_url:\s*"https?://([^/"]+)', t)
        if h:
            siteler[h.group(1)] = siteler.get(h.group(1), 0) + 1

toplam = say(VAULT)
print(f"Otomatik, hakem onaylı not : {not_sayisi}")
print(f"Onaylı bilgi (iddia)       : {iddia}")
if not_sayisi:
    print(f"Not başına ortalama        : {iddia / not_sayisi:.1f}")
print(f"Klasördeki diğer notlar    : {say(KAYNAKLI) - not_sayisi}")
print(f"Vault toplamı              : {toplam}")
print("\nSite dağılımı:")
for s, n in sorted(siteler.items(), key=lambda x: -x[1]):
    print(f"  {s:35} {n}")
print(f"\nHedef {HEDEF} bilgi: %{iddia / HEDEF * 100:.1f} tamamlandı, {max(HEDEF - iddia, 0)} kaldı")