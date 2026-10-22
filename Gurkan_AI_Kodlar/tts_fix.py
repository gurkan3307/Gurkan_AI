"""tts_fix.py - Jarvis için Türkçe telaffuz düzeltici.

Ses motoru metni olduğu gibi okur; sayılar, tarihler, saatler, birimler ve yabancı
kelimeler bu yüzden bozuk çıkar ("on dokuz nokta on nokta iki bin yirmi altı", "Jarvis" -> "Jarvis" gibi).
Bu modül metni SESİ ÜRETMEDEN ÖNCE okunacak hâle getirir.

Kullanım (speak() içinde, sesi üretmeden hemen önce):
    from tts_fix import prepare_for_speech
    clean_text = prepare_for_speech(clean_text)

Kendi sözlüğün: bu dosyanın yanındaki pronunciation.json (yoksa oluştur), örn:
    {"Wartune": "Vortyun", "Gemini 2.5": "Cemini iki nokta beş"}
Dosyayı kaydedince Jarvis'i kapatmadan geçerli olur.

Deneme:  python tts_fix.py "Sıcaklık 12°C, saat 13:24, tarih 19.10.2026"
"""
import json
import os
import re
import sys

DICT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pronunciation.json")

# Yaygın düzeltmeler. Kendi eklediklerin pronunciation.json'dan gelir ve bunların üstüne yazar.
DEFAULT_DICT = {
    "Jarvis": "Carvis",          # Türkçe 'j' yumuşak okunur, İngilizce J = Türkçe 'c'
    "Gemini": "Cemini",
    "Qwen": "Çuen",
    "Python": "Payton",
    "Obsidian": "Obsidiyan",
    "LM Studio": "El Em Stüdyo",
    "API": "ey pi ay",
    "AI": "yapay zeka",
}

