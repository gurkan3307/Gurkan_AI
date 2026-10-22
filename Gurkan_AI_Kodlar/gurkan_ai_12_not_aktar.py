"""GURKAN AI kaynak-kontrollü notlar: ön izleme varsayılan, --apply ile yeni dosya kaydı."""
import argparse
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

ARCHIVE = Path(__file__).with_name('GURKAN_AI_12_Kaynak_Kontrollu_Not.zip')

def transfer(vault: Path, apply: bool = False):
    vault = vault.expanduser().resolve()
    if not vault.is_dir():
        raise SystemExit(f'[HATA] Kasa yok: {vault}')
    with ZipFile(ARCHIVE) as z:
        count, skip = 0, 0
        for info in z.infolist():
            if info.is_dir(): continue
            name=PurePosixPath(info.filename.replace('\\','/'))
            if name.is_absolute() or '..' in name.parts or name.suffix.lower() != '.md':
                raise SystemExit(f'[HATA] Uygunsuz dosya: {info.filename}')
            if info.file_size > 50000: raise SystemExit('Not çok büyük')
            target = vault.joinpath(*name.parts)
            if not target.resolve().is_relative_to(vault):
                raise SystemExit('Kasa dışına yazma engellendi')
            if target.exists():
                skip+=1; print('[ATLANDI]',name); continue
            print('[YAZILACAK]' if apply else '[EKLENECEK]',name)
            if apply:
                target.parent.mkdir(parents=True,exist_ok=True)
                try:
                    with target.open('xb') as f: f.write(z.read(info))
                except FileExistsError:
                    skip += 1;continue
            count+=1
    print(f'SONUÇ: {count if apply else 0} not yazıldı; {skip} mevcut dosya atlandı; {count} yeni not '+('eklendi.' if apply else 'ön izlemede.'))

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--vault',required=True,help='Gerçek Obsidian kasası yolu')
    ap.add_argument('--apply',action='store_true',help='Ön izleme yerine yeni dosyaları oluştur')
    ns=ap.parse_args()
    transfer(Path(ns.vault),ns.apply)
