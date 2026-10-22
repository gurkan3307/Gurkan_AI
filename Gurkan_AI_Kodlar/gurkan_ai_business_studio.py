"""
GURKAN_AI - Business Studio v1.0 (FAZ 2: E-Ticaret ve Pazarlama Otomasyonu)
- Küçük ve orta ölçekli işletmeler (KOBİ) için saniyeler içinde SEO uyumlu ürün açıklamaları yazar.
- Sosyal medya gönderileri (Instagram/LinkedIn) tasarlar.
- B2B Satış e-postaları oluşturur.
- Çıktıları doğrudan Obsidian'a ticari bir paket olarak kaydeder.
"""

import os
from pathlib import Path
import streamlit as st
from openai import OpenAI
import time

VAULT_PATH = Path(r"D:\GURKANUS27 Yapay Zeka\GURKAN_AI_Bilgi_Bankasi")

LOCAL_PROVIDER = {
    "base_url": "http://127.0.0.1:1234/v1",
    "api_key": "lm-studio",
    "model": "qwen/qwen3-8b"
}

st.set_page_config(page_title="GURKAN_AI Business Studio", page_icon="💼", layout="wide")

def get_client():
    return OpenAI(base_url=LOCAL_PROVIDER["base_url"], api_key=LOCAL_PROVIDER["api_key"])

st.markdown("""
<div style="background-color: #0e1117; border: 1px solid #3b82f6; border-radius: 16px; padding: 24px; text-align: center; margin-bottom: 25px;">
    <div style="font-size: 36px; margin-bottom: 5px;">💼</div>
    <h1 style="margin: 0; font-size: 30px; color: #ffffff;">GURKAN_AI Business Studio</h1>
    <p style="color: #9ca3af; font-size: 16px; margin-top: 6px;">FAZ 2: E-Ticaret & Pazarlama Otomasyon Merkezi (B2B Gelir Motoru)</p>
</div>
""", unsafe_allow_html=True)

st.markdown("Müşterinin ürününü veya hizmetini girin. GURKAN_AI anında SEO açıklaması, sosyal medya planı ve satış maili hazırlasın.")

with st.form("b2b_form"):
    firma_adi = st.text_input("Firma/Marka Adı", placeholder="Örn: Gurkan Tech")
    urun_adi = st.text_input("Ürün veya Hizmet Adı", placeholder="Örn: Akıllı Ev Güvenlik Kamerası")
    urun_ozellikleri = st.text_area("Ürünün Temel Özellikleri (Virgülle ayırabilirsiniz)", placeholder="Gece görüşü, 4K çözünürlük, yapay zeka hareket algılama, kablosuz")
    hedef_kitle = st.selectbox("Hedef Kitle", ["Bireysel Tüketiciler (B2C)", "Şirketler (B2B)", "Gençler", "Profesyoneller"])
    
    submit = st.form_submit_button("🚀 Tek Tuşla Pazarlama Paketini Üret")

if submit and urun_adi and urun_ozellikleri:
    client = get_client()
    
    with st.spinner("GURKAN_AI Müşteri İçin Pazarlama Paketini Hazırlıyor..."):
        prompt = f"""Sen kıdemli bir E-Ticaret ve Pazarlama Uzmanısın.
Müşteri: {firma_adi}
Ürün/Hizmet: {urun_adi}
Özellikler: {urun_ozellikleri}
Hedef Kitle: {hedef_kitle}

Bana şu 3 parçadan oluşan bir pazarlama paketi hazırla:
1. E-Ticaret sitesi için SEO uyumlu, ikna edici bir ürün açıklaması (1 paragraf).
2. Instagram/LinkedIn için dikkat çekici bir sosyal medya gönderisi (Emojiler ve hashtagler dahil).
3. Bu ürünü kurumsal müşterilere veya bayilere satmak için profesyonel bir B2B "Soğuk Satış" e-postası taslağı.

Başlıkları Markdown (##) ile ayırarak ver.
"""
        
        try:
            res = client.chat.completions.create(
                model=LOCAL_PROVIDER["model"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6
            )
            pazarlama_paketi = res.choices[0].message.content.strip()
            
            st.success("✅ Pazarlama Paketi Başarıyla Üretildi!")
            st.markdown("---")
            st.markdown(pazarlama_paketi)
            
            # Obsidian'a Kaydet
            hedef_klasor = VAULT_PATH / "12 - B2B_Ajans_Otomasyonlari"
            hedef_klasor.mkdir(parents=True, exist_ok=True)
            
            safe_name = "".join(c for c in f"{firma_adi}_{urun_adi}" if c.isalnum() or c in " _-").replace(" ", "_")[:40]
            if not safe_name:
                safe_name = f"Pazarlama_Paketi_{int(time.time())}"
                
            dosya_yolu = hedef_klasor / f"{safe_name}.md"
            
            tam_icerik = f"---\ntarih: {time.strftime('%Y-%m-%d')}\nfirma: {firma_adi}\nurun: {urun_adi}\n---\n# {firma_adi} - {urun_adi} Pazarlama Paketi\n\n{pazarlama_paketi}"
            dosya_yolu.write_text(tam_icerik, encoding="utf-8")
            
            st.info(f"💾 Paket Obsidian'a kalıcı olarak kaydedildi: `{dosya_yolu.name}`")
            
        except Exception as e:
            st.error(f"Yerel modele bağlanırken hata oluştu: {e}. LM Studio'nun açık olduğundan emin olun.")