ONES = ["", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
TENS = ["", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan"]
MONTHS = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
          "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
SCALES = ["", "bin", "milyon", "milyar", "trilyon"]

UNITS = {  # sayıdan sonra gelen kısaltmalar
    "TL": "lira", "GB": "gigabayt", "MB": "megabayt", "KB": "kilobayt", "TB": "terabayt",
    "km": "kilometre", "kg": "kilogram", "cm": "santimetre", "mm": "milimetre",
    "USD": "dolar", "EUR": "avro", "Hz": "hertz", "kHz": "kilohertz", "MHz": "megahertz",
    "GHz": "gigahertz", "W": "vat", "V": "volt", "A": "amper",
}


def _below_1000(n):
    h, r = divmod(n, 100)
    t, o = divmod(r, 10)
    words = []
    if h:
        words.append(("" if h == 1 else ONES[h] + " ") + "yüz")
    if t:
        words.append(TENS[t])
    if o:
        words.append(ONES[o])
    return " ".join(w.strip() for w in words if w.strip())


def number_to_turkish(n):
    if n == 0:
        return "sıfır"
    if n < 0:
        return "eksi " + number_to_turkish(-n)
    parts, i = [], 0
    while n > 0 and i < len(SCALES):
        n, chunk = divmod(n, 1000)
        if chunk:
            if i == 1 and chunk == 1:
                parts.append("bin")  # "bir bin" denmez
            else:
                parts.append((_below_1000(chunk) + " " + SCALES[i]).strip())
        i += 1
    return " ".join(reversed(parts))


def _digits_words(s):
    return " ".join("sıfır" if d == "0" else ONES[int(d)] for d in s if d.isdigit())


def _to_float_words(text):
    """'12,5' / '12.5' / '1.234,5' / '32.000' -> Türkçe okunuş."""
    m = re.fullmatch(r"(\d{1,3}(?:\.\d{3})+|\d+)(?:[,.](\d+))?", text)
    if not m:
        return text
    whole, frac = m.group(1), m.group(2)
    digits = whole.replace(".", "")
    if len(digits) >= 8 and "." not in whole and frac is None:
        return _digits_words(digits)  # telefon / kimlik numarası: rakam rakam
    if int(digits) >= 10 ** 15:
        return text
    out = number_to_turkish(int(digits))
    if frac is not None:
        out += " virgül " + (_digits_words(frac) if frac.startswith("0") else number_to_turkish(int(frac)))
    return out


def _load_user_dict():
    try:
        with open(DICT_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
        return {str(k): str(v) for k, v in data.items()}
    except (OSError, ValueError):
        return {}


def _apply_dict(text):
    merged = dict(DEFAULT_DICT)
    merged.update(_load_user_dict())
    for key in sorted(merged, key=len, reverse=True):  # uzun anahtar önce
        text = re.sub(r"(?<!\w)" + re.escape(key) + r"(?![^\W\d])", lambda _m, v=merged[key]: v,  # "Qwen3" de eşleşsin
                      text, flags=re.IGNORECASE)
    return text


NUM = r"(\d{1,3}(?:\.\d{3})+|\d+)(?:[,.]\d+)?"


def prepare_for_speech(text, lang="tr"):
    """Metni sese çevrilmeden önce okunabilir hâle getirir. lang != 'tr' ise sadece temizler."""
    t = text or ""

    # --- temizlik: markdown, bağlantı, emoji ---
    t = re.sub(r"\[([^\]]+)\]\((?:https?://)[^)]+\)", r"\1", t)
    t = re.sub(r"https?://\S+", " bağlantı ", t)
    t = re.sub(r"[*_`#>]+", " ", t)
    t = re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F]", "", t)
    t = t.replace("—", ", ").replace("–", ", ").replace("→", ", ").replace("&", " ve ")
    if lang != "tr":
        return re.sub(r"\s+", " ", t).strip()

    t = _apply_dict(t)
    t = re.sub(r"([^\W\d_])(\d)", r"\1 \2", t)  # Qwen3 -> Qwen 3, Python3 -> Python 3

    # --- tarih 19.10.2026 / 19/10/2026 ---
    def date_repl(m):
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= d <= 31 and 1 <= mo <= 12:
            return f" {number_to_turkish(d)} {MONTHS[mo]} {number_to_turkish(y)} "
        return m.group(0)
    t = re.sub(r"(?<![\w.])(\d{1,2})[./](\d{1,2})[./](\d{4})(?!\d)", date_repl, t)

    # --- saat 13:24 ---
    def time_repl(m):
        h, mi = int(m.group(1)), int(m.group(2))
        out = number_to_turkish(h)
        if mi:
            out += (" sıfır " if mi < 10 else " ") + number_to_turkish(mi)
        return f" {out} "
    t = re.sub(r"(?<![\w:])([01]?\d|2[0-3]):([0-5]\d)(?![\w:])", time_repl, t)

    # --- sürüm numarası 3.12.10 -> "3 nokta 12 nokta 10" ---
    t = re.sub(r"(?<![\w.])\d+(?:\.\d+){2,}(?![\w.])",
               lambda m: " nokta ".join(number_to_turkish(int(p)) for p in m.group(0).split(".")), t)

    # --- yüzde, derece, para ---
    t = re.sub(r"%\s?" + NUM, lambda m: " yüzde " + _to_float_words(m.group(0).lstrip("% ")) + " ", t)
    t = re.sub(NUM + r"\s?%", lambda m: " yüzde " + _to_float_words(m.group(0).rstrip("% ")) + " ", t)
    t = re.sub(r"(-?)" + NUM + r"\s?°\s?[CcFf]?", lambda m: (" eksi " if m.group(1) else " ")
               + _to_float_words(m.group(0).lstrip("-").split("°")[0].strip()) + " derece ", t)
    for sym, word in (("₺", "lira"), ("$", "dolar"), ("€", "avro")):
        t = re.sub(re.escape(sym) + r"\s?" + NUM,
                   lambda m, w=word, s=sym: " " + _to_float_words(m.group(0).replace(s, "").strip()) + " " + w + " ", t)

    # --- sayıların kendisi ---
    t = re.sub(r"(?<![\w.,])" + NUM, lambda m: " " + _to_float_words(m.group(0)) + " ", t)

    # --- birimler (sayıdan sonra) ---
    for abbr in sorted(UNITS, key=len, reverse=True):
        t = re.sub(r"(?<!\w)" + re.escape(abbr) + r"(?!\w)", UNITS[abbr], t)

    t = t.replace("°", " derece ")
    t = re.sub(r"\s+", " ", t)
    return re.sub(r"\s+([,.;:!?])", r"\1", t).strip()


if __name__ == "__main__":
    sample = " ".join(sys.argv[1:]) or (
        "Jarvis: Sıcaklık 12°C, saat 13:24, tarih 19.10.2026. Bakiye 32.000 TL, yüzde 20 zam, "
        "8GB RAM, Python 3.12.10 ve Qwen3 ile Gemini kullanıyorum."
    )
    print(prepare_for_speech(sample))
