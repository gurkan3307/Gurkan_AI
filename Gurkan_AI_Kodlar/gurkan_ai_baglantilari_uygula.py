# -*- coding: utf-8 -*-
import argparse, csv, shutil, re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

START = "<!-- GURKAN_AI_AUTO_LINKS_V2_START -->"
END = "<!-- GURKAN_AI_AUTO_LINKS_V2_END -->"

def main():
    p = argparse.ArgumentParser(description="GURKAN AI bağlantı uygulama aracı")
    p.add_argument("--vault", required=True)
    p.add_argument("--csv", required=True, help="Temizlenmiş aday CSV dosyası")
    p.add_argument("--min-score", type=float, default=0.50)
    p.add_argument("--max-links", type=int, default=2)
    p.add_argument("--apply", action="store_true", help="Yedek alıp bağlantıları uygula")
    args = p.parse_args()

    vault = Path(args.vault).resolve()
    csv_path = Path(args.csv).resolve()
    if not vault.is_dir():
        raise SystemExit(f"Vault bulunamadı: {vault}")
    if not csv_path.is_file():
        raise SystemExit(f"CSV bulunamadı: {csv_path}")

    rows=[]
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r.get("baglanti_tipi") != "Aynı klasör / konu içi":
                continue
            try: score=float(r.get("similarity_score","0"))
            except: continue
            if score < args.min_score: continue
            src=(r.get("source_path") or "").replace("\\","/")
            tgt=(r.get("target_path") or "").replace("\\","/")
            # Guard against absolute paths and traversal.
            if not src or not tgt or src.startswith("/") or tgt.startswith("/") or ".." in Path(src).parts or ".." in Path(tgt).parts:
                continue
            if not src.lower().endswith(".md") or not tgt.lower().endswith(".md") or src == tgt:
                continue
            rows.append({
                "source_path":src, "source_title":r.get("source_title") or Path(src).stem,
                "target_path":tgt, "target_title":r.get("target_title") or Path(tgt).stem,
                "score":score
            })

    # Highest-scoring targets first; cap links per source.
    rows.sort(key=lambda x:(x["source_path"], -x["score"], x["target_path"]))
    by_source=defaultdict(list)
    seen=set()
    for r in rows:
        key=(r["source_path"],r["target_path"])
        if key in seen: continue
        seen.add(key)
        if len(by_source[r["source_path"]]) < max(1,args.max_links):
            by_source[r["source_path"]].append(r)

    selected=[r for values in by_source.values() for r in values]
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    preview= vault.parent / f"GURKAN_AI_Baglanti_Uygulama_Onizleme_{stamp}.csv"
    with preview.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["source_path","source_title","target_path","target_title","similarity_score","status"])
        w.writeheader()
        for r in selected:
            w.writerow({"source_path":r["source_path"],"source_title":r["source_title"],"target_path":r["target_path"],"target_title":r["target_title"],"similarity_score":round(r["score"],4),"status":"Aynı klasör + puan eşiği; yine de otomatik aday"})

    print(f"Seçilen bağlantı adayı: {len(selected)}")
    print(f"Kaynak not sayısı: {len(by_source)}")
    print(f"Önizleme CSV: {preview}")
    print("Kural: aynı klasör/konu, puan >= %.2f, not başına en fazla %d bağlantı."%(args.min_score,args.max_links))
    if not args.apply:
        print("ÖNİZLEME MODU: Vault notları değiştirilmedi.")
        print("Uygulamayı kabul edersen aynı komutu sonuna --apply ekleyebilirsin.")
        return

    # Validate every path before any write; make a full backup of each affected note.
    affected=[]
    for src, recs in by_source.items():
        path=(vault / Path(src)).resolve()
        if not path.is_relative_to(vault) or not path.is_file():
            print(f"ATLANDI (kaynak bulunamadı/güvenli değil): {src}")
            continue
        targets=[]
        for r in recs:
            target=(vault / Path(r["target_path"])).resolve()
            if target.is_relative_to(vault) and target.is_file():
                targets.append((r,target))
            else:
                print(f"ATLANDI (hedef bulunamadı/güvenli değil): {r['target_path']}")
        if targets: affected.append((src,path,targets))

    backup=vault.parent / f"GURKAN_AI_Baglanti_Yedek_{stamp}"
    backup.mkdir(parents=True,exist_ok=False)
    changed=0
    marker_re=re.compile(re.escape(START)+r".*?"+re.escape(END),re.S)
    for rel,path,targets in affected:
        original=path.read_text(encoding="utf-8-sig",errors="replace")
        content=marker_re.sub("",original).rstrip()
        section=[START,"## İlgili notlar (otomatik öneri)","","> Aynı klasör/konu ve metin benzerliğine göre üretildi; bağlantıların anlamsal doğruluğu garanti edilmez.",""]
        for r,target in targets:
            target_rel=Path(r["target_path"]).with_suffix("").as_posix()
            title=r["target_title"].replace("|","/")
            section.append(f"- [[{target_rel}|{title}]]")
        section.append(END)
        new=content+"\n\n"+"\n".join(section)+"\n"
        if new != original:
            dest=backup / Path(rel)
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(path,dest)
            path.write_text(new,encoding="utf-8",newline="\n")
            changed+=1
    print(f"Değiştirilen not: {changed}")
    print(f"Yedek klasörü: {backup}")
    print("Obsidian'da Graph View'u yeniden açıp kontrol et.")

if __name__=="__main__":
    main()
