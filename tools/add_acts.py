"""Bosnia and Herzegovina: add the Criminal Code (English, Prosecutor's Office of BiH unofficial consolidated text, OG up to 47/14).
Reads only .cache2/cc.pdf via pdftotext -layout (written to .cache2/cc.txt). Leaves the constitution untouched.
Usage: python -X utf8 add_acts.py"""
import hashlib, json, re, subprocess
from pathlib import Path
H = Path(__file__).parent
PDF = H / '.cache2/cc.pdf'
URL = 'https://www.tuzilastvobih.gov.ba/files/docs/zakoni/Criminal_Code_of_BH_-_Consolidated_text_47_14.pdf'
raw = PDF.read_bytes()
txt = subprocess.run(['pdftotext', '-enc', 'UTF-8', '-layout', str(PDF), '-'], capture_output=True, check=True).stdout.decode('utf8')
L = []
for l in txt.replace('\f', '\n').split('\n'):
    l = l.strip().replace('\xa0', ' ')
    l = re.sub(r'\s+', ' ', l)
    if not l:
        continue
    L.append(l)
# footnote 1 block: from "1High Representative" to the next lone page number
i = next(k for k, l in enumerate(L) if l.startswith('1High Representative'))
j = next(k for k in range(i, len(L)) if re.fullmatch(r'\d{1,3}', L[k]))
del L[i:j + 1]
L = [l for l in L if not re.fullmatch(r'\d*B\d*|F|\d{1,3}|[A-Z]\d*B|B\d+', l)]
def norm(s):
    s = s.replace('“', '"').replace('”', '"').replace('’', "'").replace('‘', "'").replace('–', '-').replace('—', '-')
    return s
L = [norm(l) for l in L]
mk = [k for k, l in enumerate(L) if re.fullmatch(r'Article \d+[a-z]?\.?', l)]
CH = re.compile(r'^(GENERAL PART|SPECIAL PART|[IVXL]+ C ?H ?A ?P ?T ?E ?R\b.*)$')
units, order = {}, []
def key_of(num):
    m = re.fullmatch(r'(\d+)([a-z]?)', num)
    return 'art-%03d' % int(m.group(1)) + ('-' + m.group(2) if m.group(2) else '')
def paras(lines):
    out = []
    for l in lines:
        if re.match(r'^(\(\d+\)|[a-z]\)|\d+\)|\(\w\))\s', l) or not out:
            out.append(l)
        else:
            out[-1] += ' ' + l
    return out
divn = 0
pending_title = None
def add_div(lines):
    global divn
    lines = [l for l in lines if l]
    if not lines:
        return
    divn += 1
    k = 'div-%03d' % divn
    label = ' '.join(lines)
    units[k] = {'label': label, 'kind': 'part', 'text': '# ' + label + '\n'}
    order.append(k)
# segment before the first article: only headings
first = mk[0]
head = L[L.index('GENERAL PART') if 'GENERAL PART' in L else 0:first]
pre = L[:first]
for idx, m in enumerate(mk):
    end = mk[idx + 1] if idx + 1 < len(mk) else len(L)
    seg = L[m + 1:end]
    # trailing title (and chapter headings) belong to the next article
    if idx + 1 < len(mk):
        title = seg.pop()
        # chapter heading block: from the last chapter line (and part lines before) to the end
        cut = None
        for q in range(len(seg)):
            if CH.match(seg[q]):
                cut = q
                break
        next_div = []
        if cut is not None:
            # include a directly preceding GENERAL/SPECIAL PART line already matched by CH
            next_div = seg[cut:]
            seg = seg[:cut]
    else:
        title, next_div = None, []
    num = L[m].split()[1].rstrip('.')
    cur_title = pending_title
    pending_title = title
    if idx == 0:
        # title directly before Article 1 is the chapter title; headings before it form the first division
        add_div(pre[pre.index('GENERAL PART'):])
    label = 'Article %s. %s' % (num, cur_title) if cur_title else 'Article %s' % num
    k = key_of(num)
    assert k not in units, k
    units[k] = {'label': label, 'kind': 'art', 'text': '\n'.join(['# ' + label] + paras(seg)) + '\n'}
    order.append(k)
    if next_div:
        add_div(next_div)
