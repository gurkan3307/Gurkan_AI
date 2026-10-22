"""JARVIS v2.9.2 — Görsel Zekalı (Vision & OCR), Masaüstü Otomasyonlu ve Çok Dilli Hibrit Ajan

Özellikler (v2.9.2):
- Görsel Zeka / Ekran Analizi (`analyze_screen`): Ekran görüntüsünü anında yakalar;
  1) Yerel OCR (RapidOCR) ile ekrandaki tüm yazıları/hataları/kodları internetsiz okur.
  2) Eğer Vision destekli bir model (Google Gemini veya Qwen-VL) aktifse görüntüyü doğrudan modele gönderip görsel analiz yapar.
- Masaüstü ve Sistem Kontrolü (Uygulama açma, web sitesi açma, sistem durumu ve ekran görüntüsü alma)
- Çoklu Dil Algılama ve Konuşma (TR, EN, DE, FR, ES, RU, IT)
- Çince Karakter Sızıntısı Filtresi ve Emoji Okuma Engeli
- 3 Kademeli Çökme Korumalı Ses Motoru (Edge-TTS -> gTTS -> pyttsx3)
- Hibrit Obsidian RAG (Vektör + BM25 Arama, Taslak + Onaylı Not Kaydı)
- Kesintisiz Sesli Sohbet ('s' ile açılır, 'sesli sohbeti kapat' ile kapanır)

Kurulum: venv içinde `pip install rapidocr-onnxruntime pillow psutil`
Çalıştırma: `python jarvis_v2_9_2_ekran_duzeltme.py`
"""

import os
import re
import io
import base64
import sqlite3
import json
import hashlib
import math
import asyncio
import time
import subprocess
import webbrowser
from collections import Counter
import unicodedata
from datetime import datetime
from pathlib import Path

import edge_tts
from gtts import gTTS
import pyttsx3
import pygame
import speech_recognition as sr
from langdetect import detect, DetectorFactory
from openai import OpenAI
from duckduckgo_search import DDGS

# Sistem, Ekran ve Görsel Zeka (OCR) kütüphaneleri
try:
    import psutil
except ImportError:
    psutil = None

try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None

try:
    from rapidocr_onnxruntime import RapidOCR
    ocr_engine = RapidOCR()
except ImportError:
    ocr_engine = None

DetectorFactory.seed = 0

USER_NAME = "Gurkan"
MAX_MESSAGES = 20
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "jarvis_memory.db"
EXPORT_PATH = BASE_DIR / "jarvis_proje_ozeti.md"
VAULT_PATH = Path(r"D:\GURKANUS27 Yapay Zeka\Jarvis_Beyin")
MAX_NOTE_SIZE = 200_000
INDEX_PATH = BASE_DIR / "jarvis_vectors.db"
EMBED_MODEL = "text-embedding-nomic-embed-text-v1.5"
CHUNK_CHARS = 1200
CHUNK_OVERLAP = 150
MAX_CONTEXT_CHARS = 5600
APPROVED_DIR = VAULT_PATH / "07 — Onayli JARVIS Taslaklari"
PENDING_NOTE = None
# Ekranı buluta göndermek için kullanıcının açık opt-in ayarı gerekir.
GOOGLE_VISION_ALLOWED = os.environ.get("JARVIS_GOOGLE_VISION", "0") == "1"

PROVIDERS = {
    "yerel": {
        "base_url": "http://127.0.0.1:1234/v1",
        "api_key": "lm-studio",
        "model": "qwen/qwen3-8b",
        "no_think": True,
        "timeout": 90.0,
    },
    "google": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key": os.environ.get("GOOGLE_API_KEY", ""),
        "model": os.environ.get("GOOGLE_MODEL", "gemini-2.5-flash"),
        "no_think": False,
        "timeout": 45.0,
    },
}

SYSTEM_PROMPT = (
    f"You are Jarvis, a personal AI assistant talking directly to {USER_NAME}. "
    "CRITICAL RULE: Always reply in the EXACT SAME LANGUAGE that the user speaks or writes to you. "
    "If the user speaks Turkish, reply in Turkish. If English, reply in English. If German, reply in German. "
    "NEVER output Chinese characters (Hanzi) unless explicitly asked. "
    "Use your tools whenever needed (screen analysis/vision, web search, Obsidian notes, opening apps/websites, system status, screenshot). "
    "When the user asks what is on the screen, about an error on the screen, or asks you to look at the screen, ALWAYS call `analyze_screen`. "
    "Be brief, clear, and informal. Do NOT use Markdown formatting or emojis."
)

# ==========================================
# 1. ÇOK DİLLİ SES VE DİNLEME MOTORU
# ==========================================
pygame.mixer.init()

