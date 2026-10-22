"""
GURKAN AI 5.0+ Otomatik Dosya Oluşturucu
Bu scripti çalıştırdığında:
1) gurkan_ai_paket_fabrikasi.py
2) gurkan_ai_hub_v5.py
dosyaları otomatik olarak klasörüne kaydedilir.
"""

from pathlib import Path

# 1. DOSYA: gurkan_ai_paket_fabrikasi.py
paket_fabrikasi_kodu = '''"""
GURKAN AI 5.0+ — Büyük Bilgi Paketleri Fabrikası (25.000+ Hedefi İçin Adım Adım Üretim)
5 Ana Sektörel Pakette Kaynaklı, Tekrarsız ve Yüksek Kaliteli Obsidian Notları Üretir.
"""

import os
import time
import concurrent.futures
from pathlib import Path
from duckduckgo_search import DDGS
from openai import OpenAI

VAULT_PATH = Path(r"D:\\GURKANUS27 Yapay Zeka\\GURKAN_AI_Bilgi_Bankasi")

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
        f"Ana Konu: '{theme}'.\\n"
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
        lines = [l.strip("- *0123456789.()") for l in res.choices[0].message.content.split('\\n') if len(l.strip()) > 8]
        return lines[:count]
    except Exception as e:
        print(f"Başlık üretim hatası: {e}")
        return []

def search_with_sources(topic):
    try:
        results = DDGS().text(topic, region='tr-tr', max_results=3)
        if not results:
            return "Kaynak bulunamadı.", []
        ozet = "\\n".join([f"- {r.get('title','')}: {r.get('body','')}" for r in results])
        linkler = [r.get('href', '') for r in results if r.get('href')]
        return ozet, linkler
    except Exception:
        return "Genel sektör bilgisi.", []

def generate_sourced_note(client, topic, search_data, links, folder_name):
    kaynak_listesi = "\\n".join([f'  - "{link}"' for link in links]) if links else '  - "Yerel Sentez"'
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
        
        print(f"\\n🚀 Paket Başlatıldı: {paket['klasor']} ({mevcut_sayi}/{hedef_sayi})")

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
'''

