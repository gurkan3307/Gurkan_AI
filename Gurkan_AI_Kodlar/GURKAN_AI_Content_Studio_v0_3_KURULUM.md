# GURKAN AI Content Studio v0.3 — Kurulum

Bu sürüm, önceki `gurkan_ai_content_studio_0_2.py` dosyasını değiştirmez.

1. `gurkan_ai_content_studio_0_3.py` dosyasını `D:\GURKANUS27 Yapay Zeka\GURKAN_AI` içine koy.
2. LM Studio'da Qwen3-8B modelini ve Developer / Local Server servisini çalıştır (OpenAI-compatible API: `http://127.0.0.1:1234/v1`).
3. CMD'de:

```cmd
cd /d "D:\GURKANUS27 Yapay Zeka\GURKAN_AI"
venv\Scripts\activate
python gurkan_ai_content_studio_0_3.py
```

4. Dil `Türkçe`, içerik `YouTube senaryosu`, süre `5 dk` ve konu `Küçük işletmeler yapay zekâ ile nasıl zaman kazanabilir?` seç. **Taslak Oluştur**'a bas.
5. Taslağı incele. Kelime/süre tahmini yalnızca yaklaşık değerdir. **Kontrol Listesini Hazırla** düğmesine bas, `Doğrulama / Yayın Kontrolü` sekmesini incele.
6. **Dosyaları Kaydet...** deyip `GURKAN_AI\YouTube İçerik Taslakları` klasörünü seç. İki Markdown dosyası oluşturulur. Aynı isimli dosyanın üzerine yazmaz.

## Kısıtlar

- LM Studio'nun yerel modeli yanıt üretir. Kod internette araştırma yapmaz, olguları otomatik doğrulamaz, yayın yapmaz, video/müzik üretmez.
- Sözcük sayısına ilişkin süre tahmini başlık ve sahne yönergelerini de sayabilir.
- Windows arayüzü ve gerçek LM Studio çağrıları kullanıcı bilgisayarında denenmelidir.
- Müşteri verileri, özel belgeler ve gizli API anahtarlarını kaynak alanına izinsiz yapıştırma.
- Hata alırsan önce model kimliğini, `Developer → Local Server` durumunu ve terminal çıktısını kontrol et.
