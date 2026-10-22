# GURKAN AI bağlantı uygulama aracı

Bu araç temizlenmiş CSV'den bağlantı önerilerini seçer. İlk çalıştırma sadece önizleme yapar. Orijinal vault'a yazmak için ayrıca `--apply` gerekir.

## Önce gerekli dosya
Temizlenmiş CSV'yi indir:
`GURKAN_AI_Baglanti_Onizleme_Temizlenmis_Adaylar.csv`

CSV'yi örneğin `D:\GURKANUS27 Yapay Zeka\` klasörüne kaydet. Bu paketteki `gurkan_ai_baglantilari_uygula.py` dosyasını `D:\GURKANUS27 Yapay Zeka\GURKAN_AI\` içine kopyala.

## 1) Önizleme (değişiklik yapmaz)
CMD:
```cmd
cd /d "D:\GURKANUS27 Yapay Zeka\GURKAN_AI"
python gurkan_ai_baglantilari_uygula.py --vault "D:\GURKANUS27 Yapay Zeka\GURKAN_AI_Bilgi_Bankasi" --csv "D:\GURKANUS27 Yapay Zeka\GURKAN_AI_Baglanti_Onizleme_Temizlenmis_Adaylar.csv"
```
Bu araç yalnızca aynı klasör/konu içindeki önerileri, puanı en az 0.50 olanları ve not başına en fazla 2 bağlantıyı seçer. Önizleme CSV'si vault'un bir üst klasörüne yazılır. Vault notları değişmez.

## 2) Yalnızca önizlemeyi kabul edersen uygula
Aynı komutu `--apply` ile çalıştır:
```cmd
python gurkan_ai_baglantilari_uygula.py --vault "D:\GURKANUS27 Yapay Zeka\GURKAN_AI_Bilgi_Bankasi" --csv "D:\GURKANUS27 Yapay Zeka\GURKAN_AI_Baglanti_Onizleme_Temizlenmis_Adaylar.csv" --apply
```
Araç, değişiklikten önce yalnızca değişecek notların yedeğini `D:\GURKANUS27 Yapay Zeka\` altında `GURKAN_AI_Baglanti_Yedek_...` klasörüne koyar. Notların sonuna işaretli `İlgili notlar (otomatik öneri)` bölümü ekler. Var olan aynı araç bölümü varsa günceller. Diğer not içeriğine dokunmaz.

## Dikkat
- Bu, anlamsal olarak kesin doğrulanmış bir ağ değildir; metin benzerliğine dayalı adaylar ekler.
- İlk önce önizleme komutunu çalıştırıp sonucunu paylaş.
- Bu araç bilgi içeriğini veya kaynak doğruluğunu değiştirmez.
