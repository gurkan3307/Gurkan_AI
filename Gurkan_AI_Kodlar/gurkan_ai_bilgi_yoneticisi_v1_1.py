"""GURKAN AI Bilgi Bankasi Yoneticisi v1.1 — salt okunur kalite onceliklendirmesi.

v1.0 tarayicisini kullanir; URL'leri acmaz, bilginin dogrulugunu iddia etmez.
Obsidian kasasina veya RAG veritabanina yazmaz.
"""
from __future__ import annotations
import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from gurkan_ai_bilgi_yoneticisi_v1 import scan, duplicates, DEFAULT_VAULT, find_urls, frontmatter, SOURCE_KEYS

DRAFT = {'taslak', 'etiketsiz', 'kaynak_incelemesi_bekliyor', 'kaynak_sayfasi_incelendi_tekil_iddia_denetimi_acik'}

def main():
    p=argparse.ArgumentParser(description='GURKAN AI salt okunur kaynak ve tekrar kalite kuyrugu')
    p.add_argument('--vault',default=DEFAULT_VAULT)
    p.add_argument('--out',default='GURKAN_AI_Bilgi_Denetim_Raporu_v1_1')
    a=p.parse_args()
    vault=Path(a.vault).resolve(); out=Path(a.out).resolve()
    if not vault.is_dir():p.error('Kasa klasoru bulunamadi: '+str(vault))
    if out==vault or vault in out.parents:p.error('Rapor klasoru kasa disinda olmali')
    rows=scan(vault); exact,near=duplicates(rows)
    queue=[]; domains=Counter(); source_groups=defaultdict(list)
    for item in rows:
        path=vault/item['dosya']
        text=path.read_text(encoding='utf-8-sig')
        meta,_=frontmatter(text)
        urls=find_urls('\n'.join(meta.get(k,'') for k in SOURCE_KEYS)) or find_urls(text)
        urls=list(dict.fromkeys(u.rstrip('.,;') for u in urls))
        for u in urls:
            host=urlparse(u).hostname or ''
            if host: domains[host.lower()]+=1
        reasons=[]; score=0
        if not urls:reasons.append('kaynak_url_eksik');score+=50
        if item['durum'].casefold() in DRAFT:reasons.append('inceleme_bekliyor');score+=25
        if item['kelime_sayisi']<25:reasons.append('cok_kisa_not');score+=10
        if len(urls)>0 and not any(urlparse(u).scheme in ('https','http') for u in urls):reasons.append('kaynak_bicimi');score+=10
        if not meta:reasons.append('on_bilgi_yok');score+=15
        if urls:
            source_groups[urls[0]].append(item['dosya'])
        queue.append({'oncelik_puani':score,'dosya':item['dosya'],'durum':item['durum'],
                      'kelime_sayisi':item['kelime_sayisi'],'url_sayisi':len(urls),
                      'ilk_kaynak':urls[0] if urls else '', 'nedenler':';'.join(reasons)})
    queue.sort(key=lambda r:(-r['oncelik_puani'],r['dosya']))
    # Kaynak paylasimi tekrar kaniti degildir. Ayrica ayni URL'li notlar listelenir.
    shared=[{'kaynak':u,'not_sayisi':len(files),'dosyalar':files} for u,files in source_groups.items() if len(files)>1]
    shared.sort(key=lambda x:-x['not_sayisi'])
    out.mkdir(parents=True,exist_ok=True)
    def save_csv(file, data, cols):
        with (out/file).open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(data)
    save_csv('INCELEME_KUYRUGU.csv',queue,list(queue[0]) if queue else ['dosya'])
    save_csv('KAYNAK_ALANLARI.csv',[{'alan':d,'not_sayisi':n} for d,n in domains.most_common()],['alan','not_sayisi'])
    (out/'TEKRAR_ADAYLARI.json').write_text(json.dumps({'birebir':exact,'yakin':near,'ayni_url':shared},ensure_ascii=False,indent=2),encoding='utf-8')
    statuses=Counter(r['durum'] for r in rows)
    missing=sum(not r['url_sayisi'] for r in queue)
    summary={'tarih':datetime.now().astimezone().isoformat(timespec='seconds'),
             'not_sayisi':len(rows),'kaynak_url_eksik':missing,'durumlar':dict(statuses),
             'birebir_tekrar_grubu':len(exact),'yakin_tekrar_adayi':len(near),'birden_cok_nota_ait_url':len(shared),
             'uyari':'URL varligi, kaynak okunmasi, kaynak dogrulamasi ve olgu dogrulamasi birbirinden farklidir.'}
    (out/'OZET.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    md=['# GURKAN AI Bilgi Bankasi — v1.1 Kalite Raporu','',f'- Taranan not: **{len(rows)}**',
        f'- Kaynak URL bulunamayan: **{missing}**',f'- Birebir tekrar grubu: **{len(exact)}**',
        f'- Benzer metin adayi: **{len(near)}**',f'- Birden cok notta kullanilan kaynak URL: **{len(shared)}**','',
        '## Durum etiketleri',*[f'- {k}: {v}' for k,v in statuses.most_common()],'',
        '## Ilk 20 inceleme adayi',*[f"- {i['oncelik_puani']} puan | {i['dosya']} | {i['nedenler']}" for i in queue[:20]],'',
        '## Sinirlar','- Bu yazilim internet kaynaklarina baglanmaz; URL iceriklerini denetlemez.',
        '- Inceleme puani dogruluk puani degildir; sadece oncelik siralamasi yapar.',
        '- Kasa dosyalarini ve veritabanlarini degistirmez.','- Raporlar sadece --out klasorune yazilir.']
    (out/'RAPOR.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print('Rapor:',out)

if __name__=='__main__':main()
