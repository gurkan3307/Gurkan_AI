"""
GURKAN AI - Tüm Notlara Otomatik Etiket Basıcı
Bu script, Obsidian kasasındaki tüm '.md' dosyalarını tarar ve 
'etiketsiz' olanlara önceden tanımlanmış standart bir YAML frontmatter basar.
"""

import os
import re
import time
from pathlib import Path

VAULT_PATH = Path(r"D:\GURKANUS27 Yapay Zeka\GURKAN_AI_Bilgi_Bankasi")

# Basılacak standart etiket şablonu (Eğer dosyada hiç etiket yoksa)
STANDART_FRONTMATTER = """---
kategori: "Otonom_Duzenleme"
etiketler: ["genel", "gurkan_ai_v3", "otomatik_etiketlendi"]
guvenilirlik_skoru: 50
kaynak: "Sistem_Ici"
tarih: "{tarih}"
---
"""

def has_frontmatter(content):
    """Dosyanın en üstünde '---' ile başlayan YAML formatı var mı kontrol eder."""
    lines = content.splitlines()
    if len(lines) > 0 and lines[0].strip() == "---":
        return True
    return False

def etiketleri_bas():
    if not VAULT_PATH.exists():
        print("Hata: Obsidian kasası bulunamadı!")
        return

    toplam_dosya = 0
    degisen_dosya = 0
    bugun = time.strftime('%Y-%m-%d')
    yeni_etiket = STANDART_FRONTMATTER.format(tarih=bugun)

    print("🔍 Tüm kasa taranıyor, etiketsiz dosyalara otomatik YAML basılacak...")
    
    for root, _, files in os.walk(VAULT_PATH):
        for file in files:
            if file.endswith(".md") and not file.startswith("."):
                toplam_dosya += 1
                dosya_yolu = Path(root) / file
                
                try:
                    with open(dosya_yolu, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    if not has_frontmatter(content):
                        # Dosyada frontmatter yok, en üste ekle
                        yeni_icerik = yeni_etiket + "\n" + content
                        with open(dosya_yolu, "w", encoding="utf-8") as f:
                            f.write(yeni_icerik)
                        degisen_dosya += 1
                        print(f"✅ Etiketlendi: {file}")
                except Exception as e:
                    print(f"⚠️ Hata ({file}): {e}")

    print(f"\nİşlem Tamamlandı!")
    print(f"Toplam Taranan Not: {toplam_dosya}")
    print(f"Yeni Etiket Basılan (Eksik) Not Sayısı: {degisen_dosya}")

if __name__ == "__main__":
    etiketleri_bas()
