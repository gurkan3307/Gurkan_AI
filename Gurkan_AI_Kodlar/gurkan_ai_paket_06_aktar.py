"""GURKAN AI Paket 06: 50 kaynaklı taslak Markdown notunu güvenli içe aktarma.

Çalıştırma (ön izleme): python gurkan_ai_paket_06_aktar.py
Gerçek aktarma:          python gurkan_ai_paket_06_aktar.py --apply
Test:                   python gurkan_ai_paket_06_aktar.py --vault C:\\testkasasi

Varsayılan ön izleme hiçbir not oluşturmaz. Mevcut notlara ASLA yazmaz.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
from pathlib import Path, PurePosixPath
from zipfile import ZipFile, BadZipFile

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / 'GURKAN_AI_Bilgi_Paketi_06_50_Taslak.zip'
DEFAULT_VAULT = Path(os.environ.get('JARVIS_VAULT_PATH', r'D:\GURKANUS27 Yapay Zeka\GURKAN_AI_Bilgi_Bankasi'))
ALLOWED = {
    '01 — Python ve Yazılım', '02 — Yapay Zekâ ve Modeller',
    '04 — Otomasyon Sistemleri', '06 — Kaynaklar',
    '08 — JARVIS Arayüzü',
}
MAX_FILE = 50_000
MAX_ARCHIVE = 5_000_000


def canonical_title(name: str) -> str:
    """Başlıktaki sıra numarasından bağımsız muhtemel tekrar kontrolü."""
    s = re.sub(r'^\d+\s*[-._ ]*', '', name, flags=re.I)
    return re.sub(r'\s+', ' ', s).casefold().strip()


def validate_archive(zip_path: Path) -> list[tuple[str, bytes]]:
    """Her dosyayı RAM'de doğrular, değiştirme izni vermez."""
    with ZipFile(zip_path) as z:
        bad = z.testzip()
        if bad:
            raise ValueError(f'Arşiv bozuk: {bad}')
        all_infos = z.infolist()
        if sum(x.file_size for x in all_infos) > MAX_ARCHIVE:
            raise ValueError('Arşiv açıldığında boyut sınırını aşıyor.')
        if z.namelist().count('manifest.json') != 1:
            raise ValueError('manifest.json eksik veya tekrarlı.')
        manifest = json.loads(z.read('manifest.json').decode('utf-8'))
        if not isinstance(manifest, list) or len(manifest) != 50:
            raise ValueError('Manifest tam 50 not içermeli.')
        expected = {x['dosya']: x for x in manifest}
        if len(expected) != len(manifest):
            raise ValueError('Manifest içinde çift kayıt var.')
        archive_members = [i for i in all_infos if not i.is_dir() and i.filename not in ('manifest.json', 'PAKET_ACIKLAMA.md')]
        if set(i.filename for i in archive_members) != set(expected) or len(archive_members) != len(expected):
            raise ValueError('Arşiv ve manifest içeriği eşleşmiyor.')
        entries = []
        for info in archive_members:
            raw = info.filename
            pp = PurePosixPath(raw)
            parts = pp.parts
            mode = (info.external_attr >> 16) & 0o170000
            if (len(parts) != 2 or parts[0] not in ALLOWED or
                raw.startswith('/') or ':' in raw or '\\' in raw or
                any(part in ('', '.', '..') for part in parts) or
                pp.suffix.lower() != '.md' or info.file_size > MAX_FILE or
                mode == stat.S_IFLNK):
                raise ValueError(f'İzin verilmeyen ZIP öğesi: {raw}')
            content = z.read(info)
            rec = expected[raw]
            if hashlib.sha256(content).hexdigest() != rec['sha256']:
                raise ValueError(f'SHA256 doğrulaması başarısız: {raw}')
            if content[:4] != b'---\n' or b'durum: taslak' not in content or b'test_durumu: test_edilmedi' not in content:
                raise ValueError(f'Güvenlik metaverisi eksik: {raw}')
            entries.append((raw, content))
        return entries


def process(package: Path, vault: Path, apply: bool) -> dict:
    entries = validate_archive(package)
    if not vault.is_dir():
        raise FileNotFoundError(f'Obsidian kasası bulunamadı: {vault}')
    vault_root = vault.resolve()
    existing_title = {}
    for p in vault.rglob('*.md'):
        if any(part.startswith('.') for part in p.relative_to(vault).parts):
            continue
        existing_title.setdefault(canonical_title(p.stem), str(p.relative_to(vault)))

    pending = []
    old = []
    similar = []
    for rel, content in entries:
        dst = vault.joinpath(*PurePosixPath(rel).parts)
        try:
            dst.resolve().relative_to(vault_root)
        except ValueError as err:
            raise ValueError(f'Kasa dışına erişim engellendi: {rel}') from err
        if dst.exists():
            old.append(rel)
        elif canonical_title(dst.stem) in existing_title:
            similar.append((rel, existing_title[canonical_title(dst.stem)]))
        else:
            pending.append((rel,dst,content))

    print(f'Kasa: {vault}')
    print(f'ZIP paketinde {len(entries)} not | Yeni aday {len(pending)} | Aynı yol {len(old)} | Başlık benzeri {len(similar)}')
    for rel in old:
        print('[ATLA - VAR]    ',rel)
    for rel, found in similar:
        print('[ATLA - BENZER] ',rel,'| mevcut:',found)
    for rel, _, _ in pending:
        print('[EKLENECEK]' if not apply else '[KAYDEDİLECEK]',rel)

    saved = 0
    if apply:
        for rel,dst,content in pending:
            # Önceden var olan dosyayı değiştirmeden 'exclusive create'.
            dst.parent.mkdir(parents=True,exist_ok=True)
            # Parent symlink in case it changed since checking.
            try:
                dst.resolve().relative_to(vault_root)
            except ValueError as err:
                raise ValueError(f'Yol değişti, işlem durduruldu: {rel}') from err
            try:
                with dst.open('xb') as f:
                    f.write(content)
                saved += 1
            except FileExistsError:
                print('[ATLA - SON ANDA OLUŞTU]',rel)
    print(f'\nSONUÇ: {saved} not yazıldı. ' + ('Obsidian içinde /indeksle çalıştır.' if apply else 'Bu sadece ön izlemeydi. Onaylı aktarım: python gurkan_ai_paket_06_aktar.py --apply'))
    return {'paket':len(entries),'aday':len(pending),'mevcut':len(old),'benzer':len(similar),'yazilan':saved}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply',action='store_true',help='Ön izlemeden sonra gerçekten kaydet')
    parser.add_argument('--vault',type=Path,default=DEFAULT_VAULT,help='Obsidian kasasının yolu')
    parser.add_argument('--zip',dest='archive',type=Path,default=PACKAGE,help='Bilgi paketi ZIP yolu')
    args = parser.parse_args()
    try:
        process(args.archive,args.vault,args.apply)
    except (OSError,ValueError,KeyError,json.JSONDecodeError,BadZipFile) as e:
        print('[HATA]',e)
        raise SystemExit(1)

if __name__ == '__main__':
    main()
