"""
GURKAN AI - Otonom Bilgi Fabrikası (250 -> 500+ Hedefi)
İnternette araştırma yapar ve sonuçları Obsidian'a otomatik not olarak kaydeder.
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

# --- OTONOM ARAŞTIRMA KONULARI ---
ARASTIRMA_KONULARI = [
    "Yapay Zeka B2B Satış Stratejileri",
    "Python FastAPI ile Mikroservis Mimarisi",
    "İleri Seviye RAG (Retrieval-Augmented Generation) Teknikleri",
    "Otonom AI Ajanları İçin Hafıza Yönetimi",
    "Endüstriyel Otomasyonda Yapay Zeka Kullanımı"
]

def web_search(query):
    print(f"🔍 İnternette aranıyor: {query}")
    try:
        results = DDGS().text(query, region='tr-tr', max_results=3)
        return str(results) if results else "Bilgi bulunamadı."
    except Exception as e:
        return f"Hata: {e}"

def generate_note_content(topic, search_data):
    print(f"🧠 {topic} için Obsidian notu derleniyor...")
    client = OpenAI(base_url=LOCAL_PROVIDER["base_url"], api_key=LOCAL_PROVIDER["api_key"])
    
    prompt = f"""
    Aşağıdaki internet arama verilerini kullanarak Obsidian için profesyonel bir not hazırla.
    Konu: {topic}
    Veri: {search_data}
    
    Lütfen Markdown formatında, net başlıklar (##) ve madde işaretleri kullanarak yaz.
    En üste şu YAML frontmatter'ı ekle:
    ---
    kategori: "Otonom_Arastirma"
    etiketler: ["otonom", "gurkan_ai_v3", "arastirma"]
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
    except Exception as e:
        print(f"AI Üretim Hatası: {e}")
        return None

def save_to_obsidian(topic, content):
    if not HEDEF_KLASOR.exists():
        HEDEF_KLASOR.mkdir(parents=True)
        
    safe_title = topic.replace(" ", "_").replace("/", "_")
    filepath = HEDEF_KLASOR / f"Otonom_{safe_title}.md"
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ [KAYDEDİLDİ] {filepath.name}\n")

def run_autonomous_factory():
    print("🚀 GURKAN AI Otonom Bilgi Fabrikası Başlıyor (Hedef: 500+ Not)\n")
    for topic in ARASTIRMA_KONULARI:
        data = web_search(topic)
        content = generate_note_content(topic, data)
        if content:
            save_to_obsidian(topic, content)
        time.sleep(2)
    print("🎉 Otonom üretim turu tamamlandı!")

if __name__ == "__main__":
    run_autonomous_factory()
