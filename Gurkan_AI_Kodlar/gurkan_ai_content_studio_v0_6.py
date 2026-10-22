"""GURKAN AI Content Studio v0.6 - kaynak sinirli, konu kontrollu taslak ve TTS."""
import asyncio
import io
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path

import streamlit as st
from openai import OpenAI
import edge_tts

BASE_URL = 'http://127.0.0.1:1234/v1'
DEFAULT_MODEL = 'qwen/qwen3-8b'
VOICES = {
    'TR - Emel': 'tr-TR-EmelNeural',
    'TR - Ahmet': 'tr-TR-AhmetNeural',
    'EN - Aria': 'en-US-AriaNeural',
    'EN - Christopher': 'en-US-ChristopherNeural',
}
SCHEMA_KEYS = ('narration', 'scene_notes', 'claims_to_verify', 'summary')


def normalize(value):
    value = unicodedata.normalize('NFKC', str(value)).casefold()
    value = value.replace('â', 'a').replace('î', 'i').replace('û', 'u')
    return re.sub(r'[^\w\s]', ' ', value, flags=re.UNICODE).strip()


def subject_terms(subject):
    ignored = {'ve', 'ile', 'bir', 'the', 'and', 'için', 'nedir', 'nasıl', 'tarihi', 'geçmişi', 'hakkında', 'about', 'history', 'of'}
    return [x for x in normalize(subject).split() if len(x) >= 3 and x not in ignored]


def focus_check(narration, subject, alias=''):
    """Yalnizca yuzeysel konu-isim kontrolu. Semantik dogrulama degildir."""
    haystack = normalize(narration)
    terms = subject_terms(subject)
    if not terms:
        return False, 'Ana konuyu daha belirgin girin (ör. Mekke Kâbe yapısı).'
    if any(term in haystack.split() for term in terms):
        return True, 'Konu anahtar sözcüğü metinde var; anlam/doğruluk ayrıca incelenmeli.'
    if alias and normalize(alias) in haystack:
        return True, 'Konu eşanlamlı ifadesi görüldü; ayrıca kontrol edilmeli.'
    return False, 'Ana konu metinde bulunamadı. Metin onaya/seslendirmeye kapatıldı.'


def parse_json_output(raw):
    raw = (raw or '').strip()
    raw = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw, flags=re.I)
    try:
        val = json.loads(raw)
    except json.JSONDecodeError:
        # Yalnızca içteki JSON nesnesini bul, hatalı formatı sessizce kabul etme.
        start, end = raw.find('{'), raw.rfind('}')
        if start == -1 or end <= start:
            raise ValueError('Model JSON yerine düz metin döndürdü; yeniden deneyin.')
        val = json.loads(raw[start:end + 1])
    if not isinstance(val, dict) or not all(k in val for k in SCHEMA_KEYS):
        raise ValueError('Model eksik alan döndürdü; güvenli ayrıştırma yapılamadı.')
    if not isinstance(val['narration'], str) or not val['narration'].strip():
        raise ValueError('Konuşma metni boş.')
    if not isinstance(val['scene_notes'], list) or not isinstance(val['claims_to_verify'], list):
        raise ValueError('Sahne notları ve iddialar liste olmalı.')
    return val


def narration_only(text):
    """Son emniyet filtresi; asil ayrim modelin narration alanindadir."""
    text = re.sub(r'\[[^\]\n]*\]', '', text)
    text = re.sub(r'(?im)^\s*(?:#{1,6}\s*)?(?:sahne|kamera|muzik|müzik|görüntü|arka plan|scene|background|visual|music)\s*[:：].*$', '', text)
    text = re.sub(r'(?m)^\s*#{1,6}\s+', '', text)
    text = re.sub(r'\*\*|__|`', '', text)
    text = re.sub(r'(?m)^\s*[-*_]{3,}\s*$', '', text)
    # Parantezli yonergeleri kaldir, anlamli parantezleri körlemesine silme.
    text = re.sub(r'\((?:arka planda|kamera|müzik|ses geçiş|görüntü|scene|music)[^)]*\)', '', text, flags=re.I)
    return re.sub(r'\s+', ' ', text).strip()


