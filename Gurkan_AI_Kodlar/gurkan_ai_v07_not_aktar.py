"""Varsayılan ön izleme. Yalnız .md, klasör dışına çıkmaz, üzerine yazmaz."""
import argparse
from pathlib import Path
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent
PACKAGE=HERE/'GURKAN_AI_v07_6_Kaynak_Not.zip'

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--vault', required=True)
    ap.add_argument('--apply', action='store_true')
    args=ap.parse_args()
    vault=Path(args.vault).resolve()
    if not vault.is_dir():
        raise SystemExit(f'Kasa yok: {vault}')
    dest=vault/'10 - Kaynak Kontrollu Bilgiler'
    with ZipFile(PACKAGE) as pack:
        infos=pack.infolist()
        if len(infos)>15:
            raise SystemExit('Beklenmedik dosya sayısı')
        safe=[]
        for item in infos:
            p=Path(item.filename)
            if item.is_dir() or len(p.parts)!=1 or p.suffix.lower()!='.md' or item.file_size>100000:
                raise SystemExit(f'Güvensiz paket girdisi: {item.filename}')
            safe.append((item, dest/p.name))
        ready=0; skipped=0
        for item,path in safe:
            if path.exists():
                skipped+=1
                print('[MEVCUT]',path.name)
                continue
            ready+=1
            print('[EKLENECEK]',path.name)
            if args.apply:
                dest.mkdir(parents=True,exist_ok=True)
                try:
                    with path.open('xb') as f:
                        f.write(pack.read(item))
                except FileExistsError:
                    skipped+=1; ready-=1
        print(f'SONUÇ: {ready if args.apply else 0} not yazıldı; {skipped} atlandı; {ready} eklenebilir/eklendi.')
if __name__=='__main__':main()
