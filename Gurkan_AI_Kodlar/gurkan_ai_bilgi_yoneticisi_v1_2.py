"""GURKAN AI Bilgi Bankasi Yoneticisi v1.2 - salt okunur Markdown kalite tarayici.
Standart Python kutuphanesi disinda bagimliligi yoktur. Internetten dogrulama yapmaz.
"""
from __future__ import annotations
import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_VAULT = r'D:\GURKANUS27 Yapay Zeka\GURKAN_AI_Bilgi_Bankasi'
SOURCE_FIELDS = ('kaynak_url', 'kaynak', 'source_url', 'referans', 'references', 'url')
STATUS_FIELDS = ('durum', 'status')
URL_RE = re.compile(r'https?://[^\s<>\]"\']+', re.I)
HEADER_RE = re.compile(r'(?m)^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$')
WORD_RE = re.compile(r'\b[^\W_]+(?:[-’\'][^\W_]+)*\b', re.UNICODE)


def split_frontmatter(raw: str):
    text = raw.lstrip('\ufeff')
    m = re.match(r'\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)', text, re.S)
    if not m:
        return {}, text, False
    meta = {}
    for line in m.group(1).splitlines():
        match = re.match(r'^([\w-]+):\s*(.*)$', line)
        if match:
            meta[match.group(1).lower()] = match.group(2).strip().strip('"\'')
    return meta, text[m.end():], True


def content_text(body: str) -> str:
    """Baslik, kod bloklari ve Markdown isaretlerini kaba bicimde cikartir."""
    body = re.sub(r'```[\s\S]*?```', ' ', body)
    body = re.sub(r'(?m)^\s{0,3}#{1,6}\s+.*$', ' ', body)
    body = re.sub(r'!?(?:\[([^\]]*)\])\([^)]*\)', r'\1', body)
    body = re.sub(r'(?m)^\s*[-*+]\s+', '', body)
    return body


def find_empty_sections(body: str) -> list[str]:
    headers = list(HEADER_RE.finditer(body))
    empty = []
    for i, h in enumerate(headers):
        end = headers[i+1].start() if i+1 < len(headers) else len(body)
        segment = body[h.end():end]
        # HTML aciklamalari, ayiricilar, bos listeler gercek icerik degildir.
        segment = re.sub(r'<!--.*?-->', '', segment, flags=re.S)
        segment = re.sub(r'(?m)^\s*(?:---|\*\*\*|___)\s*$', '', segment)
        if not WORD_RE.search(content_text(segment)):
            empty.append(h.group(2).strip())
    return empty


def inspect(path: Path, root: Path, min_words: int):
    raw = path.read_text(encoding='utf-8-sig')
    meta, body, has_meta = split_frontmatter(raw)
    word_count = len(WORD_RE.findall(content_text(body)))
    urls = sorted(set(u.rstrip('.,;)') for u in URL_RE.findall(raw)))
    source_urls = sorted(set(u.rstrip('.,;)') for k, v in meta.items() if k in SOURCE_FIELDS for u in URL_RE.findall(v)))
    status = next((meta[k] for k in STATUS_FIELDS if meta.get(k)), 'etiketsiz')
    trust_fields = [k for k in meta if any(x in k for x in ('guvenilirlik', 'confidence', 'trust_score', 'dogruluk_puani'))]
    empty = find_empty_sections(body)
    reasons = []
    if not source_urls and not urls:
        reasons.append('kaynak_url_yok')
    elif urls and not source_urls:
        reasons.append('kaynak_url_metadata_disinda')
    if not has_meta:
        reasons.append('yaml_ust_bilgi_yok')
    if empty:
        reasons.append('bos_baslik')
    if word_count < min_words:
        reasons.append('kisa_govde')
    if trust_fields:
        reasons.append('kanitsiz_guven_puani_incele')
    if status.casefold() in ('taslak', 'etiketsiz', 'kaynak_incelemesi_bekliyor'):
        reasons.append('inceleme_bekliyor')
    score = 50*('kaynak_url_yok' in reasons) + 20*('bos_baslik' in reasons) + 15*('kisa_govde' in reasons) + 15*('kanitsiz_guven_puani_incele' in reasons) + 10*('yaml_ust_bilgi_yok' in reasons)
    return dict(dosya=path.relative_to(root).as_posix(), durum=status,
                govde_kelime_sayisi=word_count, bos_baslik_sayisi=len(empty),
                bos_basliklar=' | '.join(empty[:12]), kaynak_url_sayisi=len(urls),
                ust_bilgide_kaynak_url_sayisi=len(source_urls),
                ilk_kaynak=urls[0] if urls else '', guven_puani_alanlari=' | '.join(trust_fields),
                inceleme_onceligi=score, nedenler=';'.join(reasons))