out = {k: units[k] for k in order}
print(len(out), 'units', sum(1 for u in out.values() if u['kind'] == 'art'), 'articles')
corpus = json.loads((H / 'corpus.json').read_text(encoding='utf-8'))
slug = 'criminal-code'
if any(a['slug'] == slug for a in corpus['acts']):
    corpus['acts'] = [a for a in corpus['acts'] if a['slug'] != slug]
corpus['laws']['cc-2003'] = {'label': 'Criminal Code of BiH (2003)', 'title': 'Criminal Code of Bosnia and Herzegovina, adopted 18 and 27 June 2003 and imposed by the High Representative', 'kind': 'law', 'enacted': '2003-06-27', 'published': '2003-03-01' if False else None, 'url': URL, 'temporary_until': None, 'restores': None, 'note': None}
corpus['laws']['tuzilastvo-oldest'] = {'label': "Prosecutor's Office of BiH (consolidated text)", 'title': "Criminal Code of Bosnia and Herzegovina, unofficial consolidated text of the Prosecutor's Office, oldest version available", 'kind': 'publisher', 'enacted': '2017-05-04', 'published': '2017-05-04', 'url': URL, 'temporary_until': None, 'restores': None, 'note': None}
corpus['acts'].append({'slug': slug, 'short': 'CC BiH', 'title': 'Criminal Code of Bosnia and Herzegovina', 'url': URL, 'first_law': None, 'earlier_laws': ['cc-2003'],
  'publisher': {'name': "Prosecutor's Office of Bosnia and Herzegovina", 'email': 'tuzilastvo@tuzilastvobih.gov.ba.invalid'},
  'versions': [{'from': '2017-05-04', 'source_url': URL, 'sha256': hashlib.sha256(raw).hexdigest(), 'units': out, 'credits': {k: ['tuzilastvo-oldest'] for k in out},
    'note': "Unofficial consolidated English text with the amendments published in the Official Gazette of BiH up to 47/14, as posted by the Prosecutor's Office of BiH (file last modified 4 May 2017). Later amendments are not in it. Footnotes and amendment mark-up are not kept; the printed text prevails in the local languages."}]})
src = {'name': "Prosecutor's Office of Bosnia and Herzegovina, Criminal Code (unofficial consolidated English text)", 'url': URL, 'retrieved': '2026-10-30', 'requests': 1,
       'licence': 'Official public text; no licence statement found', 'notes': "PDF text layer read with pdftotext. Marked by the publisher as an unofficial consolidated version (OG BiH 3/03 to 47/14). robots.txt does not disallow /files/."}
if not any(s['name'] == src['name'] for s in corpus['sources']):
    corpus['sources'].append(src)
corpus['decisions'] += ["Criminal Code: one version, dated 2017-05-04 (the Last-Modified date of the file on the Prosecutor's Office site), credited to the publisher as 'oldest version available'; the code was adopted in 2003 and in force from 1 March 2003. The text is unofficial and consolidated only to OG 47/14.",
  'Criminal Code: page numbers, typesetting artefacts and the footnote on amendments were removed; wrapped lines were joined into numbered paragraphs.',
  'Not added: a civil code and a commercial code. Civil and commercial law is made by the two entities (Federation of BiH, Republika Srpska) and the Brcko District, not by the state, so there is no state-level code to record.']
corpus['decisions'] = list(dict.fromkeys(corpus['decisions']))
(H / 'corpus.json').write_text(json.dumps(corpus, ensure_ascii=False, indent=1), encoding='utf-8')
