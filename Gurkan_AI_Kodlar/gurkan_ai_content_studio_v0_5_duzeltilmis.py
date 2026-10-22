"""
GURKAN AI Content Studio v0.5
- Çift Aşamalı Üretim (Kaba Taslak -> Akıcılık ve Yapı Düzeltme)
- Süreye Göre Genişletme (Kelime sayımı ve hedefe göre yeniden boyutlandırma)
- İddia Denetimi (Kaynaksız verilere [KAYNAK GEREKLİ] etiketi)
- Onaylı MP3 Seslendirme (Sahne başlıklarını ve uyarıları ayıklayarak Edge-TTS ile ses üretimi)
"""
import unicodedata
import os
import re
import asyncio
from pathlib import Path
import streamlit as st
import edge_tts
from openai import OpenAI

LOCAL_PROVIDER = {
    "base_url": "http://127.0.0.1:1234/v1",
    "api_key": "lm-studio",
    "model": "qwen/qwen3-8b"
}

VOICE_MAP = {
    "Türkçe (Erkek - Ahmet)": "tr-TR-AhmetNeural",
    "Türkçe (Kadın - Emel)": "tr-TR-EmelNeural",
    "İngilizce (Erkek - Christopher)": "en-US-ChristopherNeural",
    "İngilizce (Kadın - Aria)": "en-US-AriaNeural"
}

st.set_page_config(page_title="Content Studio v0.5", page_icon="🎙️", layout="wide")

st.title("🎙️ GURKAN AI Content Studio v0.5")
st.markdown("8/10+ editoryal kalitede, iddia denetimli senaryo ve onaylı MP3 seslendirme stüdyosu.")

# Session state (Üretilen metni hafızada tutmak için)
if "son_metin" not in st.session_state:
    st.session_state.son_metin = ""
if "hedef_dil" not in st.session_state:
    st.session_state.hedef_dil = "Türkçe"

with st.container():
    konu_veya_link = st.text_area("Konu, Haber veya Uzun Metin Girin", height=100)
    col1, col2 = st.columns(2)
    with col1:
        hedef_dil = st.selectbox("Üretim Dili", ["Türkçe", "İngilizce"])
    with col2:
        hedef_sure = st.selectbox("Hedeflenen Konuşma Süresi", ["Kısa (1-2 dk, ~200 kelime)", "Orta (5 dk, ~600 kelime)", "Uzun (8-10 dk, ~1000 kelime)"])

if st.button("🚀 1. Adım: Editoryal Kalitede Senaryo Üret", type="primary"):
    if not konu_veya_link:
        st.warning("Lütfen bir konu girin.")
    else:
        st.session_state.hedef_dil = hedef_dil
        client = OpenAI(base_url=LOCAL_PROVIDER["base_url"], api_key=LOCAL_PROVIDER["api_key"])
        
        hedef_kelime = 200
        if "5 dk" in hedef_sure: hedef_kelime = 600
        elif "8-10 dk" in hedef_sure: hedef_kelime = 1000

        with st.spinner("AŞAMA 1: Kaba taslak ve kanca yazılıyor..."):
            prompt_1 = f"Senaryonun ilk taslağını yaz.\nKonu: {konu_veya_link}\nDil: {hedef_dil}\nDikkat çekici bir kanca (hook) ile başla, ana konuyu ver ve bir sonuçla bağla."
            res1 = client.chat.completions.create(
                model=LOCAL_PROVIDER["model"],
                messages=[{"role": "user", "content": prompt_1}],
                temperature=0.7
            )
            taslak = res1.choices[0].message.content.strip()

        with st.spinner(f"AŞAMA 2: Süreye göre genişletiliyor (Hedef: ~{hedef_kelime} kelime)..."):
            prompt_2 = f"""Aşağıdaki kaba taslağı akıcı bir YouTube konuşma metnine çevir.
            Hedef Kelime Sayısı: Yaklaşık {hedef_kelime} kelime.
            Bölümleri netleştir: (Giriş), (Kanca - Hook), (Gelişme), (Sonuç).
            Dil: {hedef_dil}
            
            TASLAK:
            {taslak}"""
            res2 = client.chat.completions.create(
                model=LOCAL_PROVIDER["model"],
                messages=[{"role": "user", "content": prompt_2}],
                temperature=0.6
            )
            genisletilmis = res2.choices[0].message.content.strip()

        with st.spinner("AŞAMA 3: İddia denetimi yapılıyor ([KAYNAK GEREKLİ] etiketleri basılıyor)..."):
            prompt_3 = f"""Aşağıdaki metni incele. Kesin rakamlar, istatistikler veya spesifik iddialar varsa ve kaynağı belirtilmemişse yanına "[KAYNAK GEREKLİ]" etiketini ekle. Metnin akıcılığını bozma.
            
            METİN:
            {genisletilmis}"""
            res3 = client.chat.completions.create(
                model=LOCAL_PROVIDER["model"],
                messages=[{"role": "user", "content": prompt_3}],
                temperature=0.3
            )
            st.session_state.son_metin = res3.choices[0].message.content.strip()

