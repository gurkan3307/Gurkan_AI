# GURKAN AI v3.0 — Arayüz geliştirme sürümü

## Marka durumu
Ön web taramasında “GURKAN AI” için belirgin bir doğrudan eşleşme tespit edilmedi. **Bu, ismin tescile uygun olduğu veya ticari olarak güvenle kullanılabileceği anlamına gelmez.** TÜRKPATENT marka sicilinde GURKAN AI, GURKAN, GÜRKAN, GURKANAI ve benzer adları, özellikle yazılım (sınıf 9) ve teknoloji/yazılım hizmetleri (sınıf 42) açısından araştırın; ürünün kapsamına göre başka sınıflar da değerlendirilebilir. Uluslararası pazarlama öncesinde EUIPO/TMview ve ilgili pazarların sicilleri de kontrol edilmelidir.

TÜRKPATENT: https://www.turkpatent.gov.tr/research
EUIPO: https://www.euipo.europa.eu/en/search-ip

## Kurulum
1. ZIP içindeki `gurkan_ai_v3_0_arayuz.py` dosyasını **mevcut** `D:\GURKANUS27 Yapay Zeka\JARVIS` klasörüne kopyalayın.
2. `jarvis_v2_9_6_kaynakli_rag.py` dosyasını **yeniden adlandırmayın veya silmeyin**. Arayüz bu modülü çağırır.
3. CMD komutları:

```cmd
cd /d "D:\GURKANUS27 Yapay Zeka\JARVIS"
venv\Scripts\activate
python -m pip install PySide6 psutil
python gurkan_ai_v3_0_arayuz.py
```

4. Sohbet yanıtları için LM Studio yerel sunucusunun ve Qwen3-8B modelinin açık olduğundan emin olun. `/sor` gibi RAG sorguları için Nomic embedding modeli de gerekebilir.
5. F8 ses açık/kapalı geçişini, `/gor-5` sessiz ekran özetini, `/sor` ve `/ara` komutlarını tek tek test edin.

## Korunanlar
- `jarvis_memory.db`, `jarvis_vectors.db`, `Jarvis_Beyin` ve mevcut 128 not aynen kalır.
- Kodda **iç modül adı** `jarvis_v2_9_6_kaynakli_rag.py` olarak kalır: bu, geriye uyumluluk içindir.
- Yeni marka yalnızca arayüzün görünen metinlerinde değiştirilmiştir. Eski veritabanındaki sohbet kayıtlarında “JARVIS” geçebilir; bu kayıtlar otomatik değiştirilmez.
- Gerçek Windows/PySide6 açılış testi henüz kullanıcı bilgisayarında yapılmalıdır. Sözdizimi denetimi geçmiştir.
