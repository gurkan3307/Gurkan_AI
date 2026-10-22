from pathlib import Path

p = Path('kaynak_cek.py')
s = p.read_text(encoding='utf-8')

YENI = r'''def izinli(url):
    p = urlparse(url)
    taban = f'{p.scheme}://{p.netloc}'
    if taban not in _robots:
        rp = RobotFileParser()
        rp.set_url(taban + '/robots.txt')
        try:
            r = requests.get(taban + '/robots.txt', headers={'User-Agent': UA}, timeout=20)
            if r.status_code == 200:
                rp.parse(r.text.splitlines())
            elif r.status_code in (401, 403):
                rp.disallow_all = True
            else:
                rp.allow_all = True
        except Exception:
            rp = None
        _robots[taban] = rp
    rp = _robots[taban]
    return True if rp is None else rp.can_fetch(UA, url)


'''

a = s.find('def izinli(url):')
b = s.find('def cek(url):')
if 'rp.parse(r.text' in s:
    print('Zaten yamali.')
elif a < 0 or b < a:
    print('izinli fonksiyonu bulunamadi, dosyaya dokunulmadi.')
else:
    yeni = s[:a] + YENI + s[b:]
    try:
        compile(yeni, 'kaynak_cek.py', 'exec')
    except SyntaxError as e:
        print('Derleme hatasi, dosyaya dokunulmadi:', e)
    else:
        p.with_suffix('.yedek').write_text(s, encoding='utf-8')
        p.write_text(yeni, encoding='utf-8')
        print('Yama uygulandi. Yedek: kaynak_cek.yedek')