def main():
    p = argparse.ArgumentParser(description='GURKAN AI salt okunur icerik kalite denetimi')
    p.add_argument('--vault', default=DEFAULT_VAULT)
    p.add_argument('--out', default='GURKAN_AI_Bilgi_Denetim_Raporu_v1_2')
    p.add_argument('--min-words', type=int, default=60)
    args = p.parse_args()
    vault = Path(args.vault).resolve()
    out = Path(args.out).resolve()
    if not vault.is_dir():
        p.error('Obsidian kasasi bulunamadi: ' + str(vault))
    if out == vault or vault in out.parents or out == vault.parent:
        p.error('Rapor klasoru Obsidian kasasinin disinda olmali')
    if args.min_words < 0:
        p.error('--min-words sifirdan kucuk olamaz')
    rows = []
    errors = []
    for path in sorted(vault.rglob('*.md')):
        rel = path.relative_to(vault)
        if any(x.startswith('.') for x in rel.parts) or not path.is_file():
            continue
        try:
            rows.append(inspect(path, vault, args.min_words))
        except (OSError, UnicodeError) as exc:
            errors.append({'dosya': rel.as_posix(), 'hata': str(exc)})
    rows.sort(key=lambda r: (-r['inceleme_onceligi'], r['dosya'].casefold()))
    counts = Counter()
    statuses = Counter(r['durum'] for r in rows)
    for r in rows:
        for reason in filter(None, r['nedenler'].split(';')):
            counts[reason] += 1
    report = dict(tarih=datetime.now().astimezone().isoformat(timespec='seconds'),
                  toplam_not=len(rows), okunamayan_not=len(errors), durumlar=dict(statuses),
                  bulgular=dict(counts),
                  uyari='Bu rapor notlarin dogrulugunu, URL erisilebilirligini veya kaynak-iddia eslesmesini kanitlamaz.')
    out.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else ['dosya', 'durum', 'nedenler']
    with (out/'INCELEME_KUYRUGU_v1_2.csv').open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    (out/'OZET_v1_2.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = ['# GURKAN AI Bilgi Bankasi - v1.2 Denetim', '',
             f"- Taranan not: {len(rows)}", f"- Okunamayan: {len(errors)}", '',
             '## Bulgular', *[f'- {key}: {value}' for key,value in counts.most_common()],
             '', '## Oncelikli 20 not',
             *[f"- {r['inceleme_onceligi']} puan | {r['dosya']} | {r['nedenler']}" for r in rows[:20]],
             '', '## Sinirlar',
             '- Kisa notlar her zaman hatali degildir; kisa olduklari icin incelemeye adaydir.',
             '- Proje planlari gibi dahili notlar icin dis kaynak URL zorunlu olmayabilir.',
             '- Guven puani metaverisi bilimsel dogrulama sayilmaz.',
             '- Yazilim Obsidian notlarini silmez veya degistirmez; raporlar disindaki dosyalara yazmaz.',
             '- Internet baglantisi veya AI modeli kullanmaz; kaynaklarin gercekten iddiayi destekledigini test etmez.']
    (out/'RAPOR_v1_2.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    if errors:
        (out/'OKUNAMAYANLAR.json').write_text(json.dumps(errors, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print('Rapor klasoru:', out)

if __name__ == '__main__':
    main()
