"""
GURKAN AI 5.0+ — Büyük Bilgi Paketleri Fabrikası (25.000+ Hedefi İçin Adım Adım Üretim)
5 Ana Sektörel Pakette Kaynaklı, Tekrarsız ve Yüksek Kaliteli Obsidian Notları Üretir.
"""

import os
import time
import concurrent.futures
from pathlib import Path
from duckduckgo_search import DDGS
from openai import OpenAI

VAULT_PATH = Path(r"D:\GURKANUS27 Yapay Zeka\GURKAN_AI_Bilgi_Bankasi")

LOCAL_PROVIDER = {
    "base_url": "http://127.0.0.1:1234/v1",
    "api_key": "lm-studio",
    "model": "qwen/qwen3-8b"
}

BILGI_PAKETLERI = {
    "1": {
        "klasor": "Paket_01_ETicaret_ve_Katalog",
        "tema": "E-Ticaret Otomasyonu, Dönüşüm Optimizasyonu, SEO Katalog Yazımı ve Pazaryeri Stratejileri",
        "hedef_adet": 250
    },
    "2": {
        "klasor": "Paket_02_B2B_Is_Akisi_Otomasyonu",
        "tema": "KOBİ Otomasyonları, Fatura/Belge Okuma (OCR), Stok Uyarı ve Müşteri Raporlama Sistemleri",
        "hedef_adet": 250
    },
    "3": {
        "klasor": "Paket_03_Medya_ve_Icerik_Studyosu",
        "tema": "YouTube Senaryo Mühendisliği, Viral Kanca (Hook) Tasarımı, Bülten Yazarlığı ve Dijital Pazarlama",
        "hedef_adet": 250
    },
    "4": {
        "klasor": "Paket_04_Kod_ve_Veri_Analiz_Mimarisi",
        "tema": "Python Otomasyon Kütüphaneleri, Pandas Veri Analizi, SQLite Vektör Veritabanları ve RAG Sistemleri",
        "hedef_adet": 250
    },
    "5": {
        "klasor": "Paket_05_SaaS_ve_Gelir_Modelleri",
        "tema": "B2B Yapay Zeka Satış Stratejileri, SaaS Fiyatlandırma, Müşteri Edinme ve Ajans Otomasyonu",
        "hedef_adet": 250
    }
}

def get_subtopics(client, theme, count=30):
    prompt = (
        f"Ana Konu: '{theme}'.\n"
        f"Bu konuyla ilgili birbirinden tamamen farklı, spesifik, teknik ve ticari değeri yüksek {count} adet alt araştırma başlığı üret. "
        "Sadece başlıkları alt alta yaz, numara veya madde işareti koyma. /no_think"
    )
    try:
        res = client.chat.completions.create(
            model=LOCAL_PROVIDER["model"],
            messages=[{"role": "user", "content": prompt}],
            temperature=0.85,
            max_tokens=1200
        )
        lines = [l.strip("- *0123456789.()") for l in res.choices[0].message.content.split('\n') if len(l.strip()) > 8]
        return lines[:count]
    except Exception as e:
        print(f"Başlık üretim hatası: {e}")
        return []

def search_with_sources(topic):
    try:
        results = DDGS().text(topic, region='tr-tr', max_results=3)
        if not results:
            return "Kaynak bulunamadı.", []
        ozet = "\n".join([f"- {r.get('title','')}: {r.get('body','')}" for r in results])
        linkler = [r.get('href', '') for r in results if r.get('href')]
        return ozet, linkler
    except Exception:
        return "Genel sektör bilgisi.", []

