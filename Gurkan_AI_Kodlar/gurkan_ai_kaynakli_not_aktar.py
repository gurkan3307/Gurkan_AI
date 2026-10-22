"""GURKAN AI kaynak kontrollu not aktarimi: varsayilan onizleme, asla uzerine yazmaz."""
import argparse
import hashlib
from pathlib import Path
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
PACKAGE = HERE / 'GURKAN_AI_10_Kaynak_Kontrollu_Not.zip'
DEFAULT_VAULT = Path(r'D:\GURKANUS27 Yapay Zeka\GURKAN_AI_Bilgi_Bankasi')


def transfer(vault, apply=False):
    vault = Path(vault).resolve()
    if not vault.is_dir():
        raise ValueError(f'Obsidian kasası bulunamadı: {vault}')
    if not PACKAGE.is_file():
        raise FileNotFoundError(f'ZIP bulunamadı: {PACKAGE}')
    root = vault / '10 - Kaynak Kontrollu Bilgiler'
    added = 0
    skipped = 0
    with ZipFile(PACKAGE) as z:
        for item in z.infolist():
            if item.is_dir():
                continue
            p = Path(item.filename)
            if len(p.parts) != 1 or p.suffix.lower() != '.md' or p.name.startswith('.'):
                raise ValueError(f'ZIP tehlikeli/gecersiz yol iceriyor: {item.filename}')
            contents = z.read(item)
            if len(contents) > 200_000:
                raise ValueError('Not beklenenden buyuk')
            target = root / p.name
            if target.exists():
                skipped += 1
                print(f'[ATLANDI] {p.name}')
                continue
            print(f'[EKLENECEK] {p.name}')
            if apply:
                root.mkdir(parents=True, exist_ok=True)
                try:
                    with target.open('xb') as fd:
                        fd.write(contents)
                except FileExistsError:
                    skipped += 1
                    continue
            added += 1
    print(f'SONUC: {added if apply else 0} dosya yazildi, {skipped} mevcut dosya atlandi.')
    if not apply:
        print(f'ONIZLEME: {added} not eklenebilir. Gercek aktarim icin --apply kullan.')


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--vault', default=str(DEFAULT_VAULT))
    a.add_argument('--apply', action='store_true')
    args = a.parse_args()
    transfer(args.vault, args.apply)


if __name__ == '__main__':
    main()