VOICE_MAP = {
    "tr": "tr-TR-AhmetNeural",
    "en": "en-US-ChristopherNeural",
    "de": "de-DE-ConradNeural",
    "fr": "fr-FR-HenriNeural",
    "es": "es-ES-AlvaroNeural",
    "ru": "ru-RU-DmitryNeural",
    "it": "it-IT-DiegoNeural",
}

CURRENT_STT_LANG = "tr-TR"

def strip_chinese(text):
    return re.sub(r'[\u4e00-\u9fff]+', '', text)

def detect_language(text):
    try:
        lang = detect(text)
        return lang if lang in VOICE_MAP else "tr"
    except Exception:
        return "tr"

def clean_for_speech(text, lang="tr"):
    """Yalnızca seslendirilecek kopyayı düzenler; yazılı cevabı değiştirmez."""
    text = strip_chinese(str(text))
    text = re.sub(r'https?://\S+', 'bağlantı' if lang == "tr" else 'link', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'(?m)^\s{0,3}#{1,6}\s*', '', text)
    text = re.sub(r'`(.*?)`', r'\1', text)
    if lang == "tr":
        month_names = ('', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
                       'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık')
        def fmt_date(m):
            try:
                d, mon, year = map(int, m.groups())
                datetime(year, mon, d)
                return f"{d} {month_names[mon]} {year}"
            except ValueError:
                return m.group(0)
        text = re.sub(r'(?<!\d)(\d{1,2})\.(\d{1,2})\.(\d{4})(?!\d)', fmt_date, text)
        text = re.sub(r'(-?\d+(?:[.,]\d+)?)\s*°\s*C\b', r'\1 derece Selsiyus', text, flags=re.I)
        text = re.sub(r'%(\s*\d+)', r'yüzde \1', text)
        text = re.sub(r'(\d+)\s*%', r'yüzde \1', text)
        replacements = {
            'OCR': 'optik karakter tanıma', 'TTS': 'metinden sese dönüştürme',
            'AI': 'yapay zekâ', 'CPU': 'işlemci', 'GPU': 'ekran kartı',
            'ChatGPT': 'Çet Ci Pi Ti', 'Qwen': 'Kuen',
            'LM Studio': 'El Em Stüdyo',
        }
        for word, pronunciation in replacements.items():
            text = re.sub(r'(?<!\w)' + re.escape(word) + r'(?!\w)',
                          lambda _m, p=pronunciation: p, text, flags=re.I)
    cleaned = []
    for ch in text:
        cat = unicodedata.category(ch)
        if cat.startswith(('L', 'N', 'Z')) or ch in ".,!?;:()-'\"/+%":
            cleaned.append(ch)
    return re.sub(r'\s+', ' ', ''.join(cleaned)).strip()

# Sesin yanlış söylenip söylenmediğini API çağırmadan test eder.
def seslendirme_testi():
    ornek = (
        "OCR sistemi aktif. ChatGPT ve Qwen çalışıyor. "
        "Sıcaklık 12°C, tarih 19.10.2026, işlemci CPU yüzde 25."
    )
    lang = CURRENT_STT_LANG.split("-")[0].lower()
    print("\n[Ses testi: Orijinal]", ornek)
    print("[Ses testi: Seslendirilecek]", clean_for_speech(ornek, lang))
    speak(ornek)

def play_mp3(file_path):
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.music.unload()
    try:
        os.remove(file_path)
    except OSError:
        pass

async def edge_speak(clean_text, voice, temp_file):
    communicate = edge_tts.Communicate(clean_text, voice)
    await communicate.save(temp_file)

def speak(text):
    text = strip_chinese(text)
    print(f"\nJarvis: {text}\n")
    lang_code = CURRENT_STT_LANG.split("-")[0].lower()
    if lang_code not in VOICE_MAP:
        lang_code = "tr"
    clean_text = clean_for_speech(text, lang_code)
    if not clean_text:
        return
    selected_voice = VOICE_MAP.get(lang_code, "tr-TR-AhmetNeural")
    temp_file = str(BASE_DIR / "temp_voice.mp3")

    try:
        asyncio.run(edge_speak(clean_text, selected_voice, temp_file))
        play_mp3(temp_file)
        return
    except Exception:
        pass

    try:
        tts = gTTS(text=clean_text, lang=lang_code, slow=False)
        tts.save(temp_file)
        play_mp3(temp_file)
        return
    except Exception:
        pass

    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 160)
        engine.say(clean_text)
        engine.runAndWait()
    except Exception as e:
        print(f"[Ses Hatası]: {e}")

def listen(stt_lang="tr-TR"):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print(f"\n🎤 Jarvis dinliyor [{stt_lang}]... (Çıkış: 'sesli sohbeti kapat' / Dil: 'İngilizceye geç')")
        r.adjust_for_ambient_noise(source, duration=0.4)
        try:
            audio = r.listen(source, timeout=6, phrase_time_limit=15)
            try:
                text = r.recognize_google(audio, language=stt_lang)
            except Exception:
                fallback = "en-US" if stt_lang != "en-US" else "tr-TR"
                text = r.recognize_google(audio, language=fallback)
            print(f"Sen (Sesli): {text}")
            return text
        except sr.WaitTimeoutError:
            return ""
        except Exception:
            print("  [Ses tam anlaşılamadı, tekrar dinleniyor...]")
            return ""

