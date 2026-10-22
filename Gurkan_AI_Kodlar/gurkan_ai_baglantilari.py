#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GURKAN AI Obsidian Link Builder
- Default mode: read-only preview, creates CSV outside the vault.
- --apply: adds/replaces a marked "İlgili notlar" section in notes and makes a backup.
- Uses only Python standard library; recommendations are lexical, not guaranteed semantic truth.
"""
import argparse
import csv
import math
import re
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

TOKEN_RE = re.compile(r"[0-9A-Za-zÇĞİÖŞÜçğıöşü]{3,}", re.UNICODE)
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
MARKER_START = "<!-- GURKAN_AI_AUTO_LINKS_V1_START -->"
MARKER_END = "<!-- GURKAN_AI_AUTO_LINKS_V1_END -->"

STOP = set("""
ve veya ile için gibi olan olarak daha çok az bir bu şu o da de ki mi mı mu mü
ama ancak fakat çünkü ise üzere göre tarafından kadar sonra önce her tüm bazı
için içinde dışı olanların olanlar not bilgi sistem yapay zeka ai gurkan gürkan
the and for with from that this these those are was were into your you can use
how what when where why not all any each more less about into via based using
""".split())

SKIP_NAME_BITS = ("readme", "dizin", "katalog", "kalite_kontrol", "bilgi_agi_paket", "bilgi_ağı_paket")
SKIP_SUFFIXES = {".csv", ".txt", ".json", ".pdf"}

def tokens(text):
    out = []
    for t in TOKEN_RE.findall(text.lower()):
        t = t.strip()
        if t not in STOP and not t.isdigit():
            out.append(t)
    return out

def is_index_or_admin(path):
    s = path.as_posix().lower()
    n = path.stem.lower()
    return any(bit in n for bit in SKIP_NAME_BITS) or "/.obsidian/" in s

def display_title(path, content):
    # Use a simple frontmatter title if present; otherwise filename.
    m = re.search(r"(?m)^title:\s*[\"']?(.+?)[\"']?\s*$", content[:1500])
    if m:
        return m.group(1).strip().strip('"').strip("'")
    return path.stem.replace("_", " ").replace("-", " ")

def extract_existing_targets(content):
    targets = set()
    for raw in WIKILINK_RE.findall(content):
        raw = raw.strip().replace("\\", "/")
        targets.add(raw.lower())
        targets.add(Path(raw).stem.lower())
    return targets

def main():
    ap = argparse.ArgumentParser(description="Obsidian için güvenli iç bağlantı önerileri üretir.")
    ap.add_argument("--vault", required=True, help="Obsidian vault klasörünün yolu")
    ap.add_argument("--apply", action="store_true", help="Önerileri notlara yazar; önce yedek oluşturur")
    ap.add_argument("--links", type=int, default=3, help="Her nota önerilecek bağlantı sayısı (varsayılan 3)")
    ap.add_argument("--min-score", type=float, default=0.055, help="En düşük metin benzerliği eşiği (varsayılan 0.055)")
    args = ap.parse_args()

    vault = Path(args.vault).expanduser().resolve()
    if not vault.is_dir():
        raise SystemExit(f"Vault klasörü bulunamadı: {vault}")

    files = sorted(p for p in vault.rglob("*.md")
                   if p.is_file() and ".obsidian" not in p.parts)
    docs = []
    for p in files:
        try:
            content = p.read_text(encoding="utf-8-sig", errors="replace")
        except Exception:
            continue
        rel = p.relative_to(vault).as_posix()
        # Avoid using administration/index files as suggested targets, but keep them in the vault.
        title = display_title(p, content)
        title_tokens = tokens(title + " " + p.parent.name + " " + p.stem)
        body = content
        if body.startswith("---"):
            chunks = body.split("---", 2)
            if len(chunks) == 3:
                body = chunks[2]
        body_tokens = tokens(body[:10000])
        # Title and folder terms receive higher weight by repeating them.
        counts = Counter(body_tokens)
        counts.update({t: 3 * c for t, c in Counter(title_tokens).items()})
        docs.append({
            "path": p, "rel": rel, "content": content, "title": title,
            "counts": counts, "existing": extract_existing_targets(content),
            "admin": is_index_or_admin(p)
        })

    n = len(docs)
    if n < 2:
        raise SystemExit("Bağlantı önerisi üretmek için en az iki Markdown notu gerekir.")

    # TF-IDF vectors, standard-library implementation.
    df = Counter()
    for d in docs:
        for term in d["counts"]:
            df[term] += 1
    idf = {term: math.log(1 + n / (1 + freq)) + 1 for term, freq in df.items()}
    vecs, norms, postings = [], [], defaultdict(list)
    for i, d in enumerate(docs):
        v = {t: (1 + math.log(c)) * idf[t] for t, c in d["counts"].items() if c > 0}
        norm = math.sqrt(sum(x*x for x in v.values())) or 1.0
        v = {t: x / norm for t, x in v.items()}
        vecs.append(v)
        norms.append(norm)
        for term, weight in v.items():
            postings[term].append((i, weight))

    recommendations = []
    per_doc = [[] for _ in docs]
    for i, v in enumerate(vecs):
        scores = defaultdict(float)
        for term, wi in v.items():
            for j, wj in postings[term]:
                if i != j:
                    scores[j] += wi * wj
        candidates = []
        for j, score in scores.items():
            if score < args.min_score:
                continue
            # Admin notes are not targets; avoid self-folder utility links.
            if docs[j]["admin"]:
                continue
            # Avoid a link that is already present by filename or path.
            target_no_ext = docs[j]["rel"][:-3]
            if target_no_ext.lower() in docs[i]["existing"] or docs[j]["path"].stem.lower() in docs[i]["existing"]:
                continue
            candidates.append((score, j))
        candidates.sort(reverse=True)
        for score, j in candidates[:max(1, args.links)]:
            per_doc[i].append((j, score))
            recommendations.append({
                "source_path": docs[i]["rel"],
                "source_title": docs[i]["title"],
                "target_path": docs[j]["rel"],
                "target_title": docs[j]["title"],
                "similarity_score": round(score, 4),
                "status": "Öneri — otomatik benzerlik; insan kontrolü gerekir"
            })

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_csv = vault.parent / f"GURKAN_AI_Baglanti_Onizleme_{stamp}.csv"
    with report_csv.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "source_path", "source_title", "target_path", "target_title",
            "similarity_score", "status"
        ])
        writer.writeheader()
        writer.writerows(recommendations)

    changed = 0
    backup_dir = None
    if args.apply:
        backup_dir = vault.parent / f"GURKAN_AI_Baglanti_Yedek_{stamp}"
        backup_dir.mkdir(parents=True, exist_ok=False)
        for i, d in enumerate(docs):
            if not per_doc[i]:
                continue
            original = d["content"]
            # Replace only a previous section made by this script; preserve everything else.
            pattern = re.compile(
                re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END),
                flags=re.S
            )
            content = pattern.sub("", original).rstrip()
            lines = [MARKER_START, "## İlgili notlar (otomatik öneri)",
                     "", "> Bu bağlantılar metin benzerliğine göre önerilmiştir; içerik doğruluğu veya anlam ilişkisi garantisi değildir.", ""]
            for j, score in per_doc[i]:
                target = docs[j]
                target_path = target["rel"][:-3]
                lines.append(f"- [[{target_path}|{target['title']}]] *(benzerlik: {score:.3f})*")
            lines.append(MARKER_END)
            new_content = content + "\n\n" + "\n".join(lines) + "\n"
            if new_content != original:
                dest = backup_dir / d["rel"]
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(d["path"], dest)
                d["path"].write_text(new_content, encoding="utf-8", newline="\n")
                changed += 1

    print(f"Markdown notları tarandı: {n}")
    print(f"Bağlantı önerisi: {len(recommendations)}")
    print(f"Önizleme CSV: {report_csv}")
    if args.apply:
        print(f"Bağlantı bölümü eklenen/güncellenen not: {changed}")
        print(f"Yedek klasörü: {backup_dir}")
    else:
        print("Önizleme modu: Orijinal notlar değiştirilmedi.")
        print("CSV'yi kontrol ettikten sonra --apply ile bağlantıları yazabilirsin.")

if __name__ == "__main__":
    main()
