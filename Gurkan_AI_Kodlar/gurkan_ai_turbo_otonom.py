"""
GURKAN AI - Turbo Otonom Bilgi Fabrikası (10x Hızlandırma)
- Toplu arama ve üretim (Batching)
- DuckDuckGo bekleme süreleri minimize edildi
- ThreadPoolExecutor ile eşzamanlı/paralel işlem desteği
"""

import os
import time
import concurrent.futures
from pathlib import Path
from ddgs import DDGS
from openai import OpenAI

VAULT_PATH = Path(r"D:\GURKANUS27 Yapay Zeka\GURKAN_AI_Bilgi_Bankasi")
HEDEF_KLASOR = VAULT_PATH / "09 - Otonom_Arastirma_Notlari"

LOCAL_PROVIDER = {
    "base_url": "http://127.0.0.1:1234/v1",
    "api_key": "lm-studio",
    "model": "qwen/qwen3-8b"
}

ANA_TEMA = "Geleceğin Yapay Zeka İş Modelleri ve B2B Otomasyon Sistemleri"
HEDEF_NOT_SAYISI = 250

def get_subtopics(client, count=50):
    prompt = f"'{ANA_TEMA}' konusunda birbirinden tamamen farklı, derinlemesine {count} adet spesifik alt başlık listele. Sadece başlıkları alt alta yaz, numara veya tire koyma."
    try:
        res = client.chat.completions.create(
            model=LOCAL_PROVIDER["model"],
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=1500
        )
        lines = [l.strip("- *0123456789.") for l in res.choices[0].message.content.split('\n') if l.strip()]
        return lines[:count]
    except Exception as e:
        print(f"Başlık hatası: {e}")
        return []

def fast_search(topic):
    try:
        results = DDGS().text(topic, region='tr-tr', max_results=2)
        return str(results) if results else "Özet bilgi."
    except Exception:
        return "Otomasyon ve yapay zeka sektör analizi."

def create_note_fast(client, topic, data):
    prompt = f"""Aşağıdaki konuyu Obsidian için YAML frontmatter ile profesyonel bir not olarak özetle:
Konu: {topic}
Veri: {data}

Format:
---
kategori: "Otonom_Mega_Uretim"
etiketler: ["otonom", "b2b_otomasyon", "gurkan_ai"]
guvenilirlik_skoru: 90
---
## Genel Bakış
## Temel Stratejiler
## B2B Uygulama ve Gelir Potansiyeli
"""
    try:
        res = client.chat.completions.create(
            model=LOCAL_PROVIDER["model"],
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=650
        )
        return res.choices[0].message.content.strip()
    except Exception:
        return None

def save_note(topic, content):
    if not HEDEF_KLASOR.exists():
        HEDEF_KLASOR.mkdir(parents=True, exist_ok=True)
    safe = "".join(c for c in topic if c.isalnum() or c in " _-").replace(" ", "_")[:45]
    path = HEDEF_KLASOR / f"Turbo_{safe}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path.name

def process_single(topic):
    client = OpenAI(base_url=LOCAL_PROVIDER["base_url"], api_key=LOCAL_PROVIDER["api_key"])
    data = fast_search(topic)
    content = create_note_fast(client, topic, data)
    if content:
        name = save_note(topic, content)
        return name
    return None

def main():
    print(f"⚡ GURKAN AI Turbo Üretim Başlatıldı! (Hedef: {HEDEF_NOT_SAYISI})\n")
    client = OpenAI(base_url=LOCAL_PROVIDER["base_url"], api_key=LOCAL_PROVIDER["api_key"])
    
    saved_count = 0
    while saved_count < HEDEF_NOT_SAYISI:
        topics = get_subtopics(client, count=30)
        if not topics:
            time.sleep(2)
            continue
        
        # 3 eşzamanlı iş parçacığıyla hızı 3 katına çıkar
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            results = executor.map(process_single, topics)
            for res in results:
                if res:
                    saved_count += 1
                    print(f"[{saved_count}/{HEDEF_NOT_SAYISI}] ⚡ Hızlı Kaydedildi: {res}")
                if saved_count >= HEDEF_NOT_SAYISI:
                    break
        print(f"--- Tur bitti. Mevcut üretim: {saved_count}/{HEDEF_NOT_SAYISI} ---")

if __name__ == "__main__":
    main()
