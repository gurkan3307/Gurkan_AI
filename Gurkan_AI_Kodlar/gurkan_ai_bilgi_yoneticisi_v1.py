"""GURKAN AI Bilgi Bankasi Yoneticisi v1.0 - salt okunur denetim.

Bu arac hicbir Obsidian notunu, vektor DB'sini veya SQLite hafizasini degistirmez.
URL varligini/icerigini internetten dogrulamaz. Kaynak ve durum etiketleri kanit degildir.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

DEFAULT_VAULT = r'D:\GURKANUS27 Yapay Zeka\GURKAN_AI_Bilgi_Bankasi'
EXCLUDED_DIRS = {'.obsidian', '.git', '.trash', '_arsiv', '__pycache__'}
SOURCE_KEYS = ('kaynak_url', 'source_url', 'kaynak', 'source', 'url', 'referans', 'references')
STATUS_KEYS = ('durum', 'status', 'dogrulama_durumu')
STOP = {'ve', 'ile', 'bir', 'olan', 'icin', 'olarak', 'bu', 'da', 'de', 'the', 'and', 'for', 'from', 'not', 'bir', 'gibi'}

def plain(s: str) -> str:
    s = s.replace('ı', 'i').replace('İ', 'i')
    s = unicodedata.normalize('NFKD', s.casefold())
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    return s.translate(str.maketrans({'ş':'s','ğ':'g','ö':'o','ü':'u','ç':'c'}))

def tokenize(s: str) -> set[str]:
    return {v for v in re.findall(r'[a-z0-9]{3,}', plain(s)) if v not in STOP}

def frontmatter(text: str) -> tuple[dict[str,str],str]:
    match = re.match(r'\A\ufeff?---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|$)', text, re.S)
    if not match:
        return {}, text
    meta = {}
    for line in match.group(1).splitlines():
        m = re.match(r'^([\w-]+)\s*:\s*(.*?)\s*$', line)
        if m:
            meta[m.group(1).lower()] = m.group(2).strip().strip('"\'')
    return meta, text[match.end():]

def scrub_body(text: str) -> str:
    text = re.sub(r'(?m)^\s*(?:kaynak(?:_url|_turu)?|source|url|tags|durum|status|dogrulama_tarihi)\s*:.*$', '', text, flags=re.I)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'(?m)^#{1,6}\s+', '', text)
    return ' '.join(plain(text).split())

def find_urls(s: str) -> list[str]:
    return re.findall(r'https?://[^\s<>\]"\')]+', s)

def scan(vault: Path) -> list[dict]:
    output=[]
    for file in sorted(vault.rglob('*.md')):
        try:
            rel = file.relative_to(vault)
            if any(p.startswith('.') or p.casefold() in EXCLUDED_DIRS for p in rel.parts) or file.is_symlink():
                continue
            raw = file.read_bytes()
            if len(raw) > 400000:
                continue
            text = raw.decode('utf-8-sig')
        except (OSError, UnicodeError, ValueError):
            continue
        meta, body = frontmatter(text)
        status = next((meta.get(k,'') for k in STATUS_KEYS if meta.get(k)), 'etiketsiz')
        urls = find_urls('\n'.join(meta.get(k,'') for k in SOURCE_KEYS))
        all_urls = find_urls(text)
        norm = scrub_body(body)
        output.append({'dosya':rel.as_posix(),'durum':status,'kaynak_url_sayisi':len(urls),
                       'metin_icinde_url_sayisi':len(all_urls), 'kaynak_baglanti_var':bool(urls or all_urls),
                       'kelime_sayisi':len(body.split()),'sha256':hashlib.sha256(raw).hexdigest(),
                       'govde_ozeti':hashlib.sha256(norm.encode('utf-8')).hexdigest(),
                       '_tokens':tokenize(norm), '_norm':norm})
    return output

def duplicates(items: list[dict]) -> tuple[list[dict],list[dict]]:
    groups=defaultdict(list)
    for i in items:
        if i['_norm']:
            groups[i['govde_ozeti']].append(i['dosya'])
    exact=[{'dosyalar':names, 'adet':len(names)} for names in groups.values() if len(names)>1]
    # Yakın tekrarlar yalnızca adaydır. Kaynaklari ayri notlar yanlis pozitif olabilir.
    index=defaultdict(list)
    for i, item in enumerate(items):
        tokens=item['_tokens']
        if len(tokens)<6: continue
        for tok in tokens:
            index[tok].append(i)
    candidates=Counter()
    for ids in index.values():
        if len(ids)>65: continue  # cok genel terimleri sayma
        for pos,a in enumerate(ids):
            for b in ids[pos+1:]:
                candidates[(a,b)]+=1
    near=[]
    for (a,b),shared in candidates.items():
        if shared<6: continue
        aa,bb=items[a],items[b]
        if aa['govde_ozeti']==bb['govde_ozeti']:continue
        common=shared/max(1,min(len(aa['_tokens']),len(bb['_tokens'])))
        if common<0.78:continue
        # normalize edilen metinler cok farkli boydaysa benzer bilgi olma ihtimali az
        shorter=min(len(aa['_norm']),len(bb['_norm']))
        longer=max(len(aa['_norm']),len(bb['_norm']))
        if shorter/max(1,longer)<0.62:continue
        ratio=SequenceMatcher(None,aa['_norm'][:5000],bb['_norm'][:5000]).ratio()
        if ratio>=0.76:
            near.append({'dosya_1':aa['dosya'],'dosya_2':bb['dosya'],'metin_benzerligi':round(ratio,3)})
    near.sort(key=lambda x:x['metin_benzerligi'],reverse=True)
    return exact,near[:250]

def save_report(vault:Path,outdir:Path):
    items=scan(vault)
    exact,near=duplicates(items)
    stat=Counter(i['durum'] for i in items)
    lacks=[i['dosya'] for i in items if not i['kaynak_baglanti_var']]
    summary={
        'tarih':datetime.now().astimezone().isoformat(timespec='seconds'),
        'kasa':str(vault),'toplam_not':len(items),'durumlar':dict(stat),
        'kaynak_url_yok_not':len(lacks),'tam_govde_tekrare_gruplari':len(exact),
        'yakin_tekrar_adaylari':len(near),
        'uyari':'Etiket ve URL varligi bilgi dogrulugu degildir; baglantilar internette kontrol edilmedi.'
    }
    outdir.mkdir(parents=True,exist_ok=True)
    (outdir/'denetim_ozet.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    (outdir/'tekrar_adaylari.json').write_text(json.dumps({'birebir':exact,'benzer':near},ensure_ascii=False,indent=2),encoding='utf-8')
    with (outdir/'not_katalogu.csv').open('w',encoding='utf-8-sig',newline='') as f:
        fields=['dosya','durum','kaynak_baglanti_var','kaynak_url_sayisi','metin_icinde_url_sayisi','kelime_sayisi','sha256']
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for i in items:writer.writerow({k:i[k] for k in fields})
    lines=['# GURKAN AI Bilgi Bankasi Denetimi','',f'Not: **{len(items)}**',
           f'Kaynak baglantisi bulunamayan: **{len(lacks)}**','',
           '## Durum etiketleri',*('- '+k+': '+str(v) for k,v in stat.most_common()),'',
           f'Birebir govde tekrar grubu: **{len(exact)}**',f'Yakin tekrar adayi: **{len(near)}**','',
           '## Kaynak baglantisi bulunamayan ilk 50 dosya',*('- '+x for x in lacks[:50]),'',
           '## Uyarilar','- Hicbir mevcut not degistirilmedi.',
           '- Baglanti olup olmadigi kontrol edildi; kaynak sayfasi okunmadi ve olgu dogrulanmadi.',
           '- Yakin tekrarlar otomatik silinmemeli; insan incelemesi gerektirir.',
           '- Not sayisi, benzersiz olgu sayisi ve RAG indeks parcasi birbirinden farklidir.']
    (outdir/'RAPOR.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print('Rapor klasoru:',outdir)

if __name__=='__main__':
    p=argparse.ArgumentParser(description='Obsidian salt-okunur bilgi bankasi kalite raporu')
    p.add_argument('--vault',default=DEFAULT_VAULT,help='Obsidian kasasi')
    p.add_argument('--out',default='GURKAN_AI_Bilgi_Denetim_Raporu',help='Kasadan AYRI rapor klasoru')
    args=p.parse_args()
    vault=Path(args.vault).resolve()
    outdir=Path(args.out).resolve()
    if not vault.is_dir():p.error('Obsidian kasasi bulunamadi: '+str(vault))
    if outdir == vault or vault in outdir.parents:
        p.error('Rapor klasoru Obsidian kasasinin DISINDA olmali.')
    save_report(vault,outdir)
