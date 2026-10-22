"""
GURKAN_AI - Kanıt Ajanı v1.0 (FAZ 1: Nesnel ve Kusursuz Temel)
- Kaynaksız notları okur.
- İçeriklerindeki temel iddiaları DuckDuckGo Search ile araştırır.
- Doğrulanmış kaynak linklerini nota ekler.
"""

import os
import re
from pathlib import Path
from duckduckgo_search import DDGS

VAULT_PATH = Path(r"D:\GURKANUS27 Yapay Zeka\GURKAN_AI_Bilgi_Bankasi")

def web_search(query):
    try:
        results = DDGS().text(query, region='tr-tr', max_results=2)
        if results:
            links = [r.get('href', '') for r in results if r.get('href')]
            return links
        return []
    except Exception as e:
        print(f"Arama hatası: {e}")
        return []

def process_sourceless_notes():
    if not VAULT_PATH.exists():
        print(f"Kasa bulunamadı: {VAULT_PATH}")
        return

    processed_count = 0
    print("==================================================")
    print("🧠 GURKAN_AI KANIT AJANI v1.0")
    print("==================================================")
    print("🔍 Kaynaksız notlar internet üzerinden doğrulanıyor...\n")

    for root, dirs, files in os.walk(VAULT_PATH):
        for file in files:
            if not file.endswith(".md"):
                continue

            filepath = Path(root) / file
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            # Kaynaksız not tespiti (Bilgi Bankası Yöneticisi v1.0 mantığı)
            if not re.search(r'kaynak(lar)?\s*:', content, re.IGNORECASE) or '[KAYNAK GEREKLİ]' in content:
                print(f"🔄 İşleniyor: {file}")
                
                # Basit bir konu çıkarma (Dosya adından)
                topic = file.replace(".md", "").replace("_", " ")
                links = web_search(topic)

                if links:
                    kaynak_listesi = "\n".join([f"  - \"{link}\"" for link in links])
                    
                    # Eğer YAML bloğu varsa kaynakları ekle, yoksa en üste YAML oluştur
                    if content.startswith("---"):
                        # Mevcut YAML bloğunu bul
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            yaml_content = parts[1]
                            body = parts[2]
                            
                            if '[KAYNAK GEREKLİ]' in yaml_content:
                                yaml_content = yaml_content.replace('[KAYNAK GEREKLİ]', '')
                                yaml_content = yaml_content.rstrip() + f"\nkaynaklar:\n{kaynak_listesi}\n"
                            elif not re.search(r'kaynak(lar)?\s*:', yaml_content, re.IGNORECASE):
                                yaml_content = yaml_content.rstrip() + f"\nkaynaklar:\n{kaynak_listesi}\n"
                                
                            new_content = f"---{yaml_content}---{body}"
                        else:
                             new_content = f"---\nkaynaklar:\n{kaynak_listesi}\n---\n{content}"
                    else:
                        new_content = f"---\nkaynaklar:\n{kaynak_listesi}\n---\n{content}"
                        
                    # [KAYNAK GEREKLİ] etiketini gövdeden de temizle
                    new_content = new_content.replace('[KAYNAK GEREKLİ]', '')
                    
                    try:
                        filepath.write_text(new_content, encoding="utf-8")
                        print(f"  ✅ Kaynak eklendi: {len(links)} adet.")
                        processed_count += 1
                    except Exception as e:
                        print(f"  ❌ Yazma hatası: {e}")
                else:
                    print(f"  ⚠️ Kaynak bulunamadı.")

    print("\n==================================================")
    print(f"✅ İşlem Tamamlandı! Toplam {processed_count} not doğrulandı ve güncellendi.")

if __name__ == "__main__":
    process_sourceless_notes()