def generate_sourced_note(client, topic, search_data, links, folder_name):
    kaynak_listesi = "\n".join([f'  - "{link}"' for link in links]) if links else '  - "Yerel Sentez"'
    prompt = f"""Aşağıdaki konuyu ve internet bulgularını kullanarak Obsidian bilgi bankası için kapsamlı, profesyonel bir bilgi notu yaz.
Konu: {topic}
Web Bulguları:
{search_data}

Lütfen en üste şu YAML bloğunu koruyarak başla ve altındaki başlıkları detaylıca doldur:
---
kategori: "{folder_name}"
etiketler: ["gurkan_ai_5", "bilgi_paketi", "kaynakli_not"]
kaynaklar:
{kaynak_listesi}
---
# {topic}
## 1. Yönetici Özeti ve Temel Kavramlar
## 2. Teknik Mimari ve Uygulama Adımları
## 3. B2B Ticari Kullanım ve Gelir Potansiyeli
## 4. Kritik Metrikler ve Dikkat Edilecekler
/no_think"""

    try:
        res = client.chat.completions.create(
            model=LOCAL_PROVIDER["model"],
            messages=[{"role": "user", "content": prompt}],
            temperature=0.35,
            max_tokens=900
        )
        return res.choices[0].message.content.strip()
    except Exception:
        return None

def process_topic(args):
    topic, hedef_klasor, klasor_adi = args
    safe_name = "".join(c for c in topic if c.isalnum() or c in " _-").replace(" ", "_")[:50]
    file_path = hedef_klasor / f"{safe_name}.md"
    
    if file_path.exists():
        return None

    client = OpenAI(base_url=LOCAL_PROVIDER["base_url"], api_key=LOCAL_PROVIDER["api_key"])
    search_data, links = search_with_sources(topic)
    content = generate_sourced_note(client, topic, search_data, links, klasor_adi)
    
    if content:
        file_path.write_text(content, encoding="utf-8")
        return file_path.name
    return None

def main():
    print("="*60)
    print("🧠 GURKAN AI 5.0+ — BÜYÜK BİLGİ PAKETİ FABRİKASI")
    print("="*60)
    for k, v in BILGI_PAKETLERI.items():
        hedef_yol = VAULT_PATH / v["klasor"]
        mevcut = len(list(hedef_yol.glob("*.md"))) if hedef_yol.exists() else 0
        print(f"[{k}] {v['klasor']} (Mevcut: {mevcut} / Hedef: {v['hedef_adet']} Not)")
    print("[T] TÜM PAKETLERİ SIRAYLA DOLDUR (Otonom 1.250 Not)")
    print("="*60)

    secim = input("Hangi bilgi paketini üretmek istiyorsun? (1-5 veya T): ").strip().upper()
    secilen_paketler = list(BILGI_PAKETLERI.values()) if secim == "T" else [BILGI_PAKETLERI.get(secim)]

    if not secilen_paketler or None in secilen_paketler:
        print("Geçersiz seçim!")
        return

    client = OpenAI(base_url=LOCAL_PROVIDER["base_url"], api_key=LOCAL_PROVIDER["api_key"])

    for paket in secilen_paketler:
        hedef_klasor = VAULT_PATH / paket["klasor"]
        hedef_klasor.mkdir(parents=True, exist_ok=True)
        
        mevcut_sayi = len(list(hedef_klasor.glob("*.md")))
        hedef_sayi = paket["hedef_adet"]
        
        print(f"\n🚀 Paket Başlatıldı: {paket['klasor']} ({mevcut_sayi}/{hedef_sayi})")

        while mevcut_sayi < hedef_sayi:
            basliklar = get_subtopics(client, paket["tema"], count=25)
            if not basliklar:
                time.sleep(2)
                continue

            gorevler = [(b, hedef_klasor, paket["klasor"]) for b in basliklar]
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                for sonuc in executor.map(process_topic, gorevler):
                    if sonuc:
                        mevcut_sayi += 1
                        print(f"[{mevcut_sayi}/{hedef_sayi}] ✅ Kaynaklı Not Eklendi: {sonuc}")
                    if mevcut_sayi >= hedef_sayi:
                        break

        print(f"🎉 {paket['klasor']} tamamlandı! Toplam {mevcut_sayi} kaynaklı not hazır.")

if __name__ == "__main__":
    main()