# 2. DOSYA: gurkan_ai_hub_v5.py
hub_v5_kodu = '''"""
GURKAN AI 5.0+ — Çok Amaçlı Kişisel Yapay Zeka Platformu (Ana Merkez)
"""

import os
from pathlib import Path
import streamlit as st
import pandas as pd
from duckduckgo_search import DDGS
from openai import OpenAI

VAULT_PATHS = [
    Path(r"D:\\GURKANUS27 Yapay Zeka\\GURKAN_AI_Bilgi_Bankasi"),
    Path(r"D:\\GURKANUS27 Yapay Zeka\\Jarvis_Beyin")
]

LOCAL_PROVIDER = {
    "base_url": "http://127.0.0.1:1234/v1",
    "api_key": "lm-studio",
    "model": "qwen/qwen3-8b"
}

st.set_page_config(page_title="GURKAN AI 5.0+", page_icon="🧠", layout="wide")

def get_client():
    return OpenAI(base_url=LOCAL_PROVIDER["base_url"], api_key=LOCAL_PROVIDER["api_key"])

def count_knowledge_base():
    total = 0
    for vp in VAULT_PATHS:
        if vp.exists():
            total += len(list(vp.rglob("*.md")))
    return total

toplam_not = count_knowledge_base()

st.markdown(f"""
<div style="background-color: #0e1117; border: 1px solid #262730; border-radius: 16px; padding: 28px; text-align: center; margin-bottom: 25px;">
    <div style="font-size: 36px; margin-bottom: 5px;">🧠</div>
    <h1 style="margin: 0; font-size: 32px; color: #ffffff;">GURKAN AI 5.0+</h1>
    <p style="color: #9ca3af; font-size: 16px; margin-top: 6px;">Çok amaçlı kişisel yapay zekâ platformu</p>
    <div style="display: flex; justify-content: center; gap: 120px; margin-top: 24px; margin-bottom: 16px;">
        <div>
            <h2 style="margin: 0; font-size: 28px; color: #60a5fa;">26+</h2>
            <span style="color: #9ca3af; font-size: 14px;">Planlanan modül (5 Aktif)</span>
        </div>
        <div>
            <h2 style="margin: 0; font-size: 28px; color: #34d399;">{toplam_not:,} / 25.000+</h2>
            <span style="color: #9ca3af; font-size: 14px;">Kaynaklı bilgi hedefi (Mevcut / Hedef)</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.title("⚡ GURKAN AI 5.0+ Modüller")
secilen_modul = st.sidebar.radio(
    "Aktif Çekirdek Modülü Seçin:",
    [
        "1️⃣ Kod Geliştirme Stüdyosu",
        "2️⃣ Veri Analiz Motoru",
        "3️⃣ İş Akışı Otomasyonu",
        "4️⃣ Bilgi Bankası Hızlandırıcı (25K Hedefi)"
    ]
)

if secilen_modul == "1️⃣ Kod Geliştirme Stüdyosu":
    st.header("💻 Kod Geliştirme Stüdyosu")
    gorev_tanimi = st.text_area("Yazılacak Aracı veya Modülü Tarif Edin:", height=120)
    dosya_adi = st.text_input("Kaydedilecek Dosya Adı:", value="yeni_otomasyon_modulu.py")

    if st.button("⚙️ Kodu Üret ve Denetle", type="primary"):
        if gorev_tanimi:
            client = get_client()
            with st.spinner("Qwen3 mimariyi kuruyor ve kodu yazıyor..."):
                prompt = f"Sen kıdemli bir Python yazılım mimarısın. Aşağıdaki görevi yerine getiren hatasız bir Python kodu yaz. Sadece Python kodunu ver:\\n{gorev_tanimi}"
                res = client.chat.completions.create(
                    model=LOCAL_PROVIDER["model"],
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2
                )
                temiz_kod = res.choices[0].message.content.replace("```python", "").replace("```", "").strip()
            st.code(temiz_kod, language="python")
            st.download_button("📥 Python Dosyasını İndir (.py)", data=temiz_kod, file_name=dosya_adi, mime="text/x-python")

elif secilen_modul == "2️⃣ Veri Analiz Motoru":
    st.header("📊 Veri Analiz Motoru (B2B Raporlama)")
    yuklenen_dosya = st.file_uploader("Veri Dosyası Yükleyin (.csv veya .xlsx)", type=["csv", "xlsx"])
    if yuklenen_dosya:
        df = pd.read_csv(yuklenen_dosya) if yuklenen_dosya.name.endswith(".csv") else pd.read_excel(yuklenen_dosya)
        st.dataframe(df.head(10), use_container_width=True)
        ozet_bilgi = f"Sütunlar: {list(df.columns)}\\nİstatistikler:\\n{df.describe(include='all').to_string()}"
        if st.button("🧠 Yapay Zeka ile Yönetici Raporu Çıkar", type="primary"):
            client = get_client()
            with st.spinner("Veri seti analiz ediliyor..."):
                res = client.chat.completions.create(
                    model=LOCAL_PROVIDER["model"],
                    messages=[{"role": "user", "content": f"Veri özeti üzerinden en dikkat çekici 3 bulguyu ve 3 aksiyon önerisini raporla:\\n{ozet_bilgi[:4000]}"}],
                    temperature=0.3
                )
                rapor = res.choices[0].message.content.strip()
                st.info(rapor)
                st.download_button("📄 Raporu İndir (.md)", data=rapor, file_name="Veri_Analiz_Raporu.md")

elif secilen_modul == "3️⃣ İş Akışı Otomasyonu":
    st.header("🔗 İş Akışı Otomasyonu (Zincirleme Görev Motoru)")
    hedef_konu = st.text_input("Otomasyon Zinciri Konusu:")
    if st.button("🚀 İş Akışını Başlat", type="primary") and hedef_konu:
        client = get_client()
        arama = DDGS().text(hedef_konu, region="tr-tr", max_results=3)
        res = client.chat.completions.create(
            model=LOCAL_PROVIDER["model"],
            messages=[{"role": "user", "content": f"Şu konuyu ve web verisini analiz edip müşteriye sunulacak stratejik rapor ve bülten yaz:\\nKonu: {hedef_konu}\\nVeri: {arama}"}],
            temperature=0.5
        )
        sonuc = res.choices[0].message.content.strip()
        st.info(sonuc)
        hedef_kasa = VAULT_PATHS[0] / "10 - Is_Akisi_Ciktilari"
        hedef_kasa.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(c for c in hedef_konu if c.isalnum() or c in " _-").replace(" ", "_")[:45]
        dosya_yolu = hedef_kasa / f"Otomasyon_{safe_name}.md"
        dosya_yolu.write_text(sonuc, encoding="utf-8")
        st.success(f"💾 Obsidian'a kaydedildi: {dosya_yolu.name}")

elif secilen_modul == "4️⃣ Bilgi Bankası Hızlandırıcı (25K Hedefi)":
    st.header("📚 25.000+ Kaynaklı Bilgi Bankası Yönetimi")
    st.progress(min(toplam_not / 25000, 1.0), text=f"İlerleme: {toplam_not:,} / 25.000 Not")
'''

Path("gurkan_ai_paket_fabrikasi.py").write_text(paket_fabrikasi_kodu, encoding="utf-8")
Path("gurkan_ai_hub_v5.py").write_text(hub_v5_kodu, encoding="utf-8")
print("✅ İki dosya da başarıyla oluşturuldu: gurkan_ai_paket_fabrikasi.py ve gurkan_ai_hub_v5.py")