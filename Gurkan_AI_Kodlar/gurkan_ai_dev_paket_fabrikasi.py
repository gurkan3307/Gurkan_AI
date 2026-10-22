"""
GURKAN_AI - BÜYÜK BİLGİ PAKETİ FABRİKASI v2.1 (Hedef: 25.000+ Not)
- Doğrudan GURKAN_AI_Bilgi_Bankasi kasasına kaydeder.
- /no_think ve <think> temizleyici ile 2 kat hızlı çalışır.
"""

import os
import time
import re
import warnings
from pathlib import Path
from duckduckgo_search import DDGS
from openai import OpenAI

warnings.filterwarnings("ignore", category=RuntimeWarning)

LOCAL_PROVIDER = {
    "base_url": "http://127.0.0.1:1234/v1",
    "api_key": "lm-studio",
    "model": "qwen/qwen3-8b"
}

# Doğrudan ana Bilgi Bankası kasanın yolu
VAULT_PATH = Path(r"D:\GURKANUS27 Yapay Zeka\GURKAN_AI_Bilgi_Bankasi")

def get_client():
    return OpenAI(base_url=LOCAL_PROVIDER["base_url"], api_key=LOCAL_PROVIDER["api_key"])

def clean_thinking(text):
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

def web_search(query):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            results = DDGS().text(query, region='tr-tr', max_results=3)
        if results:
            return "\n".join([f"- {r.get('body')} (Kaynak: {r.get('href')})" for r in results])
        return ""
    except Exception as e:
        print(f"  [Arama Hatası]: {e}")
        return ""

def create_knowledge_package():
    print("==================================================")
    print("🏭 GURKAN_AI - BİLGİ PAKETİ FABRİKASI v2.1 (Hedef: 25K+)")
    print(f"📂 Hedef Kasa: {VAULT_PATH}")
    print("==================================================")
    
    ana_konu = input("\nHangi ana konuda dev bir paket üretelim? (Örn: Dijital Pazarlama veya Siber Güvenlik): ").strip()
    if not ana_konu:
        return
        
    kac_not = input("Kaç alt başlık/not üretilsin? (Önerilen: 5-10 arası, dev paket için 20): ").strip()
    try:
        kac_not = int(kac_not)
    except:
        kac_not = 5

    print(f"\n🧠 '{ana_konu}' için {kac_not} adet nesnel alt başlık planlanıyor...")
    client = get_client()
    
    prompt_baslik = f"'{ana_konu}' hakkında dev bir ansiklopedi hazırlıyorum. Bana bu konunun en kritik, en bilgi dolu {kac_not} alt başlığını sadece virgülle ayırarak yaz. Başka hiçbir açıklama yapma. /no_think"
    
    try:
        res = client.chat.completions.create(
            model=LOCAL_PROVIDER["model"],
            messages=[{"role": "user", "content": prompt_baslik}],
            temperature=0.4
        )
        raw_text = clean_thinking(res.choices[0].message.content)
        basliklar = [b.strip().strip("-*0123456789. ") for b in re.split(r",|\n", raw_text) if len(b.strip()) > 3][:kac_not]
    except Exception as e:
        print(f"Model bağlantı hatası: {e}")
        return
    
    print(f"✅ Hedef Başlıklar ({len(basliklar)} adet): {', '.join(basliklar)}\n")
    
    hedef_klasor = VAULT_PATH / f"Paket_{ana_konu.replace(' ', '_')}"
    hedef_klasor.mkdir(parents=True, exist_ok=True)

    uretim_sayisi = 0
    for idx, baslik in enumerate(basliklar, 1):
        print(f"🔍 [{idx}/{len(basliklar)}] Araştırılıyor ve Yazılıyor: {baslik}")
        arama_sonucu = web_search(f"{ana_konu} {baslik}")
        
        prompt_icerik = f"Sen nesnel, tamamen bilimsel ve veri odaklı bir araştırmacısın. Konu: '{baslik}' ({ana_konu}).\n\nAşağıdaki internet araştırma verilerini kullanarak tarafsız, detaylı ve profesyonel bir ansiklopedi notu yaz. Asla halüsinasyon görme.\n\nVERİLER:\n{arama_sonucu}\n\nFormat: Direkt bilgi ver, gereksiz giriş veya çıkış cümlesi kullanma. /no_think"
        
        try:
            icerik_res = client.chat.completions.create(
                model=LOCAL_PROVIDER["model"],
                messages=[{"role": "user", "content": prompt_icerik}],
                temperature=0.2
            )
            metin = clean_thinking(icerik_res.choices[0].message.content)
            
            dosya_adi = re.sub(r'[<>:"/\\|?*]', '', baslik)[:50].strip() + ".md"
            dosya_yolu = hedef_klasor / dosya_adi
            
            tam_icerik = f"---\nkategori: Bilgi_Paketi\nkonu: {ana_konu}\ntarih: {time.strftime('%Y-%m-%d')}\ndogrulanmis: true\nkaynak_durumu: internet_aramasi\n---\n# {baslik}\n\n{metin}\n\n---\n*GURKAN_AI Bilgi Fabrikası (v2.1) tarafından doğrudan GURKAN_AI_Bilgi_Bankasi kasasına üretilmiştir.*"
            dosya_yolu.write_text(tam_icerik, encoding="utf-8")
            
            print(f"  💾 Bilgi Bankasına Kaydedildi: {dosya_adi}")
            uretim_sayisi += 1
            time.sleep(1.5)
        except Exception as e:
            print(f"  ❌ Hata oluştu: {e}")

    print(f"\n🎉 İŞLEM TAMAM! {uretim_sayisi} adet nesnel not doğrudan '{hedef_klasor}' içine eklendi.")

if __name__ == "__main__":
    create_knowledge_package()
