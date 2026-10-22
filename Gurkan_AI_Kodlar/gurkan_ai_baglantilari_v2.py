# -*- coding: utf-8 -*-
import argparse, csv, shutil, re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

START = "<!-- GURKAN_AI_AUTO_LINKS_V2_START -->"
END = "<!-- GURKAN_AI_AUTO_LINKS_V2_END -->"

def norm_rel(s):
    return (s or "").strip().replace("\\", "/")

def safe_path(root, rel):
    rel = norm_rel(rel)
    if not rel or rel.startswith("/") or ".." in Path(rel).parts:
        return None
    p = (root / Path(rel)).resolve()
    try:
        p.relative_to(root)
    except ValueError:
        return None
    return p

def main():
    ap = argparse.ArgumentParser(description="GURKAN AI Obsidian bağlantı ağı — güvenli v2")
    ap.add_argument("--vault", required=True)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--min-same-score", type=float, default=0.65)
    ap.add_argument("--min-bridge-score", type=float, default=0.60)
    ap.add_argument("--max-links", type=int, default=3)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    vault = Path(args.vault).resolve()
    csv_path = Path(args.csv).resolve()
    if not vault.is_dir(): raise SystemExit(f"Vault klasörü bulunamadı: {vault}")
    if not csv_path.is_file(): raise SystemExit(f"CSV bulunamadı: {csv_path}")
    raw=[]
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader=csv.DictReader(f)
        required={"source_path","source_title","target_path","target_title","similarity_score","baglanti_tipi"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise SystemExit("CSV başlıkları beklenen biçimde değil. Temizlenmiş aday CSV'sini kullan.")
        for r in reader:
            typ=(r.get("baglanti_tipi") or "").strip()
            try: score=float(r.get("similarity_score") or 0)
            except ValueError: continue
            if typ == "Aynı klasör / konu içi":
                if score < args.min_same_score: continue
            elif typ == "Klasörler arası köprü":
                if score < args.min_bridge_score: continue
            else: continue
            src=norm_rel(r.get("source_path")); tgt=norm_rel(r.get("target_path"))
            if not src or not tgt or src == tgt or not src.lower().endswith(".md") or not tgt.lower().endswith(".md"): continue
            pair=tuple(sorted((src.casefold(),tgt.casefold())))
            raw.append({"source_path":src,"source_title":r.get("source_title") or Path(src).stem,
                        "target_path":tgt,"target_title":r.get("target_title") or Path(tgt).stem,
                        "similarity_score":score,"baglanti_tipi":typ,"pair":pair})
    best={}
    for r in raw:
        if r["pair"] not in best or r["similarity_score"] > best[r["pair"]]["similarity_score"]:
            best[r["pair"]]=r
    candidates=sorted(best.values(), key=lambda x:x["similarity_score"], reverse=True)
    degree=defaultdict(int); selected=[]; skipped_missing=0
    for r in candidates:
        srcp=safe_path(vault,r["source_path"]); tgtp=safe_path(vault,r["target_path"])
        if srcp is None or tgtp is None or not srcp.is_file() or not tgtp.is_file():
            skipped_missing += 1; continue
        s=r["source_path"].casefold(); t=r["target_path"].casefold()
        if degree[s] >= max(1,args.max_links) or degree[t] >= max(1,args.max_links): continue
        selected.append(r); degree[s]+=1; degree[t]+=1
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    preview=vault.parent / f"GURKAN_AI_Baglanti_Agi_v2_Onizleme_{stamp}.csv"
    fields=["source_path","source_title","target_path","target_title","similarity_score","baglanti_tipi","status"]
    with preview.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in selected:
            row={k:r[k] for k in fields[:-1]}
            row["similarity_score"]=round(r["similarity_score"],4)
            row["status"]="Öneri; anlam doğruluğu garanti değil — uygulamadan önce kontrol et"
            w.writerow(row)
    print(f"CSV aday satırı (eşik sonrası, tekrarlar dahil): {len(raw)}")
    print(f"Benzersiz bağlantı adayı: {len(candidates)}")
    print(f"Seçilen bağlantı: {len(selected)}")
    print(f"Eksik/güvenli olmayan dosya yüzünden atlanan aday: {skipped_missing}")
    print(f"Önizleme CSV: {preview}")
    print(f"Kurallar: aynı konu >= {args.min_same_score:.2f}; klasörler arası köprü >= {args.min_bridge_score:.2f}; not başına azami {max(1,args.max_links)} seçili kenar.")
    if not args.apply:
        print("ÖNİZLEME MODU: Orijinal notlara hiçbir değişiklik yapılmadı.")
        print("Önizlemeyi kontrol etmeden --apply kullanma.")
        return
    marker_re=re.compile(re.escape(START)+r".*?"+re.escape(END),re.S)
    changes={}
    for r in selected:
        srcp=safe_path(vault,r["source_path"]); tgtp=safe_path(vault,r["target_path"])
        if srcp is None or tgtp is None or not srcp.is_file() or not tgtp.is_file(): continue
        rel=r["source_path"]
        if rel not in changes:
            original=srcp.read_text(encoding="utf-8-sig",errors="replace")
            changes[rel]={"path":srcp,"original":original,"targets":[]}
        changes[rel]["targets"].append(r)
    backup=vault.parent / f"GURKAN_AI_Baglanti_Yedek_v2_{stamp}"
    backup.mkdir(parents=True,exist_ok=False)
    changed=0
    for rel,item in changes.items():
        original=item["original"]
        content=marker_re.sub("",original).rstrip()
        lines=[START,"## İlgili notlar (GURKAN AI bağlantı ağı v2)","",
               "> Benzerlik puanı ve konu/klasör ilişkisine göre önerildi; içerik doğruluğu garanti edilmez.",""]
        seen_targets=set()
        for r in item["targets"]:
            target_rel=Path(r["target_path"]).with_suffix("").as_posix()
            if target_rel.casefold() in seen_targets: continue
            seen_targets.add(target_rel.casefold())
            title=(r["target_title"] or Path(target_rel).name).replace("|","/").replace("]","")
            lines.append(f"- [[{target_rel}|{title}]]")
        lines.append(END)
        new=content+"\n\n"+"\n".join(lines)+"\n"
        if new != original:
            dest=backup / Path(rel); dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(item["path"],dest)
            item["path"].write_text(new,encoding="utf-8",newline="\n")
            changed+=1
    print(f"Uygulandı. Değiştirilen not sayısı: {changed}")
    print(f"Yedek klasörü: {backup}")
    print("Obsidian'da grafiği yenileyip kontrol edebilirsin.")

if __name__ == "__main__": main()
