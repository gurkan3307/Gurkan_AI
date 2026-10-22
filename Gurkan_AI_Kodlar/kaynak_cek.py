"""GURKAN AI kaynak cekici: urls.txt'deki sayfalari indirir, ana metni cikarir, ham_kaynaklar/ icine kaydeder."""
import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
import trafilatura

KLASOR = Path(__file__).resolve().parent
HAM = KLASOR / 'ham_kaynaklar'
UA = 'GurkanAI-Bilgi-Bot/1.0 (kisisel arastirma)'
BEKLE = 1.5
MIN_KARAKTER = 800
_robots = {}


def izinli(url):
    p = urlparse(url)
    taban = f'{p.scheme}://{p.netloc}'
    if taban not in _robots:
        rp = RobotFileParser()
        rp.set_url(taban + '/robots.txt')
        try:
            r = requests.get(taban + '/robots.txt', headers={'User-Agent': UA}, timeout=20)
            if r.status_code == 200:
                rp.parse(r.text.splitlines())
            elif r.status_code in (401, 403):
                rp.disallow_all = True
            else:
                rp.allow_all = True
        except Exception:
            rp = None
        _robots[taban] = rp
    rp = _robots[taban]
    return True if rp is None else rp.can_fetch(UA, url)


def cek(url):
    r = requests.get(url, headers={'User-Agent': UA}, timeout=20)
    r.raise_for_status()
    html = r.content
    metin = trafilatura.extract(html, include_comments=False, include_tables=True) or ''
    meta = trafilatura.extract_metadata(html)
    baslik = (meta.title if meta and meta.title else '')
    return baslik, metin

def main():
    liste = KLASOR / 'urls.txt'
    if not liste.is_file():
        print('urls.txt bulunamadi. Her satira bir URL yaz.')
        return
    HAM.mkdir(exist_ok=True)
    urller = [s.strip() for s in liste.read_text(encoding='utf-8').splitlines()
              if s.strip().startswith('http')]
    say = {'yeni': 0, 'atlandi': 0, 'izinsiz': 0, 'kisa': 0, 'hata': 0}

    for url in urller:
        kimlik = hashlib.sha1(url.encode()).hexdigest()[:16]
        dosya = HAM / f'{kimlik}.json'
        if dosya.exists():
            say['atlandi'] += 1
            print(f'[ATLANDI] {url}')
            continue
        if not izinli(url):
            say['izinsiz'] += 1
            print(f'[IZINSIZ] {url} (robots.txt)')
            continue
        try:
            baslik, metin = cek(url)
        except Exception as e:
            say['hata'] += 1
            print(f'[HATA]    {url} ({e})')
            continue
        if len(metin) < MIN_KARAKTER:
            say['kisa'] += 1
            print(f'[KISA]    {url} ({len(metin)} karakter)')
            continue
        kayit = {
            'url': url,
            'baslik': baslik,
            'cekim_tarihi': datetime.now().strftime('%Y-%m-%d'),
            'metin_sha256': hashlib.sha256(metin.encode('utf-8')).hexdigest(),
            'metin': metin,
        }
        dosya.write_text(json.dumps(kayit, ensure_ascii=False, indent=2), encoding='utf-8')
        say['yeni'] += 1
        print(f'[YENI]    {baslik[:60]} ({len(metin)} karakter)')
        time.sleep(BEKLE)

    print(f"\nOZET: {say['yeni']} yeni, {say['atlandi']} atlandi, {say['izinsiz']} izinsiz, "
          f"{say['kisa']} kisa, {say['hata']} hatali")


if __name__ == '__main__':
    main()