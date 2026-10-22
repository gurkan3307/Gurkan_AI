"""
GURKAN AI - Mega Otonom Bilgi Fabrikası (250'lik Bloklar)
Bu script, verdiğin tek bir ana konudan kendi kendine 250 alt başlık üretir,
bunları internette araştırır ve Obsidian kasana 250 yeni not olarak basar.
"""

import os
import time
from pathlib import Path
from duckduckgo_search import DDGS
from openai import OpenAI

# --- AYARLAR ---
VAULT_PATH = Path(r"D:\GURKANUS27 Yapay Zeka\GURKAN_AI_Bilgi_Bankasi")
HEDEF_KLASOR = VAULT_PATH / "09 - Otonom_Arastirma_Notlari"

LOCAL_PROVIDER = {
    "base_url": "http://127.0.0.1:1234/v1",
    "api_key": "lm-studio",
    "model": "qwen/qwen3-8b"
}

ANA_TEMA = "Geleceğin Yapay Zeka İş Modelleri ve Otomasyon Sistemleri"
HEDEF_NOT_SAYISI = 250

def get_subtopics_from_llm(client, theme, count=25):
    print(f"🧠 '{theme}' üzerine {count} adet yeni alt başlık düşünülüyor...")
    prompt = f"Ana konu: '{theme}'. Lütfen bu konuyla ilgili birbirinden farklı, spesifik ve detaylı {count} adet alt araştırma başlığı üret. Sadece başlıkları alt alta yaz, madde işareti veya numara kullanma."
    
    try:
        response = client.chat.completions.create(
            model=LOCAL_PROVIDER["model"],
            messages=[
                {"role": "system", "content": "Sen vizyoner bir sistem analistisin. Sadece istenen başlıkları liste halinde ver."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8
        )
        content = response.choices[0].message.content.strip()
        basliklar = [line.strip("- *1234567890.") for line in content.split('\n') if line.strip()]
        return basliklar[:count]
    except Exception as e:
        print(f"Başlık üretim hatası: {e}")
        return []

def web_search(query):
    try:
        results = DDGS().text(query, region='tr-tr', max_results=2)
        return str(results) if results else "Bilgi bulunamadı."
    except Exception:
        return "İnternet araması başarısız."

def generate_note_content(client, topic, search_data):
    prompt = f"""
    Aşağıdaki internet verilerini kullanarak Obsidian için profesyonel, detaylı bir not hazırla.
    Konu: {topic}
    Veri: {search_data}
    
    Markdown formatında (##) başlıklar ve maddeler kullan.
    En üste şu YAML frontmatter'ı ekle:
    ---
    kategori: "Otonom_Mega_Uretim"
    etiketler: ["otonom", "mega_arastirma", "bilgi_bankasi"]
    guvenilirlik_skoru: 85
    kaynak: "Web Search (DDGS)"
    ---
    """
    
    try:
        response = client.chat.completions.create(
            model=LOCAL_PROVIDER["model"],
            messages=[
                {"role": "system", "content": "Sen kıdemli bir araştırmacı ve sistem mühendisisin."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None

def save_to_obsidian(topic, content):
    if not HEDEF_KLASOR.exists():
        HEDEF_KLASOR.mkdir(parents=True)
        
    safe_title = "".join(c for c in topic if c.isalnum() or c in " _-").replace(" ", "_")[:50]
    filepath = HEDEF_KLASOR / f"Mega_{safe_title}.md"
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath.name

def run_mega_factory():
    print(f"🚀 GURKAN AI Mega Otonom Fabrika Başlıyor (Hedef: {HEDEF_NOT_SAYISI} Not)\n")
    client = OpenAI(base_url=LOCAL_PROVIDER["base_url"], api_key=LOCAL_PROVIDER["api_key"])
    
    toplam_uretilen = 0
    tur = 1
    
    while toplam_uretilen < HEDEF_NOT_SAYISI:
        print(f"\n--- TUR {tur} Başlıyor ---")
        basliklar = get_subtopics_from_llm(client, ANA_TEMA, count=10) # Her turda 10 başlık (stabilite için)
        
        if not basliklar:
            print("Başlık üretilemedi, 5 saniye bekleniyor...")
            time.sleep(5)
            continue
            
        for konu in basliklar:
            if toplam_uretilen >= HEDEF_NOT_SAYISI:
                break
                
            print(f"\n[{toplam_uretilen+1}/{HEDEF_NOT_SAYISI}] Araştırılıyor: {konu}")
            veri = web_search(konu)
            icerik = generate_note_content(client, konu, veri)
            
            if icerik:
                dosya_adi = save_to_obsidian(konu, icerik)
                print(f"✅ KAYDEDİLDİ: {dosya_adi}")
                toplam_uretilen += 1
            
            time.sleep(1) # Aşırı yüklenmeyi önlemek için
            
        tur += 1

    print(f"\n🎉 Mega üretim tamamlandı! Obsidian kasana {HEDEF_NOT_SAYISI} yeni not eklendi.")

if __name__ == "__main__":
    run_mega_factory()
