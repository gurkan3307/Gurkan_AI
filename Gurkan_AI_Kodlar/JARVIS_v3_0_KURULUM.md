# JARVIS v3.0 — İlk masaüstü arayüzü

## Ne işe yarar?
Bu, **gerçek PySide6 masaüstü programı** için ilk deneme sürümüdür. Animasyonlu çekirdek QPainter ile çizilir. Mevcut `jarvis_v2_9_6_kaynakli_rag.py` motoruna bağlanır; onu ve veritabanlarını değiştirmez.

## Kurulum — Windows CMD
1. `jarvis_v3_0_arayuz.py` dosyasını mevcut `JARVIS` klasörüne yerleştir. `jarvis_v2_9_6_kaynakli_rag.py` aynı klasörde bulunmalı.
2. CMD aç, aşağıdaki satırları sırayla çalıştır:

```cmd
cd /d "D:\GURKANUS27 Yapay Zeka\JARVIS"
venv\Scripts\activate
python -m pip install PySide6 psutil
python jarvis_v3_0_arayuz.py
```

3. LM Studio'da yerel sunucunun `http://127.0.0.1:1234/v1` adresinde açık olduğundan ve Qwen3-8B modelinin hazır olduğundan emin ol. `/sor` yanıtları için de yerel model gerekir.

## Test sırası
1. Pencere açılıyor mu ve mavi JARVIS çekirdeği **hareket ediyor mu**?
2. Bilgi durumu kartında **128 not** yazıyor mu? (Mevcut JARVIS Obsidian kasan gerçek zamanlı okunur.)
3. Normal sohbetten `Merhaba` yaz; yanıt yazılı gelsin, **konuşmasın**.
4. F8 ile sesi aç, sonra tekrar kapat. **GUI'de F8 uygulama odaktayken çalışır.**
5. `/sor PySide6 QMainWindow nasıl kullanılır?` yaz; ilgili notları kaynak olarak göstermeli.
6. `Ekranı Oku` düğmesine bas; pencere küçülür. 5 saniyede hedef pencereye geç. Sonuç **sessiz** görüntülenir.

## Güvenlik ve kapsam
- Yerel mod varsayılandır. Google seçildiğinde normal sohbet buluta aktarılabilir, ücretlendirme oluşabilir.
- Obsidian not taslağı kaydı `/onayla` olmadan yapılmaz; mevcut dosyaların üzerine yazılmaz.
- Ekran okuyucu mevcut v2.9.6'daki yerel OCR yöntemini kullanır. Ekran görüntüsünü varsayılan olarak Google'a göndermez.
- Mikrofon düğmesi şimdilik **tek turluk** sesli sohbet içindir; sürekli dinleme bir sonraki sürümün konusu.
- Bu arayüz ilk sürümdür; tam çizimle eşleşen bütün menüler ve gerçek zamanlı akış henüz tamamlanmadı.
- Ses çıktısı yazılı modda varsayılan olarak kapalıdır; arayüzden F8 ile açılabilir.
- `/indeksle` uzun sürebilir. Çalışırken programı kapatmak yerine bitmesini bekle.

## Sorun giderme
`ModuleNotFoundError: No module named 'PySide6'` çıkarsa `venv` etkin mi kontrol et ve `python -m pip install PySide6` çalıştır.

`jarvis_v2_9_6_kaynakli_rag.py bulunamadı` hatası çıkarsa iki Python dosyasını aynı JARVIS klasörüne yerleştir.

Yerel model yanıt vermiyorsa LM Studio sunucusunu, model adını ve port `1234`'ü kontrol et.

Sesli özelliğin yanlış telaffuz etmesi durumunda kullandığın TTS motorunu ayrıca test etmek gerekir.

**Önemli:** Bu Python kodunun sözdizimi test edildi; bu çalışma ortamında PySide6 kurulumu mümkün olmadığı için grafik arayüzün Windows üzerinde çalışma testi henüz yapılamadı.
