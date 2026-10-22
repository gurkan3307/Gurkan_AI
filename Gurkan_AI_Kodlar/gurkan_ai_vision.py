"""GURKAN_AI v2.8 - Gören Ajan (Vision/OCR)"""
import os
from PIL import ImageGrab
from rapidocr_onnxruntime import RapidOCR
from openai import OpenAI

LOCAL_PROVIDER = {
    "base_url": "http://127.0.0.1:1234/v1",
    "api_key": "lm-studio",
    "model": "qwen/qwen3-8b"
}

def extract_text_from_screen():
    print("📸 Ekran görüntüsü alınıyor...")
    img = ImageGrab.grab()
    img.save("temp_screen.png")
    
    print("🔍 Yazılar analiz ediliyor (OCR)...")
    ocr = RapidOCR()
    result, _ = ocr("temp_screen.png")
    
    if result:
        text = "\n".join([line[1] for line in result])
        if os.path.exists("temp_screen.png"):
            os.remove("temp_screen.png")
        return text
    return "Ekranda okunabilir metin bulunamadı."

def analyze_screen_with_ai(screen_text):
    client = OpenAI(base_url=LOCAL_PROVIDER["base_url"], api_key=LOCAL_PROVIDER["api_key"])
    prompt = f"Şu an ekranımda şu yazılar var:\n\n{screen_text}\n\nEkranda gördüğün içeriği özetle ve bana teknik/stratejik bir öneri sun."
    
    print("🧠 GURKAN_AI Düşünüyor...")
    response = client.chat.completions.create(
        model=LOCAL_PROVIDER["model"],
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    print("GURKAN_AI Görsel Zeka Aktif.")
    metin = extract_text_from_screen()
    if metin != "Ekranda okunabilir metin bulunamadı.":
        yanit = analyze_screen_with_ai(metin)
        print(f"\n🤖 GURKAN_AI:\n{yanit}")
    else:
        print(metin)