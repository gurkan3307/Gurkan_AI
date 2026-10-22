"""GURKAN AI not uretici v2: ham_kaynaklar/ -> LM Studio -> 3 kontrol -> not.
Kontrol 1: alinti kaynak metinde birebir var mi
Kontrol 2: alinti duz yazi mi (kod/cikti ornegi degil)
Kontrol 3: model hakem: alinti iddiayi acikca destekliyor mu"""
import argparse
import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse

import requests

KLASOR = Path(__file__).resolve().parent
HAM = KLASOR / 'ham_kaynaklar'
API = 'http://localhost:1234/v1'
PARCA_BOY = 3500
MIN_ALINTI = 40
VARSAYILAN_CIKTI = 'uretilen_notlar'


def norm(s):
    s = (s.replace('\u2019', "'").replace('\u2018', "'")
          .replace('\u201c', '"').replace('\u201d', '"'))
    return re.sub(r'\s+', ' ', s).strip().lower()


def parcala(metin):
    parcalar, simdiki = [], ''
    for satir in metin.split('\n'):
        if simdiki and len(simdiki) + len(satir) > PARCA_BOY:
            parcalar.append(simdiki)
            simdiki = ''
        simdiki += satir + '\n'
    if simdiki.strip():
        parcalar.append(simdiki)
    return [p for p in parcalar if len(p) > 400]


def sec(parcalar, n):
    if len(parcalar) <= n:
        return parcalar
    return [parcalar[int(i * len(parcalar) / n)] for i in range(n)]


def model_adi():
    r = requests.get(f'{API}/models', timeout=10)
    r.raise_for_status()
    return r.json()['data'][0]['id']


def sohbet(model, istek, max_tokens):
    r = requests.post(f'{API}/chat/completions', timeout=300, json={
        'model': model,
        'messages': [{'role': 'user', 'content': istek}],
        'temperature': 0.1,
        'max_tokens': max_tokens,
    })
    r.raise_for_status()
    icerik = r.json()['choices'][0]['message']['content']
    return re.sub(r'<think>.*?</think>', '', icerik, flags=re.S)


def json_al(icerik):
    a, b = icerik.find('{'), icerik.rfind('}')
    if a < 0 or b < 0:
        return {}
    try:
        veri = json.loads(icerik[a:b + 1])
    except json.JSONDecodeError:
        return {}
    return veri if isinstance(veri, dict) else {}


def kod_gibi(a):
    a = a.strip()
    if '\n' in a or '#' in a:
        return True
    if a[:1] in '\'"' and a[-1:] in '\'"':
        return True
    if a[:1] in '@`{':
        return True
    if re.search(r'\bdef \w+\(|\bimport \w|\breturn\b|=\s*\w+\(|@\w+\.\w+', a):
        return True
    harf = sum(c.isalpha() or c in " ,.;:'-()\u2018\u2019" for c in a)
    return harf / max(len(a), 1) < 0.88


INGILIZCE = {'the', 'is', 'are', 'of', 'to', 'and', 'for', 'in', 'be', 'will',
             'that', 'this', 'with', 'it', 'as', 'by', 'or', 'not', 'if'}
BASLANGIC_YASAK = {'this', 'these', 'it', 'they', 'that', 'those', 'so', 'however',
                   'but', 'and', 'also', 'then', 'such', 'note', 'see', 'here', 'there'}


def ingilizce_mi(t):
    kelimeler = re.findall(r"[a-z']+", t.lower())
    return sum(k in INGILIZCE for k in kelimeler) >= 2


def cumleler(parca):
    metin = re.sub(r'\s+', ' ', parca)
    metin = metin.replace('|', ' ||| ').replace('\u00b6', ' ||| ')
    metin = re.sub(r'\s[-\u2013]\s(?=[A-Za-z_`])', ' ||| ', metin)
    adaylar = []
    for blok in metin.split('|||'):
        for c in re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', blok):
            c = c.strip()
            kelimeler = c.split()
            if not 10 <= len(kelimeler) <= 40 or len(c) < MIN_ALINTI:
                continue
            if not (c[0].isupper() or c[0].isdigit()) or c[-1] not in '.!?':
                continue
            if kelimeler[0].lower().strip(',') in BASLANGIC_YASAK:
                continue
            if any(x in c for x in ('>>>', 'Traceback', '...', '\u2026')) or kod_gibi(c):
                continue
            adaylar.append(c)
    if len(adaylar) > 14:
        adaylar = [adaylar[int(i * len(adaylar) / 14)] for i in range(14)]
    return adaylar


