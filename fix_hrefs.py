import os, re
d = r'C:\Kuliah\UIUX_copy\Frontend'
for r, dirs, f in os.walk(d):
    for file in f:
        if file.endswith('.html') or file.endswith('.js'):
            p = os.path.join(r, file)
            with open(p, 'r', encoding='utf-8') as fh: c = fh.read()
            c = re.sub(r'location\.href\s*=\s*([\'"`])/(.*?)\1', r'location.href = \1\2\1', c)
            c = re.sub(r'href\s*=\s*([\'"`])/(.*?)\1', r'href=\1\2\1', c)
            with open(p, 'w', encoding='utf-8') as fh: fh.write(c)
print("Done fixing hrefs")
