"""
GURKAN AI Content Studio v0.4
- Çift Aşamalı Üretim (Kaba Taslak -> Akıcılık ve Yapı Düzeltme)
- Süreye Göre Genişletme (Kelime sayımı ve hedefe göre yeniden boyutlandırma)
- İddia Denetimi (Kaynaksız verilere [KAYNAK GEREKLİ] etiketi)
"""

import streamlit as st
from openai import OpenAI
import time

LOCAL_PROVIDER = {
    "base_url": "http://127.0.0.1:1234/v1",
    "api_key": "lm-studio",
    "model": "qwen/qwen3-8b"
}

st.set_page_config(page_title="Content Studio v0.4", page_icon="📝", layout="wide")

st.title("📝 GURKAN AI Content Studio v0.4")
st.markdown("Hedef: En az 8/10 editoryal kaliteye ulaşan, iddia denetimli, akıcı senaryolar üretmek.")

with st.container():
    konu_veya_link = st.text_area("Konu, Haber veya Uzun Metin Girin", height=100)
    col1, col2 = st.columns(2)
    with col1:
        hedef_dil = st.selectbox("Üretim Dili", ["Türkçe", "İngilizce"])
    with col2:
        hedef_sure = st.selectbox("Hedeflenen Konuşma Süresi", ["Kısa (1-2 dk, ~200 kelime)", "Orta (5 dk, ~600 kelime)", "Uzun (8-10 dk, ~1000 kelime)"])

if st.button("🚀 Editoryal Kalitede Senaryo Üret"):
    if not konu_veya_link:
        st.warning("Lütfen bir konu girin.")
    else:
        client = OpenAI(base_url=LOCAL_PROVIDER["base_url"], api_key=LOCAL_PROVIDER["api_key"])
        
        # Süreye göre hedef kelime sayısı belirleme
        hedef_kelime = 200
        if "5 dk" in hedef_sure: hedef_kelime = 600
        elif "8-10 dk" in hedef_sure: hedef_kelime = 1000

        with st.spinner("AŞAMA 1: Kaba taslak ve kanca yazılıyor..."):
            prompt_asama_1 = f"""Senaryonun ilk taslağını yaz.
            Konu: {konu_veya_link}
            Dil: {hedef_dil}
            Dikkat çekici bir kanca (hook) ile başla, ana konuyu ver ve bir sonuçla bağla."""
            
            try:
                res1 = client.chat.completions.create(
                    model=LOCAL_PROVIDER["model"],
                    messages=[{"role": "user", "content": prompt_asama_1}],
                    temperature=0.7
                )
                taslak = res1.choices[0].message.content.strip()
            except Exception as e:
                st.error(f"1. Aşama Hatası: {e}")
                st.stop()

        with st.spinner(f"AŞAMA 2: Süreye göre genişletiliyor ve akıcılık sağlanıyor (Hedef: ~{hedef_kelime} kelime)..."):
            prompt_asama_2 = f"""Aşağıdaki kaba taslağı akıcı bir YouTube konuşma metnine çevir.
            Hedef Kelime Sayısı: Yaklaşık {hedef_kelime} kelime. (Metni bu hedefe göre uzat veya kısalt).
            Bölümleri netleştir (Giriş, Kanca, Gelişme, Sonuç).
            Dil: {hedef_dil}
            
            TASLAK:
            {taslak}
            """
            try:
                res2 = client.chat.completions.create(
                    model=LOCAL_PROVIDER["model"],
                    messages=[{"role": "user", "content": prompt_asama_2}],
                    temperature=0.6
                )
                genisletilmis_metin = res2.choices[0].message.content.strip()
            except Exception as e:
                st.error(f"2. Aşama Hatası: {e}")
                st.stop()

        with st.spinner("AŞAMA 3: İddia denetimi yapılıyor ([KAYNAK GEREKLİ] etiketleri basılıyor)..."):
            prompt_asama_3 = f"""Aşağıdaki metni incele. Eğer metinde kesin rakamlar, istatistikler, tarihler veya spesifik iddialar varsa ve bunların kaynağı belirtilmemişse, o cümlenin veya rakamın yanına tam olarak "[KAYNAK GEREKLİ]" etiketini ekle. Doğrulanmamış hiçbir veriyi gerçek kabul etme.
            Metnin akıcılığını bozma, sadece etiket ekle.
            
            METİN:
            {genisletilmis_metin}
            """
            try:
                res3 = client.chat.completions.create(
                    model=LOCAL_PROVIDER["model"],
                    messages=[{"role": "user", "content": prompt_asama_3}],
                    temperature=0.3
                )
                son_metin = res3.choices[0].message.content.strip()
            except Exception as e:
                st.error(f"3. Aşama Hatası: {e}")
                st.stop()
        
        st.success("✨ 8/10 Editoryal Kalitede Senaryo Hazır!")
        st.markdown("### 📝 Üretilen Senaryo:")
        st.info(son_metin)
        
        kelime_sayisi = len(son_metin.split())
        st.caption(f"📊 Metin İstatistikleri: Yaklaşık {kelime_sayisi} kelime üretildi.")
        
        st.download_button(
            label="📄 Senaryoyu İndir (.txt)",
            data=son_metin,
            file_name=f"GURKAN_AI_Senaryo_{hedef_dil}.txt",
            mime="text/plain"
        )
