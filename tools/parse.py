import re, json, hashlib, pymupdf, os
HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(HERE, 'src', 'ustav_en.pdf')
sha = hashlib.sha256(open(PDF,'rb').read()).hexdigest()
d = pymupdf.open(PDF)
lines = []
for p in d:
    lines += p.get_text().replace('\xa0',' ').split('\n') + ['\x00']
ROM = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII']
paras = []; cur = []; pend_break = False
def flush():
    global cur
    if cur: paras.append(' '.join(cur)); cur = []
for raw in lines:
    l = raw.strip()
    if l == '\x00':
        pend_break = True; continue
    if not l:
        flush(); continue
    startnew = bool(re.match(r'^(\d+\.\s|[a-z]\)\s|\([a-z]\)\s)', l)) or l.startswith(('Article ','Annex '))
    if pend_break:
        pend_break = False
        # continued paragraph if we have an open paragraph, or the page break followed a blank and new text is lowercase
        if not cur and paras and l[:1].islower() and not startnew and not re.search(r'[.:;]$', paras[-1]):
            cur = [paras.pop()]
    if startnew: flush()
    cur.append(l)
    # a short numbered heading closes itself
    if re.match(r'^\d+\.\s+[A-Z][^.:;]{0,45}$', l) or re.match(r'^(Article|Annex) [IVX]+:\s*$', l):
        flush()
flush()
paras = [re.sub(r'\s+', ' ', p).strip() for p in paras]
paras = [p for p in paras if p]
# preamble..: first para "CONSTITUTION OF ..." ; then PREAMBLE
units = {}; order = []
cur = None
def add(key, label, kind):
    global cur
    cur = key; units[key] = {'label': label, 'kind': kind, 'lines': []}; order.append(key)
add('preamble', 'Preamble', 'preamble')
i = 0
TITLES = {}
stop = False
for p in paras:
    if p.startswith('CONSTITUTION OF') or p == 'PREAMBLE': continue
    if p.startswith('Declaration On Behalf'): break
    m = re.match(r'^Article ([IVX]+):$', p)
    if m:
        n = ROM.index(m.group(1)) + 1
        add('art-%02d' % n, 'Article %s' % m.group(1), 'art'); units[cur]['title_pending'] = True; continue
    m = re.match(r'^Annex ([IVX]+):$', p)
    if m:
        add('annex-%s' % m.group(1).lower(), 'Annex %s' % m.group(1), 'schedule'); units[cur]['title_pending'] = True; continue
    if units[cur].pop('title_pending', False):
        units[cur]['title'] = p; continue
    units[cur]['lines'].append(p)
out = {}
for k in order:
    u = units[k]
    h = '# ' + u['label'] + (': ' + u['title'] if u.get('title') else '')
    out[k] = {'label': u['label'], 'kind': u['kind'], 'text': h + '\n' + '\n'.join(u['lines']) + '\n'}
assert [k for k in out if k.startswith('art-')] == ['art-%02d' % n for n in range(1, 13)]
assert 'annex-i' in out and 'annex-ii' in out
for k in ('art-01','art-12','annex-ii'): print(out[k]['text'][:1500]); print('---')
URL = 'https://www.ustavnisud.ba/public/down/USTAV_BOSNE_I_HERCEGOVINE_engl.pdf'
corpus = {
 'country': {'code':'BA','name':'Bosnia and Herzegovina','slug':'bosnia-and-herzegovina','lang':'en','tz':'Europe/Sarajevo','future_branch':'future',
   'publisher': {'name':'Constitutional Court of Bosnia and Herzegovina','email':'info@ustavnisud.ba.invalid'},
   'default_in_force_rule': {'text':'Constitution Article XII(1): it enters into force upon signature of the General Framework Agreement (Paris, 14 December 1995)','source':URL},
   'licence_note':'English text of the Constitution of Bosnia and Herzegovina (Annex 4 to the General Framework Agreement for Peace) as published by the Constitutional Court of Bosnia and Herzegovina, www.ustavnisud.ba.'},
 'sources':[{'name':'Constitutional Court of Bosnia and Herzegovina, Constitution (English)','url':URL,'retrieved':'2026-10-29','requests':1,'licence':'Official public text; no licence statement found','notes':'15-page text-layer PDF created February 2006. It does not include Amendment I (2009).'}],
 'laws': {'gfap-annex-4': {'label':'GFAP Annex 4','title':'General Framework Agreement for Peace in Bosnia and Herzegovina, Annex 4 (Constitution of Bosnia and Herzegovina)','kind':'treaty','enacted':'1995-12-14','published':'1995-12-14','url':URL,'temporary_until':None,'restores':None,'note':None}},
 'acts':[{'slug':'constitution','short':'Const.','title':'Constitution of Bosnia and Herzegovina','url':URL,'first_law':'gfap-annex-4','earlier_laws':[],
   'versions':[{'from':'1995-12-14','source_url':URL,'sha256':sha,'units':out,'credits':{},'note':'The Constitution as signed in Paris on 14 December 1995, from the Constitutional Court\'s English PDF of 2006. Amendment I (2009, Brcko District) is not in this text.'}]}],
 'applies':[],
 'decisions':['The source is a 2006 English PDF from the Constitutional Court, so the repository holds one version, the Constitution as signed on 14 December 1995 (Article XII(1): in force on signature). Amendment I of 26 March 2009 is not in it and is not in the record.',
   'One file per Article and per Annex; the numbered sections stay as lines inside each file. The three declarations at the end (signatures) are not units.'],
 'ai_use':['none']}
json.dump(corpus, open(os.path.join(HERE,'corpus.json'),'w',encoding='utf-8'), ensure_ascii=False, indent=1)
