"""Eski kurallarla uretilen otomatik notlari arsive tasir. Silmez."""
import shutil
from pathlib import Path

KLASOR = Path(__file__).resolve().parent
VAULT = Path(r'D:\GURKANUS27 Yapay Zeka\GURKAN_AI_Bilgi_Bankasi')
ARSIV = KLASOR / '_arsiv_eski_notlar'
KAYNAKLAR = [KLASOR / 'uretilen_notlar', VAULT / '10 - Kaynak Kontrollu Bilgiler']
ISARET = 'durum: otomatik_dogrulandi'

tasinan = 0
for kaynak in KAYNAKLAR:
    if not kaynak.is_dir():
        continue
    hedef = ARSIV / kaynak.name
    hedef.mkdir(parents=True, exist_ok=True)
    for p in sorted(kaynak.glob('*.md')):
        if ISARET in p.read_text(encoding='utf-8', errors='replace'):
            shutil.move(str(p), str(hedef / p.name))
            tasinan += 1

silinen = 0
for m in (KLASOR / 'ham_kaynaklar').glob('*.islendi'):
    m.unlink()
    silinen += 1

print(f'{tasinan} eski otomatik not -> {ARSIV}')
print(f'{silinen} eski yetersiz isareti temizlendi')