def chat(model, messages, max_tokens=2800, temperature=0.3):
    client = OpenAI(base_url=BASE_URL, api_key='lm-studio', timeout=150.0, max_retries=1)
    response = client.chat.completions.create(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
    content = response.choices[0].message.content
    if not content:
        raise ValueError('Model boş yanıt döndürdü.')
    # Bazi modellerin düşünme metnini ayır.
    return re.sub(r'<think>.*?</think>', '', content, flags=re.S).strip()


def create_script(subject, scope, alias, source, lang, minutes, model, mode):
    word_target = int(minutes * (125 if lang == 'Türkçe' else 135))
    if mode == 'Kaynağa bağlı (olgusal)' and len(source.strip()) < 80:
        raise ValueError('Olgusal mod için en az 80 karakter kaynak metni ekleyin. URL tek başına kaynak değildir.')
    source_rules = (
        'YALNIZCA kullanıcı tarafından verilen KAYNAK METNİ ile desteklenen olguları kullan. '
        'Kaynakta bulunmayan bir tarih, isim, sayı, olay veya iddia EKLEME. '
        'Bir iddia kaynakta yoksa narration metnine katma, claims_to_verify listesine ekle.'
        if mode == 'Kaynağa bağlı (olgusal)' else
        'Bu yaratici taslaktir; teyitsiz tarih, rakam, isim veya spesifik iddialari olgu olarak uydurma. '
        'Bilgi eksikse genelleme yap ya da claims_to_verify listesine uyarı ekle.'
    )
    prompt = f'''Sadece geçerli JSON nesnesi döndür, markdown kod çiti kullanma.
Alanlar: "narration" (tek seslendirme metni string), "scene_notes" (sahne önerileri string listesi), "claims_to_verify" (kaynak kontrolü gerektiren iddialar string listesi), "summary" (1 cümle).
KİLİTLİ ANA KONU: {subject}
KONU TANIMI / SINIR: {scope}
ALTERNATİF AD: {alias or 'Yok'}
DİL: {lang}; HEDEF KONUŞMA SÜRESİ: {minutes} dakika, yaklaşık {word_target} kelime.
MOD: {mode}
KAYNAK METNİ (web bağlantısı otomatik okunmaz; kullanıcı metnidir):
<source>\n{source[:18000]}\n</source>
KURALLAR:
- ANA KONU DIŞINA ÇIKMA. Benzer yazılan başka nesnelere veya kavramlara geçme.
- Kâbe -> kaba, tarih -> kılıç gibi yorumlar YASAK.
- {source_rules}
- narration yalnız konuşulacak cümleleri içersin. Müzik/kamera/sahne komutları ve başlıklar yalnız scene_notes içinde olsun.
- Tekrar, gereksiz sansasyon ve kaynak dışı kesinlik yapma.
- Eğer konuya yetecek kanıt yoksa kısaca bunu belirt, olay uydurma.
- Herhangi bir URL'yi kendiliğinden kaynak olarak uydurma.
'''
    raw = chat(model, [
        {'role': 'system', 'content': 'Görevin kullanıcı konusundan sapmadan kaynak sınırları içinde içerik üretmek. JSON dışında çıktı verme.'},
        {'role': 'user', 'content': prompt},
    ], max_tokens=max(1300, min(4300, int(word_target * 3.0))), temperature=0.2)
    result = parse_json_output(raw)
    ok, detail = focus_check(result['narration'], subject, alias)
    result['focus_ok'] = ok
    result['focus_detail'] = detail
    return result


async def synthesize(text, voice, rate):
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'voice.mp3'
        await edge_tts.Communicate(text, voice=voice, rate=rate).save(str(path))
        return path.read_bytes()


st.set_page_config(page_title='GURKAN AI Content Studio v0.6', page_icon='🎙️', layout='wide')
st.title('GURKAN AI Content Studio v0.6')
st.caption('Konu kilidi • Kaynağa bağlı taslak • Ayrı sahne notları • Manuel onaylı MP3')
for key, default in [('draft', None), ('approved', False), ('mp3', None), ('last_subject', '')]:
    if key not in st.session_state:
        st.session_state[key] = default

with st.form('generation'):
    subject = st.text_input('Kesin konu (örn. Mekke’deki Kâbe yapısının tarihi)', value='Mekke’deki Kâbe yapısının tarihi')
    scope = st.text_input('Konu tanımı ve sınırı', value='Mekke’de bulunan kutsal yapı; kaba kelimesi, bıçak veya kılıç hakkında değildir.')
    alias = st.text_input('Alternatif ad / yazılış (opsiyonel)', value='Kâbe')
    a, b, c = st.columns(3)
    lang = a.selectbox('Dil', ['Türkçe', 'İngilizce'])
    minutes = b.select_slider('Hedef süre (dakika)', options=[1, 2, 3, 5, 8, 10], value=2)
    mode = c.selectbox('İçerik güvenliği', ['Kaynağa bağlı (olgusal)', 'Yaratıcı taslak (kontrol gerekir)'])
    model = st.text_input('LM Studio model kimliği', value=DEFAULT_MODEL)
    source = st.text_area('Kaynak metni / doğrulanmış notlar (URL değil, alıntıladığın gerçek içerik)', height=170)
    files = st.file_uploader('İsteğe bağlı: kendi .md veya .txt kaynak notlarını ekle', type=['md', 'txt'], accept_multiple_files=True)
    generate = st.form_submit_button('Taslak oluştur ve konuyu kontrol et', type='primary')

if generate:
    extra = []
    for f in files or []:
        raw = f.getvalue()
        if len(raw) > 150000:
            st.warning(f'{f.name} 150 KB sınırını geçti, kullanılmadı.')
            continue
        extra.append(f'\nKaynak dosyası: {f.name}\n' + raw.decode('utf-8-sig', errors='replace'))
    combined = source + '\n'.join(extra)
    try:
        with st.spinner('Yerel model senaryo hazırlıyor ve yapılandırılmış alanlar üretiyor...'):
            result = create_script(subject.strip(), scope.strip(), alias.strip(), combined, lang, minutes, model.strip(), mode)
        st.session_state.pop('narration_editor', None)
        st.session_state.draft = result
        st.session_state.last_subject = subject
        st.session_state.approved = False
        st.session_state.mp3 = None
    except Exception as exc:
        st.error(f'Üretim başarısız: {exc}')

if st.session_state.draft:
    result = st.session_state.draft
    st.divider()
    if result['focus_ok']:
        st.success('Yüzeysel konu anahtar sözcüğü kontrolü geçti. Bu, gerçek konu sadakati veya doğruluk garantisi değildir.')
    else:
        st.error(result['focus_detail'])
        st.info('Konuyu/tanımı daha açık yazıp kaynağı ekleyerek yeniden oluştur. Bu taslak için seslendirme kapalı.')

    edited = st.text_area('Yalnızca spikerin söyleyeceği metin (düzenlenebilir)', value=result['narration'], height=280, key='narration_editor')
    words = len(narration_only(edited).split())
    st.caption(f'Konuşma kelimesi: {words} • Yaklaşık {words / 125:.1f} dakika (TR varsayımı; gerçek süre farklı olabilir).')
    x, y = st.columns(2)
    with x:
        st.subheader('Sahne / müzik yönergeleri (seslendirilmez)')
        st.text_area('Sahne notları', value='\n'.join(map(str, result['scene_notes'])), height=180)
    with y:
        st.subheader('Doğrulanacak iddialar')
        st.text_area('Modelin tespit ettiği iddialar (otomatik olgu doğrulaması değildir)', value='\n'.join(map(str, result['claims_to_verify'])), height=180)
    if st.button('Metni yeniden konu kontrolünden geçir'):
        result['focus_ok'], result['focus_detail'] = focus_check(edited, st.session_state.last_subject, alias)
        st.session_state.approved = False
        st.rerun()
    st.download_button('Konuşma metnini indir (.md)', data=edited, file_name='gurkan_ai_konusma_metni.md', mime='text/markdown')
    st.download_button('Üretim raporunu indir (.json)', data=json.dumps({**result, 'edited_narration': edited, 'topic': st.session_state.last_subject}, ensure_ascii=False, indent=2), file_name='gurkan_ai_kontrol_raporu.json', mime='application/json')
    st.warning('Kaynak URL’leri program tarafından ziyaret edilmez. Kaynakların doğruluğunu ve iddiaları bizzat kontrol edin.')
    st.session_state.approved = st.checkbox('Metni ve iddiaları inceledim; bu metnin seslendirilmesini onaylıyorum.', value=st.session_state.approved, disabled=not result['focus_ok'])
    left, right = st.columns(2)
    voice = left.selectbox('Ses', list(VOICES.keys()))
    rate = right.select_slider('Ses hızı', options=['-15%', '-5%', '+0%', '+5%', '+15%'], value='+0%')
    st.caption('Edge TTS çevrimiçi çalışır. Gizli müşteri verileriyle kullanmayın.')
    if st.button('Onaylı MP3 oluştur', disabled=not (st.session_state.approved and result['focus_ok'])):
        safe_text = narration_only(edited)
        if not safe_text or len(safe_text) < 30:
            st.error('Seslendirilecek konuşma metni çok kısa/boş.')
        elif not focus_check(safe_text, st.session_state.last_subject, alias)[0]:
            st.error('Düzenleme sonrası konu kilidi başarısız oldu.')
        else:
            try:
                with st.spinner('Seslendirme oluşturuluyor...'):
                    audio_bytes = asyncio.run(synthesize(safe_text, VOICES[voice], rate))
                st.session_state.mp3 = audio_bytes
                st.success('MP3 hazır.')
            except Exception as exc:
                st.error(f'Seslendirme hatası: {exc}')
    if st.session_state.mp3:
        st.audio(st.session_state.mp3, format='audio/mp3')
        st.download_button('MP3 indir', data=st.session_state.mp3, file_name='gurkan_ai_seslendirme.mp3', mime='audio/mpeg')