def sor(model, parca):
    adaylar = cumleler(parca)
    if len(adaylar) < 3:
        return []
    liste = '\n'.join(f'{n}. {c}' for n, c in enumerate(adaylar, 1))
    istek = (
        "/no_think\n"
        "Asagida bir dokumantasyondan numarali Ingilizce cumleler var. En fazla 3 tanesini sec: "
        "somut bilgi iceren (deger, kural, davranis, kisit) cumleleri. "
        "Giris, gezinme, ayni seyi tekrar eden ya da icerigi olmayan cumleleri secme.\n"
        "Her secim icin 'iddia' yaz: TURKCE, tek cumle, secilen cumlenin soyledigi seyi ozetle. "
        "Ingilizce cumleyi kopyalama. Sadece kod, fonksiyon ve parametre adlari Ingilizce kalabilir. "
        "Cumlede olmayan hicbir ayrinti ekleme.\n"
        'Sadece JSON dondur: {"secimler":[{"no":1,"iddia":"Turkce ozet cumlesi"}]}\n\n' + liste
    )
    secimler = json_al(sohbet(model, istek, 500)).get('secimler')
    if not isinstance(secimler, list):
        return []
    sonuc = []
    for x in secimler:
        if not isinstance(x, dict) or not isinstance(x.get('iddia'), str):
            continue
        if ingilizce_mi(x['iddia']):
            continue
        try:
            no = int(x.get('no'))
        except (TypeError, ValueError):
            continue
        if 1 <= no <= len(adaylar):
            sonuc.append({'iddia': x['iddia'], 'alinti': adaylar[no - 1]})
    return sonuc


def hakem(model, ciftler):
    onayli = []
    debug = os.environ.get('HAKEM_DEBUG') == '1'
    for i in range(0, len(ciftler), 6):
        grup = ciftler[i:i + 6]
        liste = '\n'.join(f"{n}. IDDIA: {c['iddia']}\n   ALINTI: {c['alinti']}"
                          for n, c in enumerate(grup, 1))
        istek = (
            "/no_think\n"
            "Asagida Turkce IDDIA'lar ve her birinin Ingilizce ALINTI'si var. "
            "Her madde icin karar ver: IDDIA, ALINTI'nin anlattigi seyi dogru ozetliyor mu?\n"
            "- true: iddianin ana fikri alintida var. Ceviri ve ozet farki sorun degil.\n"
            "- false: iddia alintida OLMAYAN yeni bir bilgi, sayi, mekanizma ya da sonuc ekliyor "
            "veya alintiyla celisiyor.\n"
            'Sadece JSON dondur: {"sonuc":[{"no":1,"destekliyor":true,"neden":"kisa"}]}\n\n' + liste
        )
        try:
            sonuc = json_al(sohbet(model, istek, 800)).get('sonuc')
        except Exception as e:
            print(f'   hakem hatasi: {e}')
            continue
        if not isinstance(sonuc, list):
            print('   hakem cevabi okunamadi')
            continue
        evet = set()
        for x in sonuc:
            if not isinstance(x, dict):
                continue
            try:
                no = int(x.get('no'))
            except (TypeError, ValueError):
                continue
            if not 1 <= no <= len(grup):
                continue
            ok = str(x.get('destekliyor')).strip().lower() == 'true'
            if debug:
                print(f"   [{'EVET ' if ok else 'HAYIR'}] {grup[no - 1]['iddia'][:75]} | {str(x.get('neden', ''))[:70]}")
            if ok:
                evet.add(no)
        onayli += [c for n, c in enumerate(grup, 1) if n in evet]
    return onayli


def dosya_adi(baslik, url):
    temiz = (re.sub(r'[<>:"/\\|?*\n\r]', '', baslik).strip()[:70]) or 'adsiz'
    host = urlparse(url).netloc.replace('www.', '')
    return f'{temiz} ({host}).md'


