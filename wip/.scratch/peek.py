import re, html, sys, subprocess
sys.path.insert(0, r'C:/Users/alany/Documents/lexifina/scripts/bosnia-and-herzegovina-law')
import fetch
url, start, n, pat = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
t = fetch.fetch(url).decode('utf8', 'replace')
links = []
for m in re.finditer(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', t, re.S):
    txt = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', m.group(2)))).strip()
    links.append((m.group(1), txt))
b = re.sub(r'<script.*?</script>|<style.*?</style>', '', t, flags=re.S)
b = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', b)))
print(b[start:start + n])
seen = set()
for h, x in links:
    if re.search(pat, h + ' ' + x, re.I) and (h, x) not in seen:
        seen.add((h, x)); print(h, '|', x[:120])
