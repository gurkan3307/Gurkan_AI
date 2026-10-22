"""
GURKAN_AI Hub v5.1 - Tam Otomasyonlu Şirket Raporlama Modülü (Excel B2B)
"""

import os
from pathlib import Path
import streamlit as st
import pandas as pd
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

st.set_page_config(page_title="GURKAN_AI Hub v5.1", page_icon="📈", layout="wide")

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
    <div style="font-size: 36px; margin-bottom: 5px;">📈</div>
    <h1 style="margin: 0; font-size: 32px; color: #ffffff;">GURKAN_AI Hub v5.1</h1>
    <p style="color: #9ca3af; font-size: 16px; margin-top: 6px;">B2B Veri Analiz ve Otomasyon Merkezi</p>
    <div style="display: flex; justify-content: center; gap: 120px; margin-top: 24px; margin-bottom: 16px;">
        <div>
            <h2 style="margin: 0; font-size: 28px; color: #34d399;">{toplam_not:,} / 25.000+</h2>
            <span style="color: #9ca3af; font-size: 14px;">Kaynaklı Bilgi Hedefi</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.header("📊 B2B Müşteri Veri Analiz & Raporlama Motoru")
st.markdown("Müşteriden gelen ham veriyi (CSV/Excel) yükleyin, GURKAN_AI temizlesin, özetlesin ve yönetici raporu olarak Obsidian'a kaydetsin.")

yuklenen_dosya = st.file_uploader("Veri Dosyası Yükleyin (.csv veya .xlsx)", type=["csv", "xlsx"])

if yuklenen_dosya:
    try:
        if yuklenen_dosya.name.endswith(".csv"):
            df = pd.read_csv(yuklenen_dosya)
        else:
            df = pd.read_excel(yuklenen_dosya)

        st.subheader("📋 Veri Önizleme (İlk 5 Satır)")
        st.dataframe(df.head(5), use_container_width=True)

        ozet_bilgi = f"Sütunlar: {list(df.columns)}\n\nİstatistikler:\n{df.describe(include='all').to_string()}"

        if st.button("🧠 Yapay Zeka ile B2B Yönetici Raporu Çıkar", type="primary"):
            client = get_client()
            with st.spinner("GURKAN_AI verileri analiz ediyor ve strateji üretiyor..."):
                prompt = f"""Sen kıdemli bir veri analisti ve B2B stratejistisin. Aşağıdaki veri özeti üzerinden şirket yöneticisine şu formata uygun bir Markdown raporu hazırla:

                # 📊 GURKAN_AI Veri Analiz Raporu
                ## 1. Temel İstatistikler ve Mevcut Durum
                ## 2. En Dikkat Çekici 3 Anomali veya Fırsat
                ## 3. Gelir Artırıcı 3 Stratejik Aksiyon (Acil)

                VERİ ÖZETİ:
                {ozet_bilgi[:4000]}"""

                res = client.chat.completions.create(
                    model=LOCAL_PROVIDER["model"],
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                rapor = res.choices[0].message.content.strip()
                st.info(rapor)

                # Raporu Obsidian'a kaydetme opsiyonu
                st.subheader("💾 Raporu Obsidian Bilgi Bankasına Kaydet")
                dosya_adi = st.text_input("Dosya Adı:", value=f"Rapor_{yuklenen_dosya.name.split('.')[0]}")

                if st.button("Obsidian'a Aktar"):
                    hedef_kasa = VAULT_PATHS[0] / "11 - B2B_Musteri_Raporlari"
                    hedef_kasa.mkdir(parents=True, exist_ok=True)
                    safe_name = "".join(c for c in dosya_adi if c.isalnum() or c in " _-").replace(" ", "_")[:45]
                    dosya_yolu = hedef_kasa / f"{safe_name}.md"
                    dosya_yolu.write_text(rapor, encoding="utf-8")
                    st.success(f"✅ Rapor Obsidian'a başarıyla kaydedildi: `{dosya_yolu.name}`")

    except Exception as e:
        st.error(f"Dosya okunurken bir hata oluştu: {e}. Lütfen Excel/CSV formatının düzgün olduğundan emin olun.")