# --- ONAY VE SESLENDİRME EKRANI ---
if st.session_state.son_metin:
    st.divider()
    st.subheader("📝 Senaryo İnceleme ve Onay Alanı")
    st.markdown("Seslendirmeye geçmeden önce metin üzerindeki `[KAYNAK GEREKLİ]` noktalarını düzenleyebilir veya doğrudan onaylayabilirsiniz:")
    
    # Kullanıcının metni ekranda düzenleyebilmesi için text_area
    onayli_metin = st.text_area("Düzenlenebilir Senaryo Metni:", value=st.session_state.son_metin, height=300)
    
    kelime_sayisi = len(onayli_metin.split())
    st.caption(f"📊 Mevcut Kelime Sayısı: {kelime_sayisi} kelime")

    col_dl, col_tts = st.columns(2)
    
    with col_dl:
        st.download_button(
            label="📄 Senaryoyu İndir (.txt)",
            data=onayli_metin,
            file_name=f"GURKAN_AI_Senaryo_{st.session_state.hedef_dil}.txt",
            mime="text/plain"
        )

    st.divider()
    st.subheader("🎧 2. Adım: Onaylı Senaryoyu MP3'e Çevir (Seslendirme)")
    
    secilen_ses = st.selectbox("Spiker Sesi Seçin:", list(VOICE_MAP.keys()))

    def clean_script_for_tts(text):
        """Başlıkları, sahne direktiflerini, [KAYNAK GEREKLİ] uyarılarını ve Markdown işaretlerini temizler."""
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\((Giriş|Kanca.*?|Gelişme|Sonuç|Hook|Intro|Conclusion|Pause.*?)\)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^(#+\s*.*|\*\*.*?\*\*)\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'---+', '', text)
        # Emojileri temizle, harf, rakam ve noktalama işaretlerini koru
        cleaned = [ch for ch in text if unicodedata.category(ch).startswith(('L', 'N', 'Z')) or ch in ".,!?;:()-'\"/+%$"]
        return re.sub(r'\s+', ' ', "".join(cleaned)).strip()
    async def generate_mp3(clean_text, voice, output_path):
        communicate = edge_tts.Communicate(clean_text, voice)
        await communicate.save(output_path)

    if st.button("🔊 Senaryoyu Onayla ve MP3 Oluştur"):
        temiz_konusma_metni = clean_script_for_tts(onayli_metin)
        
        with st.expander("🔍 Spikerin Okuyacağı Saf Metni Gör (Başlıklar ve Uyarılar Ayıklandı)"):
            st.write(temiz_konusma_metni)
            
        mp3_dosya_adi = f"GURKAN_AI_Voiceover_{st.session_state.hedef_dil}.mp3"
        
        with st.spinner("Gerçekçi insan sesiyle MP3 oluşturuluyor..."):
            try:
                voice_id = VOICE_MAP[secilen_ses]
                asyncio.run(generate_mp3(temiz_konusma_metni, voice_id, mp3_dosya_adi))
                
                st.success("✅ Seslendirme tamamlandı! Hemen dinleyebilir veya indirebilirsiniz.")
                
                with open(mp3_dosya_adi, "rb") as audio_file:
                    audio_bytes = audio_file.read()
                    st.audio(audio_bytes, format="audio/mp3")
                    
                    st.download_button(
                        label="📥 MP3 Ses Dosyasını İndir",
                        data=audio_bytes,
                        file_name=mp3_dosya_adi,
                        mime="audio/mp3"
                    )
            except Exception as e:
                st.error(f"Ses oluşturulurken hata meydana geldi: {e}")
