"""
GURKAN_AI - Creative Studio v1.3 (FAZ 3: Stabil Çökme Korumalı Medya Üretimi)
"""

import os
import re
import time
import asyncio
from pathlib import Path
import streamlit as st
import edge_tts
from gtts import gTTS
from openai import OpenAI

VAULT_PATH = Path(r"D:\GURKANUS27 Yapay Zeka\GURKAN_AI_Bilgi_Bankasi")

LOCAL_PROVIDER = {
    "base_url": "http://127.0.0.1:1234/v1",
    "api_key": "lm-studio",
    "model": "qwen/qwen3-8b"
}

st.set_page_config(page_title="GURKAN_AI Creative Studio", page_icon="🎬", layout="wide")

def get_client():
    return OpenAI(base_url=LOCAL_PROVIDER["base_url"], api_key=LOCAL_PROVIDER["api_key"])

def generate_srt(text):
    words = text.split()
    srt_content = ""
    start_time = 0
    words_per_subtitle = 4
    subtitle_index = 1
    
    for i in range(0, len(words), words_per_subtitle):
        chunk = " ".join(words[i:i+words_per_subtitle])
        duration = len(chunk.split()) * 0.4
        end_time = start_time + duration
        
        def format_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds % 1) * 1000)
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
            
        srt_content += f"{subtitle_index}\n{format_time(start_time)} --> {format_time(end_time)}\n{chunk}\n\n"
        start_time = end_time
        subtitle_index += 1
        
    return srt_content

def create_voiceover_sync(text, filename, voice):
    try:
        async def run_edge():
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(filename)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_edge())
        return True
    except Exception as e:
        print(f"Edge-TTS hatası: {e}")
        return False

def create_voiceover(text, filename, voice="tr-TR-AhmetNeural"):
    if create_voiceover_sync(text, str(filename), voice):
        return True
        
    print("Yedek sisteme (gTTS) geçiliyor...")
    try:
        tts = gTTS(text=text, lang="tr", slow=False)
        tts.save(str(filename))
        return True
    except Exception as e:
        print(f"gTTS hatası: {e}")
        return False

st.markdown("""
<div style="background-color: #0e1117; border: 1px solid #eab308; border-radius: 16px; padding: 24px; text-align: center; margin-bottom: 25px;">
    <div style="font-size: 36px; margin-bottom: 5px;">🎬</div>
    <h1 style="margin: 0; font-size: 30px; color: #ffffff;">GURKAN_AI Creative Studio v1.3</h1>
    <p style="color: #9ca3af; font-size: 16px; margin-top: 6px;">FAZ 3: Stabil Medya ve Spiker Ses Merkezi</p>
</div>
""", unsafe_allow_html=True)

with st.form("creative_form"):
    konu_veya_icerik = st.text_area("Hangi konu hakkında içerik üretilsin?", placeholder="Örn: Roma İmparatorluğu'nun Çöküşü")
    platform = st.selectbox("Format", ["YouTube Shorts (Dikey - 60 sn)", "Instagram Reels (Dikey)", "Uzun YouTube Videosu (Yatay)"])
    ses_secimi = st.selectbox("Seslendirmen", ["Ahmet (Erkek)", "Emel (Kadın)"])
    submit = st.form_submit_button("🎬 Senaryo, Ses ve Altyazı Üret")

if submit and konu_veya_icerik:
    client = get_client()
    with st.spinner("GURKAN_AI Senaryoyu Yazıyor..."):
        prompt = f"""Sen viral video içerikleri üreten usta bir senarist ve profesyonel bir seslendirmen koçusun. 
Konu: {konu_veya_icerik}
Platform: {platform}

Bana bu platform için uygun, kancası (hook) çok güçlü, izleyiciyi hemen yakalayacak bir video metni yaz.
ÖNEMLİ KURALLAR:
1. SADECE okunacak metni ver. [Müzik girer] gibi yönetmen notları ASLA KULLANMA.
2. Emojileri ve özel sembolleri ASLA kullanma.
3. SESLENDİRME İÇİN VURGU FORMATI: Metni bir spiker okuyacak. Cümleleri çok kısa tut. Vurgulanması gereken kelimelerden sonra bolca virgül (,) koyarak nefes aldır. Heyecanlı yerlerde ünlem (!) ve soru işareti (?) kullan.
Örnek Format: "Biliyor muydun? Kleopatra, aslında Mısırlı değildi! Evet, yanlış duymadın. O, safkan bir Yunandı."
"""
        
        try:
            res = client.chat.completions.create(model=LOCAL_PROVIDER["model"], messages=[{"role": "user", "content": prompt}], temperature=0.7)
            senaryo_metni = res.choices[0].message.content.strip()
            
            # Emojileri ve sorunlu karakterleri hatasız Regex ile temizle
            senaryo_metni = re.sub(r'[^\w\s.,!?;:\-\'"çğıöşüÇĞİÖŞÜ]', '', senaryo_metni)
            
            st.success("✅ Senaryo Üretildi!")
            st.text_area("📝 Okunacak Metin (Düzenleyebilirsiniz):", value=senaryo_metni, height=200)
            
            with st.spinner("🎙️ Ses ve Altyazı Oluşturuluyor (Çökme Koruması Aktif)..."):
                hedef_klasor = VAULT_PATH / "13 - Creative_Studio_Uretimleri"
                hedef_klasor.mkdir(parents=True, exist_ok=True)
                
                safe_name = "".join(c for c in konu_veya_icerik if c.isalnum() or c in " _-").replace(" ", "_")[:30]
                if not safe_name: safe_name = f"Icerik_{int(time.time())}"
                
                mp3_yolu = hedef_klasor / f"{safe_name}.mp3"
                srt_yolu = hedef_klasor / f"{safe_name}.srt"
                md_yolu = hedef_klasor / f"{safe_name}_Senaryo.md"
                
                voice_model = "tr-TR-AhmetNeural" if "Ahmet" in ses_secimi else "tr-TR-EmelNeural"
                ses_basarili = create_voiceover(senaryo_metni, mp3_yolu, voice_model)
                
                srt_icerik = generate_srt(senaryo_metni)
                srt_yolu.write_text(srt_icerik, encoding="utf-8")
                
                md_icerik = f"---\ntarih: {time.strftime('%Y-%m-%d')}\nformat: {platform}\n---\n# {safe_name}\n\n{senaryo_metni}\n\n---\n*GURKAN_AI Creative Studio tarafından üretildi.*"
                md_yolu.write_text(md_icerik, encoding="utf-8")
                
                st.success("🎉 Tüm Medya Paketleri Hazır!")
                col1, col2, col3 = st.columns(3)
                with col1:
                    if ses_basarili:
                        st.info(f"🎵 **Ses Dosyası:**\n`{mp3_yolu.name}`")
                        st.audio(str(mp3_yolu))
                    else:
                        st.error("Ses motorları yanıt vermedi.")
                with col2:
                    st.warning(f"💬 **Altyazı Dosyası:**\n`{srt_yolu.name}`")
                    st.download_button(label="SRT İndir", data=srt_icerik, file_name=srt_yolu.name, mime="text/plain")
                with col3:
                    st.success(f"💾 **Obsidian Notu:**\n`{md_yolu.name}`")
                    
        except Exception as e:
            st.error(f"Hata oluştu: {e}")