# ==========================================
# 2. VERİTABANI & HİBRİT OBSIDIAN RAG SİSTEMİ
# ==========================================
def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
            role TEXT NOT NULL, content TEXT NOT NULL, provider TEXT NOT NULL)""")
        db.commit()

def save_exchange(user_text, reply, provider):
    stamp = datetime.now().astimezone().isoformat(timespec="seconds")
    with sqlite3.connect(DB_PATH) as db:
        db.executemany("INSERT INTO messages (created_at, role, content, provider) VALUES (?, ?, ?, ?)",
            [(stamp, "user", user_text, provider), (stamp, "assistant", reply, provider)])
        db.commit()

def load_history(limit=MAX_MESSAGES):
    with sqlite3.connect(DB_PATH) as db:
        rows = db.execute("SELECT role, content FROM messages ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [{"role": role, "content": content} for role, content in reversed(rows)]

def export_summary():
    with sqlite3.connect(DB_PATH) as db:
        rows = db.execute("SELECT created_at, role, content, provider FROM messages ORDER BY id DESC LIMIT 20").fetchall()
    lines = ["# Gurkan AI — JARVIS Devir Notu", "", "## Son 20 Mesaj"]
    for date, role, content, provider in reversed(rows):
        lines.append(f"\n### {date} — {role} ({provider})\n\n{content}\n")
    EXPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    return EXPORT_PATH

def make_client(name):
    p = PROVIDERS[name]
    return OpenAI(base_url=p["base_url"], api_key=p["api_key"] or "yerel-anahtar", timeout=p["timeout"], max_retries=0)

def clean_thinking(text):
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"<think>.*$", "", text, flags=re.DOTALL)
    return strip_chinese(text).strip()

def list_notes():
    if not VAULT_PATH.is_dir():
        return []
    notes = []
    for path in VAULT_PATH.rglob("*.md"):
        relative = path.relative_to(VAULT_PATH)
        if any(part.startswith(".") for part in relative.parts):
            continue
        if path.is_file() and path.stat().st_size <= MAX_NOTE_SIZE:
            notes.append((relative.as_posix(), path))
    return sorted(notes, key=lambda item: item[0].casefold())

def normalize_words(text):
    text = unicodedata.normalize("NFKC", text).casefold()
    return set(re.findall(r"\w+", text, flags=re.UNICODE))

def chunk_note(text):
    text = text.strip()
    if not text:
        return []
    chunks, start = [], 0
    while start < len(text):
        end = min(len(text), start + CHUNK_CHARS)
        if end < len(text):
            split = text.rfind("\n", start + CHUNK_CHARS // 2, end)
            if split > start:
                end = split + 1
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(start + 1, end - CHUNK_OVERLAP)
    return [c for c in chunks if c]

def init_vector_db():
    with sqlite3.connect(INDEX_PATH) as db:
        db.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS documents (path TEXT PRIMARY KEY, sha256 TEXT NOT NULL)")
        db.execute("""CREATE TABLE IF NOT EXISTS chunks (
            path TEXT NOT NULL, chunk_no INTEGER NOT NULL,
            content TEXT NOT NULL, embedding TEXT NOT NULL,
            PRIMARY KEY (path, chunk_no))""")
        db.commit()

def embed_texts(texts):
    client = make_client("yerel")
    result = client.embeddings.create(model=EMBED_MODEL, input=texts)
    ordered = sorted(result.data, key=lambda d: d.index)
    return [list(item.embedding) for item in ordered]

def index_notes():
    init_vector_db()
    note_items = list_notes()
    current = {rel for rel, _ in note_items}
    with sqlite3.connect(INDEX_PATH) as db:
        old = dict(db.execute("SELECT path, sha256 FROM documents").fetchall())
    processed = 0
    for rel, path in note_items:
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if old.get(rel) == digest:
            continue
        text = raw.decode("utf-8-sig")
        chunks = chunk_note(text)
        embeddings = []
        for start in range(0, len(chunks), 8):
            embeddings += embed_texts(chunks[start:start+8])
        with sqlite3.connect(INDEX_PATH) as db:
            db.execute("DELETE FROM chunks WHERE path = ?", (rel,))
            for n, (content, vec) in enumerate(zip(chunks, embeddings)):
                db.execute("INSERT INTO chunks VALUES (?, ?, ?, ?)",
                           (rel, n, content, json.dumps(vec, separators=(',', ':'))))
            db.execute("INSERT OR REPLACE INTO documents VALUES (?, ?)", (rel, digest))
            db.execute("INSERT OR REPLACE INTO metadata VALUES ('model', ?)", (EMBED_MODEL,))
            db.commit()
        processed += 1
        print(f"  İndekslendi: {rel} ({len(chunks)} parça)")
    with sqlite3.connect(INDEX_PATH) as db:
        for rel in set(old) - current:
            db.execute("DELETE FROM chunks WHERE path=?", (rel,))
            db.execute("DELETE FROM documents WHERE path=?", (rel,))
        db.commit()
        total = db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    return processed, len(set(old) - current), total

def cosine(a, b):
    if len(a) != len(b): return -1.0
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(x*x for x in b))
    return sum(x*y for x,y in zip(a,b))/(na*nb) if na and nb else -1.0

def hybrid_search(question, count=4):
    if not INDEX_PATH.exists(): return []
    init_vector_db()
    with sqlite3.connect(INDEX_PATH) as db:
        rows = db.execute("SELECT path, chunk_no, content, embedding FROM chunks").fetchall()
    if not rows: return []
    try:
        query_vec = embed_texts([question])[0]
    except Exception:
        return []
    query_terms = normalize_words(question)
    term_freqs = [Counter(re.findall(r"\w+", content.casefold(), re.UNICODE)) for _, _, content, _ in rows]
    lengths = [sum(tf.values()) for tf in term_freqs]
    avg_len = sum(lengths) / len(lengths) if lengths else 1
    df = Counter(term for tf in term_freqs for term in tf)
    n_docs = len(rows)
    records = []
    for (rel, no, content, vec_json), tf, length in zip(rows, term_freqs, lengths):
        vec = json.loads(vec_json)
        similarity = cosine(query_vec, vec)
        lexical = 0.0
        for term in query_terms:
            freq = tf.get(term, 0)
            if not freq: continue
            idf = math.log(1 + (n_docs - df[term] + 0.5) / (df[term] + 0.5))
            lexical += idf * freq * 2.2 / (freq + 1.2 * (0.25 + 0.75 * length / max(avg_len, 1)))
        lexical += 1.5 * len(query_terms & normalize_words(rel))
        records.append((similarity, lexical, rel, no, content))
    by_vector = sorted(range(len(records)), key=lambda i: records[i][0], reverse=True)
    by_keyword = sorted(range(len(records)), key=lambda i: records[i][1], reverse=True)
    vector_rank = {i: rank for rank, i in enumerate(by_vector, 1)}
    keyword_rank = {i: rank for rank, i in enumerate(by_keyword, 1)}
    fused = []
    for i, (sim, lexical, rel, no, content) in enumerate(records):
        score = 1 / (60 + vector_rank[i]) + (1 / (60 + keyword_rank[i]) if lexical > 0 else 0)
        fused.append((score, sim, lexical, rel, no, content))
    fused.sort(key=lambda row: (-row[0], -row[1]))
    return fused[:count]

def search_obsidian_notes(sorgu):
    matches = hybrid_search(sorgu, count=3)
    if matches:
        return "\n\n---\n\n".join(f"KAYNAK: {rel} (parça {no+1})\n{cnt}" for _, _, _, rel, no, cnt in matches)
    
    words = normalize_words(sorgu)
    if not words:
        return "Arama terimi boş."
    candidates = []
    for relative, path in list_notes():
        try:
            content = path.read_text(encoding="utf-8-sig")
        except Exception:
            continue
        score = len(words & normalize_words(content)) + 3 * len(words & normalize_words(relative))
        if score > 0:
            candidates.append((score, relative, content[:1500]))
    candidates.sort(key=lambda item: (-item[0], item[1]))
    if not candidates:
        return "Obsidian notlarında bu konuyla ilgili bilgi bulunamadı."
    return "\n\n---\n\n".join(f"KAYNAK: {rel}\n{cnt}" for _, rel, cnt in candidates[:3])

# ==========================================
# 3. AKSİYON ARAÇLARI (GÖRSEL ZEKA + MASAÜSTÜ + WEB + OBSIDIAN)
# ==========================================
def bilgi_durumu():
    """Notların kayıtlı güven durumunu SAYAR; doğruluğunu ispatlamaz."""
    files = list_notes()
    sayac = {"kaynakla_dogrulandi": 0, "uygulamada_test_edildi": 0,
             "taslak": 0, "etiketsiz": 0}
    for _, path in files:
        try:
            with path.open("r", encoding="utf-8-sig") as f:
                head = f.read(2500)
            match = re.match(r"\A---\s*\n(.*?)\n---\s*(?:\n|$)", head, re.S)
            if not match:
                sayac["etiketsiz"] += 1
                continue
            status = re.search(r"(?m)^durum:\s*[\"']?([\w-]+)", match.group(1))
            key = status.group(1) if status else "etiketsiz"
            sayac[key if key in sayac else "etiketsiz"] += 1
        except (OSError, UnicodeError):
            sayac["etiketsiz"] += 1
    return (f"Toplam: {len(files)} not | "
            f"Kaynakla doğrulandı etiketi: {sayac['kaynakla_dogrulandi']} | "
            f"Uygulamada test edildi etiketi: {sayac['uygulamada_test_edildi']} | "
            f"Taslak: {sayac['taslak']} | Etiketsiz/bilinmeyen: {sayac['etiketsiz']}. "
            "Etiketler gerçek doğrulama yerine geçmez.")

def get_time():
    return f"Saat: {datetime.now().strftime('%H:%M')} | Tarih: {datetime.now().strftime('%d.%m.%Y')}"

def web_search(sorgu):
    try:
        results = DDGS().text(sorgu, max_results=3)
        return json.dumps(results, ensure_ascii=False) if results else "Sonuç bulunamadı."
    except Exception as e:
        return f"Arama hatası: {e}"

def create_obsidian_note(baslik, icerik):
    """Yalnızca taslak hazırlar; yazma yetkisi için /onayla gerekir."""
    global PENDING_NOTE
    safe_title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', str(baslik)).strip(' .')[:100] or 'Yeni_Not'
    if not str(icerik).strip():
        return 'Boş içerik kaydedilemez.'
    if len(str(icerik)) > MAX_NOTE_SIZE:
        return 'Not çok uzun, kaydedilmedi.'
    filepath = APPROVED_DIR / f"{safe_title}.md"
    if filepath.exists():
        return f"'{safe_title}.md' zaten var. Mevcut dosyanın üzerine yazmayacağım."
    header = ('---\ndurum: taslak\nkaynak_turu: belirtilmedi\n'
              'kaynak_url: ""\ndogrulama_tarihi: ""\n'
              'jarvis_surumu: "2.9.1"\n---\n\n')
    content = str(icerik)
    if not content.lstrip().startswith('---'):
        content = header + content
    PENDING_NOTE = (filepath, content)
    return (f"'{safe_title}.md' için TASLAK hazırlandı, henüz kaydedilmedi. "
            "Dosyayı yazmak için terminalde /onayla, iptal etmek için /reddet yaz. "
            "Bu taslak DOĞRULANMIŞ bilgi sayılmaz.")


def approve_obsidian_note():
    global PENDING_NOTE
    if PENDING_NOTE is None:
        return 'Onay bekleyen not yok.'
    filepath, content = PENDING_NOTE
    try:
        APPROVED_DIR.mkdir(parents=True, exist_ok=True)
        # x: aynı isimli dosyanın üzerine yazılmasını atomik olarak engeller.
        with filepath.open('x', encoding='utf-8') as f:
            f.write(content)
        PENDING_NOTE = None
        return f"Taslak kaydedildi: {filepath.name}. Durumu: taslak (doğrulanmadı)."
    except FileExistsError:
        PENDING_NOTE = None
        return 'Bu isimde not zaten var. Üzerine yazılmadı.'
    except OSError as e:
        return f'Not kaydedilemedi: {e}'

def open_application_or_site(hedef):
    h = hedef.lower().strip()
    apps = {
        "hesap makinesi": "calc.exe",
        "calculator": "calc.exe",
        "not defteri": "notepad.exe",
        "notepad": "notepad.exe",
        "cmd": "cmd.exe",
        "komut istemi": "cmd.exe",
        "görev yöneticisi": "taskmgr.exe",
        "paint": "mspaint.exe",
        "dosya gezgini": "explorer.exe",
    }
    sites = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "github": "https://www.github.com",
        "chatgpt": "https://chatgpt.com",
    }
    try:
        for key, cmd in apps.items():
            if key in h:
                subprocess.Popen(cmd)
                return f"{key} uygulaması açıldı."
        for key, url in sites.items():
            if key in h:
                webbrowser.open(url)
                return f"{key} web sitesi açıldı."
        if h.startswith("http://") or h.startswith("https://") or ".com" in h or ".org" in h:
            url = h if h.startswith("http") else f"https://{h}"
            webbrowser.open(url)
            return f"{url} tarayıcıda açıldı."
        return "Güvenlik nedeniyle yalnızca izin verilen uygulama ve siteleri açabilirim."
    except Exception as e:
        return f"Hedef açılamadı: {e}"

def get_system_status():
    if not psutil:
        return "psutil kütüphanesi kurulu değil (pip install psutil)."
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent
    battery = psutil.sensors_battery()
    bat_str = f", Pil: %{battery.percent}" if battery else ""
    return f"Sistem Durumu -> İşlemci (CPU) Kullanımı: %{cpu}, Bellek (RAM) Kullanımı: %{ram}{bat_str}"

def take_screenshot(isim="ekran_goruntusu"):
    if not ImageGrab:
        return "Pillow kütüphanesi kurulu değil (pip install pillow)."
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = re.sub(r'[<>:"/\\|?*]', '', isim).strip() or "ekran"
    filepath = BASE_DIR / f"{safe_name}_{stamp}.png"
    try:
        img = ImageGrab.grab()
        img.save(filepath)
        return f"Ekran görüntüsü kaydedildi: {filepath.name}"
    except Exception as e:
        return f"Ekran görüntüsü alınamadı: {e}"

def analyze_screen(soru="Ekranda ne var ve hangi pencereler/yazılar görünüyor?"):
    """Ekran görüntüsünü yakalar, OCR ile içindeki tüm metinleri/hataları okur ve varsa Vision modeliyle inceler."""
    if not ImageGrab:
        return "Pillow kütüphanesi kurulu değil (pip install pillow)."
    
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = BASE_DIR / f"vision_{stamp}.png"
    try:
        img = ImageGrab.grab()
        img.save(filepath)
    except Exception as e:
        return f"Ekran yakalanamadı: {e}"

    rapor = [f"Ekran görüntüsü '{filepath.name}' olarak kaydedildi."]

    # 1. Aşama: Yerel OCR (RapidOCR) ile ekrandaki tüm yazıları/hataları/kodları oku
    ocr_text = ""
    if ocr_engine is not None:
        try:
            result, _ = ocr_engine(str(filepath))
            if result:
                lines = [line[1] for line in result if len(line) > 1]
                ocr_text = "\n".join(lines)
        except Exception as e:
            rapor.append(f"OCR okuma uyarısı: {e}")
    else:
        rapor.append("Not: 'pip install rapidocr-onnxruntime' kurulu olmadığı için yerel OCR atlandı.")

    # 2. Aşama: Google Vision yalnızca JARVIS_GOOGLE_VISION=1 ise çalışır.
    if GOOGLE_VISION_ALLOWED and PROVIDERS["google"]["api_key"]:
        try:
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            b64_img = base64.b64encode(buf.getvalue()).decode("utf-8")
            g_client = make_client("google")
            v_resp = g_client.chat.completions.create(
                model=PROVIDERS["google"]["model"],
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Kullanıcının sorusu: {soru}. Bu ekran görüntüsünü kısaca analiz et."},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_img}"}}
                    ]
                }]
            )
            rapor.append("Görsel Model Analizi: " + v_resp.choices[0].message.content.strip())
        except Exception:
            pass

    if ocr_text:
        # Çok uzunsa ilk 3500 karakteri al ki yerel modelin hafızası taşmasın
        rapor.append(f"Ekranda Okunan Metinler / Pencereler (OCR):\n{ocr_text[:3500]}")
    elif len(rapor) == 1:
        rapor.append("Ekranda okunabilir bir metin bulunamadı veya OCR paketi (rapidocr-onnxruntime) henüz kurulmadı.")

    return "\n\n".join(rapor)

def analyze_other_window():
    """/gor-5: Kullaniciya hedef pencereye gecmesi icin zaman verir.

    OCR sonucunu yalnizca yerel LM Studio ile ozetler; buluta yollamaz.
    """
    print("\n[EKRAN TESTI] 5 saniyen var: ALT+TAB ile incelemek istedigin pencereye gec.")
    print("[EKRAN TESTI] JARVIS terminali yerine hedef program on planda olmali.")
    for sec in range(5, 0, -1):
        print(f"  {sec}...", flush=True)
        time.sleep(1)

    # Google Vision ayari acik olsa bile bu ozel testte ekran sadece yerel
    # OCR tarafindan okunur. Global ayari try/finally ile eski haline getir.
    global GOOGLE_VISION_ALLOWED
    old = GOOGLE_VISION_ALLOWED
    GOOGLE_VISION_ALLOWED = False
    try:
        report = analyze_screen("Ekrandaki metinleri oldugu gibi oku ve kisaca ozetle.")
    finally:
        GOOGLE_VISION_ALLOWED = old

    ocr_part = report.split("Ekranda Okunan Metinler / Pencereler (OCR):\n", 1)
    if len(ocr_part) != 2:
        return report
    extracted = ocr_part[1]
    # Yanlis pencereye donulurse, eski terminal metnini 'yeni sonuc' diye aktarma.
    terminal_signals = sum(marker.lower() in extracted.lower() for marker in (
        "JARVIS v2.", "Gurkan [tr-TR]", "Jarvis dusunuyor", "Jarvis düşünüyor", "/bilgi-durum"))
    if terminal_signals >= 2:
        return ("JARVIS terminali hâlâ ekranda görünüyor. "
                "Komutu tekrar verip 5 saniye içinde Alt+Tab ile başka bir pencereye geç.")
    try:
        client = make_client("yerel")
        response = client.chat.completions.create(
            model=PROVIDERS["yerel"]["model"],
            messages=[
                {"role": "system", "content": (
                    "Sen yerel OCR inceleyicisisin. SADECE verilen ekrandan okunmuş metinleri kullan. "
                    "Görmediğin pencere, düğme ve görselleri uydurma. OCR hataları varsa belirsiz olduğunu söyle. "
                    "En fazla üç Türkçe cümlede doğal dille özetle; Markdown veya madde işareti kullanma. "
                    "Önceki sohbetleri ekran kanıtı sayma.")},
                {"role": "user", "content": "Ekran OCR metni:\n" + extracted[:3500]},
            ],
            temperature=0.1,
        )
        reply = response.choices[0].message.content or ""
        return clean_thinking(reply) or "OCR metni alındı ancak özet üretilemedi."
    except Exception as err:
        return ("Ekran OCR ile okundu ancak yerel model özetleyemedi. "
                f"Hata: {type(err).__name__}. Okunan metnin ilk kısmı: " + extracted[:600])


tools = [
    {"type": "function", "function": {"name": "get_time", "description": "Geçerli saati ve tarihi söyler."}},
    {
        "type": "function",
        "function": {
            "name": "analyze_screen",
            "description": "Kullanıcı 'ekranımda ne var', 'ekrana bak', 'bu hatayı nasıl çözerim', 'ekrandaki yazıyı oku' dediğinde bilgisayar ekranını görüp analiz eder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "soru": {"type": "string", "description": "Ekranla ilgili sorulan soru veya odaklanılacak detay"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "İnternette güncel haberleri, fiyatları veya bilgileri arar.",
            "parameters": {"type": "object", "properties": {"sorgu": {"type": "string"}}, "required": ["sorgu"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_obsidian_notes",
            "description": "Yalnızca JARVIS Obsidian bilgi bankasındaki notlarda arama yapar.",
            "parameters": {"type": "object", "properties": {"sorgu": {"type": "string"}}, "required": ["sorgu"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_obsidian_note",
            "description": "Obsidian için doğrulanmamış Markdown taslağı oluşturur. Kullanıcı /onayla demeden kaydetmez.",
            "parameters": {
                "type": "object",
                "properties": {
                    "baslik": {"type": "string", "description": "Dosya adı"},
                    "icerik": {"type": "string", "description": "Not içeriği"}
                },
                "required": ["baslik", "icerik"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_application_or_site",
            "description": "Bilgisayarda program (hesap makinesi, not defteri, cmd) veya web sitesi (youtube, google vb.) açar.",
            "parameters": {"type": "object", "properties": {"hedef": {"type": "string"}}, "required": ["hedef"]}
        }
    },
    {
        "type": "function",
        "function": {"name": "get_system_status", "description": "Bilgisayarın CPU, RAM ve pil kullanım durumunu raporlar."}
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Sadece ekran görüntüsü alıp kaydetmek istendiğinde kullanılır.",
            "parameters": {"type": "object", "properties": {"isim": {"type": "string"}}, "required": []}
        }
    }
]

def get_reply_with_tools(name, history, user_message):
    p = PROVIDERS[name]
    current = user_message + (" /no_think" if p["no_think"] else "")
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-(MAX_MESSAGES - 1):] + [{"role": "user", "content": current}]
    client = make_client(name)
    
    if name == "yerel":
        response = client.chat.completions.create(model=p["model"], messages=messages, tools=tools, temperature=0.3)
        response_message = response.choices[0].message
        
        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                func_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments or "{}")
                print(f"⚙️ [Jarvis Aksiyon Alıyor: {func_name}]")
                
                if func_name == "get_time": result = get_time()
                elif func_name == "analyze_screen": result = analyze_screen(args.get("soru", user_message))
                elif func_name == "web_search": result = web_search(args.get("sorgu", ""))
                elif func_name == "search_obsidian_notes": result = search_obsidian_notes(args.get("sorgu", ""))
                elif func_name == "create_obsidian_note": result = create_obsidian_note(args.get("baslik", "Not"), args.get("icerik", ""))
                elif func_name == "open_application_or_site": result = open_application_or_site(args.get("hedef", ""))
                elif func_name == "get_system_status": result = get_system_status()
                elif func_name == "take_screenshot": result = take_screenshot(args.get("isim", "ekran"))
                else: result = "Bilinmeyen fonksiyon."
                
                messages.append(response_message)
                messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
                
            final_response = client.chat.completions.create(model=p["model"], messages=messages)
            return clean_thinking(final_response.choices[0].message.content.strip())
            
        return clean_thinking(response_message.content.strip() if response_message.content else "Tamamdır patron.")
    else:
        stream = client.chat.completions.create(model=p["model"], messages=messages, stream=True, temperature=0.7)
        parts = [chunk.choices[0].delta.content or "" for chunk in stream if chunk.choices]
        return clean_thinking("".join(parts))

# ==========================================
# 4. ANA DÖNGÜ
# ==========================================
def main():
    global CURRENT_STT_LANG
    init_db()
    history = load_history()
    provider = "yerel"
    voice_mode = False
    
    print("="*72)
    print("JARVIS v2.9.2 — GÖRSEL ZEKALI (VISION/OCR) & MASAÜSTÜ KONTROLLÜ AJAN AKTİF")
    print("="*72)
    print("Komutlar: /yerel /google /tr /en /de /gor /notlar /indeksle /aktar /ses-test /bilgi-durum /gor-5 /onayla /reddet /cik")
    print("Sesli Mod: 's' yazıp Enter'a basınca KESİNTİSİZ SESLİ SOHBET başlar.\n")
    
    speak("Sistemler devrede patron. Görsel zeka ve ekran okuma modülü aktif.")
    
    while True:
        if voice_mode:
            user = listen(CURRENT_STT_LANG)
            if not user:
                continue
            low = user.lower()
            
            if any(k in low for k in ["sesli sohbeti kapat", "sesliyi kapat", "sessize geç", "stop voice", "text mode"]):
                voice_mode = False
                speak("Sesli sohbet kapatıldı patron, yazılı moda geçtim.")
                continue
            if any(k in low for k in ["sistemi kapat", "programı kapat", "shut down", "exit program"]):
                speak("Sistem kapatılıyor, görüşmek üzere.")
                break
                
            if any(k in low for k in ["ingilizceye geç", "ingilizce dinle", "switch to english", "speak english"]):
                CURRENT_STT_LANG = "en-US"
                speak("Switched to English mode. I am listening to you, boss.")
                continue
            if any(k in low for k in ["türkçeye geç", "türkçe dinle", "switch to turkish", "speak turkish"]):
                CURRENT_STT_LANG = "tr-TR"
                speak("Türkçe moduna geçildi patron, seni dinliyorum.")
                continue
            if any(k in low for k in ["almancaya geç", "switch to german"]):
                CURRENT_STT_LANG = "de-DE"
                speak("Ich höre dir jetzt auf Deutsch zu, Chef.")
                continue
        else:
            try:
                user = input(f"\n{USER_NAME} [{CURRENT_STT_LANG}] (Ses için 's'): ").strip()
            except (EOFError, KeyboardInterrupt):
                speak("Sistem kapatılıyor, görüşmek üzere.")
                break
            if not user:
                continue
            if user.lower() == 's':
                voice_mode = True
                speak("Kesintisiz sesli sohbet aktif. Seni dinliyorum.")
                continue

        if user == "/gor-5":
            reply = analyze_other_window()
            speak(reply)
            # Ekran okuma sonucu veritabaninda tutuluyor, ancak ekranin
            # hassas veri tasiyabilecegini bilerek bu komutu kullan.
            save_exchange("/gor-5", reply, "yerel")
            history = load_history()
            continue
        if user == "/ses-test":
            seslendirme_testi()
            continue
        if user == "/bilgi-durum":
            print("Jarvis:", bilgi_durumu())
            continue
        if user == "/onayla":
            print("Jarvis:", approve_obsidian_note())
            continue
        if user == "/reddet":
            global PENDING_NOTE
            PENDING_NOTE = None
            print("Jarvis: Bekleyen taslak iptal edildi.")
            continue
        if user == "/cik":
            speak("Sistem kapatılıyor, görüşmek üzere.")
            break
        if user == "/gor":
            user = "Şu an ekranımda ne var, hangi yazılar veya pencereler açık analiz et."
        if user == "/en":
            CURRENT_STT_LANG = "en-US"
            speak("Microphone set to English. How can I help you?")
            continue
        if user == "/tr":
            CURRENT_STT_LANG = "tr-TR"
            speak("Mikrofon Türkçeye ayarlandı patron.")
            continue
        if user == "/de":
            CURRENT_STT_LANG = "de-DE"
            speak("Mikrofon auf Deutsch eingestellt.")
            continue
        if user in ("/yerel", "/google"):
            provider = user[1:]
            speak(f"{provider} motoruna geçiş yapıldı.")
            continue
        if user == "/notlar":
            for rel, _ in list_notes()[:30]:
                print(f"  - {rel}")
            continue
        if user == "/indeksle":
            try:
                print("Jarvis: Obsidian notları vektör veritabanına indeksleniyor...")
                changed, removed, chunks = index_notes()
                speak(f"İndeksleme tamamlandı. Toplam {chunks} parça hafızaya alındı.")
            except Exception as e:
                print(f"[Hata] İndeksleme başarısız: {e}")
            continue
        if user == "/aktar":
            path = export_summary()
            print(f"Jarvis: Proje özeti kaydedildi -> {path}")
            continue

        try:
            print("Jarvis düşünüyor...")
            reply = get_reply_with_tools(provider, history, user)
            speak(reply)
            save_exchange(user, reply, provider)
            history = load_history()
        except Exception as exc:
            print(f"[Hata] Bağlantı hatası: {exc}")
            speak("Patron, yerel motora bağlanırken bir sorun yaşadım. LM Studio açık mı?")

if __name__ == "__main__":
    main()
