"""GURKAN AI 08B kaynak kontrollü not aktarımı. Varsayılan: SADECE önizleme.
Kullanım:
 python gurkan_ai_08B_aktar.py --vault "D:\\...\\GURKAN_AI_Bilgi_Bankasi"
 python gurkan_ai_08B_aktar.py --vault "D:\\...\\GURKAN_AI_Bilgi_Bankasi" --apply
"""
import argparse
from pathlib import Path, PurePosixPath
from zipfile import ZipFile
import re
import sys

ARCHIVE=Path(__file__).with_name('GURKAN_AI_08B_25_Kaynak_Kontrollu_Not.zip')

def normalize(s):
    return re.sub(r'\s+',' ',s.casefold()).strip()

def main():
    parser=argparse.ArgumentParser(description='Obsidian 08B paketi güvenli aktarım')
    parser.add_argument('--vault',required=True,help='Mevcut gerçek Obsidian kasasının tam yolu')
    parser.add_argument('--apply',action='store_true',help='Varsayılan önizlemeden sonra ekleme yap')
    args=parser.parse_args()
    vault=Path(args.vault).expanduser().resolve()
    if not vault.is_dir():
        sys.exit(f'[HATA] Kasa bulunamadı: {vault}')
    if not ARCHIVE.is_file():
        sys.exit(f'[HATA] ZIP bulunamadı: {ARCHIVE}')
    existing_names={normalize(p.stem) for p in vault.rglob('*.md') if p.is_file()}
    new_count=skip_count=written=0
    with ZipFile(ARCHIVE) as z:
        infos=z.infolist()
        if len(infos)!=25: sys.exit(f'[HATA] Beklenen 25 not yerine {len(infos)} kayıt bulundu.')
        for info in infos:
            member=PurePosixPath(info.filename)
            if info.is_dir() or len(member.parts)<2 or member.is_absolute() or '..' in member.parts or member.suffix!='.md' or info.file_size>40_000:
                sys.exit(f'[HATA] Güvensiz ZIP öğesi: {info.filename}')
            target=vault.joinpath(*member.parts)
            if not target.resolve().is_relative_to(vault): sys.exit('[HATA] ZIP yolu kasa dışına taşıyor')
            if target.exists() or normalize(target.stem) in existing_names:
                print('[ATLANACAK]',member); skip_count+=1;continue
            print('[EKLENECEK]' if not args.apply else '[EKLENDİ]',member)
            new_count+=1
            if args.apply:
                target.parent.mkdir(parents=True,exist_ok=True)
                try:
                    with target.open('xb') as f: f.write(z.read(info))
                except FileExistsError:
                    print('[ATLANDI] Hedef aynı anda oluştu:',member);continue
                written+=1
            existing_names.add(normalize(target.stem))
    print(f'SONUÇ: aday={new_count} atlanan={skip_count} yazılan={written}.')
    if not args.apply: print('Bu sadece önizlemeydi. Gerçek aktarım için --apply ekleyin.')

if __name__=='__main__':main()
