"""
GURKAN AI - Bilgi Bankası Yöneticisi v1.0 (FAZ 1: Nesnel ve Kusursuz Temel)
- Tekrar Kontrolü (Mükerrer notları tespit eder)
- Kaynak Doğrulaması (YAML'daki kaynakları denetler)
- Nesnellik Denetimi (Kaynaksız veya şüpheli notları raporlar)
"""

import os
import re
import hashlib
from pathlib import Path
from datetime import datetime

VAULT_PATH = Path(r"D:\GURKANUS27 Yapay Zeka\GURKAN_AI_Bilgi_Bankasi")
REPORT_DIR = Path(r"D:\GURKANUS27 Yapay Zeka\GURKAN_AI\GURKAN_AI_Bilgi_Denetim_Raporu")

def get_file_hash(content):
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def analyze_vault():
    if not VAULT_PATH.exists():
        print(f"Kasa bulunamadı: {VAULT_PATH}")
        return

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    total_notes = 0
    sourceless_notes = []
    duplicate_candidates = []
    content_hashes = {}

    print("==================================================")
    print("🧠 GURKAN AI BİLGİ BANKASI YÖNETİCİSİ v1.0")
    print("==================================================")
    print("🔍 Mükerrer kayıtlar ve kaynak doğrulaması yapılıyor...")

    for root, dirs, files in os.walk(VAULT_PATH):
        for file in files:
            if not file.endswith(".md"):
                continue

            total_notes += 1
            filepath = Path(root) / file
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            # Tekrar Kontrolü (Hash ile birebir aynı içerik tespiti)
            file_hash = get_file_hash(content)
            if file_hash in content_hashes:
                duplicate_candidates.append((file, content_hashes[file_hash]))
            else:
                content_hashes[file_hash] = file

            # Kaynak Kontrolü (YAML frontmatter içinde 'kaynak' veya 'kaynaklar' veya '[KAYNAK GEREKLİ]' geçiyor mu?)
            if not re.search(r'kaynak(lar)?\s*:', content, re.IGNORECASE) or '[KAYNAK GEREKLİ]' in content:
                sourceless_notes.append(file)

    # Rapor Oluşturma
    report_lines = [
        f"# 🧠 GURKAN AI Bilgi Bankası Denetim Raporu",
        f"**Tarih:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Toplam Taranan Not:** {total_notes}\n",
        f"## ⚠️ Mükerrer (Kopya) Notlar ({len(duplicate_candidates)})",
        "Aynı içeriğe sahip birebir kopya dosyalar:"
    ]

    if duplicate_candidates:
        for dup1, dup2 in duplicate_candidates:
            report_lines.append(f"- `{dup1}` <-> `{dup2}`")
    else:
        report_lines.append("- Kopya not bulunmadı. Sistem temiz.")

    report_lines.append(f"\n## 🚨 Kaynaksız / Doğrulanmamış Notlar ({len(sourceless_notes)})")
    report_lines.append("Güvenilirlik standardına uymayan veya kaynak etiketi eksik olan notlar:")
    if sourceless_notes:
        for sn in sourceless_notes:
            report_lines.append(f"- [EKSİK/ŞÜPHELİ KAYNAK] `{sn}`")
    else:
        report_lines.append("- Tüm notlar kaynaklı ve nesnel. Kasa kusursuz.")

    report_content = "\n".join(report_lines)
    report_file = REPORT_DIR / f"Denetim_Raporu_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    report_file.write_text(report_content, encoding="utf-8")

    print(f"✅ Tarama Tamamlandı! Toplam Not: {total_notes}")
    print(f"⚠️ Kopya Dosyalar: {len(duplicate_candidates)}")
    print(f"🚨 Kaynaksız/Şüpheli Notlar: {len(sourceless_notes)}")
    print(f"\n📄 Detaylı yönetici raporu oluşturuldu: {report_file}")

if __name__ == "__main__":
    analyze_vault()
