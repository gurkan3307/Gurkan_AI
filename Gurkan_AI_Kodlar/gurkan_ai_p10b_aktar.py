#!/usr/bin/env python3
"""GURKAN AI Paket 10B güvenli aktarma; varsayılan sadece önizlemedir."""
import argparse
from pathlib import Path, PurePosixPath
import zipfile

ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / "GURKAN_AI_Paket_10B_100_Not_ve_Aktarim.zip"
PREFIX = "11 - Kaynak Adaylari/P10B 100 Not/"

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--vault', required=True)
    p.add_argument('--apply', action='store_true')
    args = p.parse_args()
    vault = Path(args.vault).expanduser().resolve()
    if not vault.is_dir():
        raise SystemExit(f"HATA: Kasa klasörü yok: {vault}")
    if not ARCHIVE.is_file():
        raise SystemExit(f"HATA: Paket dosyası yok: {ARCHIVE}")
    count=skipped=0
    with zipfile.ZipFile(ARCHIVE) as z:
        items=[x for x in z.infolist() if x.filename.startswith(PREFIX) and x.filename.endswith('.md')]
        for info in items:
            rel=PurePosixPath(info.filename)
            if any(x in ('..','') for x in rel.parts):
                raise SystemExit('Güvensiz arşiv yolu')
            dest=(vault / Path(*rel.parts)).resolve()
            if not dest.is_relative_to(vault):
                raise SystemExit('Kasa dışına çıkış engellendi')
            if dest.exists():
                print('[ATLANDI]', rel); skipped+=1;continue
            print('[EKLENECEK]' if not args.apply else '[EKLENDİ]', rel)
            if args.apply:
                dest.parent.mkdir(parents=True,exist_ok=True)
                try:
                    with dest.open('xb') as f: f.write(z.read(info))
                except FileExistsError:
                    print('[ATLANDI: yarış]',rel);skipped+=1;continue
            count+=1
    print(f'SONUÇ: aday={len(items)} eklenebilir/yazılan={count} atlanan={skipped} mod={"YAZMA" if args.apply else "ÖN İZLEME"}')
    if not args.apply: print('Hiçbir dosya yazılmadı. Yazmak için --apply kullanın.')
if __name__=='__main__': main()
