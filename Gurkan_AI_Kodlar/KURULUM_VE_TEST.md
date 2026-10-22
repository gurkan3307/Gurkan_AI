# GURKAN AI Content Studio v0.7 — Kurulum ve test

1. Eski v0.6 ve v0.5 dosyalarını silme. Bu ZIP içindeki üç dosyayı `D:\GURKANUS27 Yapay Zeka\GURKAN_AI` konumuna çıkar.
2. LM Studio'da qwen/qwen3-8b modelini ve 1234 numaralı yerel sunucuyu aç.
3. CMD'de:
   ```cmd
   cd /d "D:\GURKANUS27 Yapay Zeka\GURKAN_AI"
   venv\Scripts\activate
   python -m streamlit run gurkan_ai_content_studio_v0_7.py --server.port 8506
   ```
4. Tarayıcıda http://localhost:8506 adresini aç. 8505 portundaki v0.6'yı kapatmak zorunda değilsin.
5. Test: Konu "Mekke'deki Kâbe'nin onarımları", dışlanan sözcükler "kılıç, bıçak". Kaynağa bağlı modu seç, kendi kontrol ettiğin >=80 karakter kaynağı koy ve üret.
6. Kaynağın aynen geçtiği alıntıları ve üretilen tarihleri tek tek kontrol et. Üç onayı işaretlemeden seslendirme devreye girmez.
7. Konuşma, sahne notları, kontrol raporu ve kaynak özeti ZIP olarak indirilebilir. Bu rapor, otomatik tarihsel doğrulama DEĞİLDİR.

## Obsidian notları

Ön izleme (not yazmaz):
```cmd
python gurkan_ai_v07_not_aktar.py --vault "D:\GURKANUS27 Yapay Zeka\GURKAN_AI_Bilgi_Bankasi"
```
Uygunsa:
```cmd
python gurkan_ai_v07_not_aktar.py --vault "D:\GURKANUS27 Yapay Zeka\GURKAN_AI_Bilgi_Bankasi" --apply
```
Ardından asistanın kendi terminalinde `/bilgi-durum` ve `/indeksle` (LM Studio embedding modeli açıkken).

## Dikkat

- Yeni bilgiler için onay, yayın izni veya gerçek olgu doğrulama anlamına gelmez.
- Kaynak metnindeki talimatlar güvenilmez içeriktir.
- Seslendirmede Edge TTS çevrimiçi servis kullanır; özel veri paylaşma.
- Bu sürüm statik sözdizimi ve aktarım denemelerinden geçti, gerçek Windows/LM Studio testi henüz yapılmadı.