def not_yaz(veri, dogrulananlar):
    url = veri['url']
    govde = '\n'.join(f"- {d['iddia']}\n  > {d['alinti']}" for d in dogrulananlar)
    return (
        '---\n'
        'durum: otomatik_kontrol_edildi\n'
        'kontrol: alinti_kaynakta_var + model_hakem_onayli\n'
        'kaynak_turu: web_sayfasi\n'
        f'kaynak_url: "{url}"\n'
        f"cekim_tarihi: {veri['cekim_tarihi']}\n"
        f"kaynak_metin_sha256: {veri['metin_sha256']}\n"
        f'onayli_iddia_sayisi: {len(dogrulananlar)}\n'
        'test_durumu: test_edilmedi\n'
        'tags:\n  - gurkan-ai\n  - kaynak-kontrollu\n  - otomatik\n'
        'kaynaklar:\n'
        f'  - "{url}"\n'
        '---\n\n'
        f"# {veri['baslik']}\n\n"
        '## Kaynakli bilgiler\n'
        f'{govde}\n\n'
        '## Kaynak\n'
        f'{url}\n'
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', default=None)
    ap.add_argument('--max-parca', type=int, default=6)
    ap.add_argument('--en-az', type=int, default=3)
    ap.add_argument('--cikti', default=VARSAYILAN_CIKTI)
    ap.add_argument('--sadece', nargs='*', default=None, help='url icinde gecen parca(lar)')
    args = ap.parse_args()
    test = args.cikti != VARSAYILAN_CIKTI

    try:
        model = args.model or model_adi()
    except Exception as e:
        print(f'LM Studio sunucusuna ulasilamadi ({e}). Sunucuyu baslattin mi, model yuklu mu?')
        return
    print(f'Model: {model}   cikti: {args.cikti}\n')

    cikti = KLASOR / args.cikti
    cikti.mkdir(exist_ok=True)
    ozet = {'yazildi': 0, 'yetersiz': 0, 'atlandi': 0}

    for dosya in sorted(HAM.glob('*.json')):
        veri = json.loads(dosya.read_text(encoding='utf-8'))
        if args.sadece and not any(s in veri['url'] for s in args.sadece):
            continue
        hedef = cikti / dosya_adi(veri['baslik'], veri['url'])
        isaret = dosya.with_suffix('.islendi')
        if hedef.exists() or (isaret.exists() and not test):
            ozet['atlandi'] += 1
            print(f"[ATLANDI]  {veri['baslik'][:60]}")
            continue

        adaylar, gorulen = [], set()
        bulunamadi = kod_elenen = 0
        for parca in sec(parcala(veri['metin']), args.max_parca):
            try:
                gelenler = sor(model, parca)
            except Exception as e:
                print(f'   model hatasi: {e}')
                continue
            parca_n = norm(parca)
            for x in gelenler:
                alinti = x['alinti'].strip()
                n = norm(alinti)
                if len(alinti) < MIN_ALINTI or n not in parca_n or n in gorulen:
                    bulunamadi += 1
                    continue
                if kod_gibi(alinti):
                    kod_elenen += 1
                    continue
                gorulen.add(n)
                adaylar.append({'iddia': x['iddia'].strip(), 'alinti': alinti})

        dogru = hakem(model, adaylar) if adaylar else []
        detay = (f"{len(dogru)} onayli, {kod_elenen} kod, "
                 f"{len(adaylar) - len(dogru)} hakem, {bulunamadi} bulunamadi")
        if len(dogru) < args.en_az:
            ozet['yetersiz'] += 1
            if not test:
                isaret.write_text('yetersiz', encoding='utf-8')
            print(f"[YETERSIZ] {veri['baslik'][:50]} ({detay})")
            continue
        hedef.write_text(not_yaz(veri, dogru), encoding='utf-8')
        ozet['yazildi'] += 1
        print(f"[NOT]      {veri['baslik'][:50]} ({detay})")

    print(f"\nOZET: {ozet['yazildi']} not yazildi, {ozet['yetersiz']} yetersiz, {ozet['atlandi']} atlandi")


if __name__ == '__main__':
    main()