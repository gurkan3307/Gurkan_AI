"""Paket 09 ön izleme ve yalnızca yeni dosya ekleme aracı.
Varsayılan önizlemedir. Mevcut dosyalara ASLA yazmaz.
"""
import argparse
from pathlib import Path, PurePosixPath
from zipfile import ZipFile
import csv, io, re, unicodedata

BASE=Path(__file__).resolve().parent
ZIP=BASE/'GURKAN_AI_Paket_09_104_Not.zip'

def normal(s):
    s=unicodedata.normalize('NFKD',s).casefold()
    return re.sub(r'[^a-z0-9]+','',s)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--vault', required=True)
    p.add_argument('--apply',action='store_true')
    a=p.parse_args()
    vault=Path(a.vault).resolve()
    if not vault.is_dir():p.error('Obsidian kasasi bulunamadi: '+str(vault))
    if not ZIP.is_file():p.error('Paket ZIP bulunamadi: '+str(ZIP))
    prior={normal(f.stem) for f in vault.rglob('*.md') if '.obsidian' not in f.parts}
    count={'aday':0,'ekle':0,'ayni_ad':0,'ad_benzer':0}
    with ZipFile(ZIP) as z:
        members=z.infolist()
        if len(members)!=104:p.error('Paket 104 not icermiyor')
        for info in members:
            if info.is_dir():continue
            path=PurePosixPath(info.filename)
            if path.is_absolute() or '..' in path.parts or path.suffix.lower()!='.md' or info.file_size>30000:
                p.error('Guvenli olmayan arsiv yolu: '+str(path))
            count['aday']+=1
            dest=vault.joinpath(*path.parts)
            if dest.exists(): count['ayni_ad']+=1;status='ATLANDI - yol mevcut'
            elif normal(dest.stem) in prior:count['ad_benzer']+=1;status='INCELE - baslik benziyor'
            else:
                status='EKLENECEK'
                count['ekle']+=1
                if a.apply:
                    dest.parent.mkdir(parents=True,exist_ok=True)
                    with dest.open('x',encoding='utf-8') as f:f.write(z.read(info).decode('utf-8'))
                    prior.add(normal(dest.stem))
                    status='EKLENDI'
            print(f'[{status}] {path}')
    print('SONUC:', count,'| yazma modu:',a.apply)
    if not a.apply:print('Bu sadece on izlemedir. Dogruysa --apply ekleyin.')
if __name__=='__main__':main()
