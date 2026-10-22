"""
GURKAN AI 5.0+ — Çok Amaçlı Kişisel Yapay Zeka Platformu (Ana Merkez)
"""

import os
from pathlib import Path
import streamlit as st
import pandas as pd
from duckduckgo_search import DDGS
from openai import OpenAI

VAULT_PATHS = [
    Path(r"D:\GURKANUS27 Yapay Zeka\GURKAN_AI_Bilgi_Bankasi"),
    Path(r"D:\GURKANUS27 Yapay Zeka\Jarvis_Beyin")
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
                prompt = f"Sen kıdemli bir Python yazılım mimarısın. Aşağıdaki görevi yerine getiren hatasız bir Python kodu yaz. Sadece Python kodunu ver:\n{gorev_tanimi}"
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
        ozet_bilgi = f"Sütunlar: {list(df.columns)}\nİstatistikler:\n{df.describe(include='all').to_string()}"
        if st.button("🧠 Yapay Zeka ile Yönetici Raporu Çıkar", type="primary"):
            client = get_client()
            with st.spinner("Veri seti analiz ediliyor..."):
                res = client.chat.completions.create(
                    model=LOCAL_PROVIDER["model"],
                    messages=[{"role": "user", "content": f"Veri özeti üzerinden en dikkat çekici 3 bulguyu ve 3 aksiyon önerisini raporla:\n{ozet_bilgi[:4000]}"}],
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
            messages=[{"role": "user", "content": f"Şu konuyu ve web verisini analiz edip müşteriye sunulacak stratejik rapor ve bülten yaz:\nKonu: {hedef_konu}\nVeri: {arama}"}],
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
