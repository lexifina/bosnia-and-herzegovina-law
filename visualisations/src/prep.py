"""Compute every number for the 20 charts into <build>/data.json.

    python prep.py <build-dir>

Reads what make.py extracted into <build>: cc.tsv, acts.json, sg.tsv, bills.json, sud.json, texts.json and repo/.
Every rule that reads a category out of a title or a text is in this file; each rule that classifies leaves a
visible "other" rather than guessing.
"""
import collections, csv, json, os, re, statistics, sys
from datetime import date

B = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '.build')
R = os.path.join(B, 'repo')
OUT, PROFILE = {}, {}
D = lambda s: date.fromisoformat(s[:10])
csv.field_size_limit(10 ** 8)

# ------------------------------------------------------------------ text helpers
_CYR = dict(zip('АБВГДЂЕЖЗИЈКЛЉМНЊОПРСТЋУФХЦЧЏШабвгдђежзијклљмнњопрстћуфхцчџш',
                ['A', 'B', 'V', 'G', 'D', 'Đ', 'E', 'Ž', 'Z', 'I', 'J', 'K', 'L', 'LJ', 'M', 'N', 'NJ', 'O', 'P', 'R', 'S', 'T', 'Ć', 'U', 'F', 'H', 'C', 'Č', 'DŽ', 'Š',
                 'a', 'b', 'v', 'g', 'd', 'đ', 'e', 'ž', 'z', 'i', 'j', 'k', 'l', 'lj', 'm', 'n', 'nj', 'o', 'p', 'r', 's', 't', 'ć', 'u', 'f', 'h', 'c', 'č', 'dž', 'š']))
_HOMO = {'А': 'A', 'В': 'B', 'Е': 'E', 'К': 'K', 'М': 'M', 'Н': 'H', 'О': 'O', 'Р': 'P', 'С': 'C', 'Т': 'T', 'Х': 'X', 'Ј': 'J',
         'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'х': 'x', 'ј': 'j', 'у': 'y', 'і': 'i', 'І': 'I', 'ѕ': 's'}


def lat(s):
    """Latin script: a Cyrillic word is transliterated; Cyrillic look-alike letters inside a Latin word become the Latin letter."""
    out = []
    for w in re.split(r'(\s+)', s or ''):
        if re.search('[Ѐ-ӿ]', w):
            mixed = re.search('[A-Za-zČĆŽŠĐčćžšđ]', w)
            w = ''.join((_HOMO.get(ch) if mixed and ch in _HOMO else _CYR.get(ch, ch)) for ch in w)
        out.append(w)
    return ''.join(out)


def U(s):
    t = re.sub(r'\s+', ' ', lat(s)).strip().upper()
    # some 1998-2013 titles use an old Serbian Latin encoding: W for NJ and X for DŽ ("DONOŠEWU", "BUXETA")
    return re.sub(r'(?<=[AEIOU])X(?=[AEIOU])', 'DŽ', re.sub(r'(?<=[AEIOUŠ])W(?=[AEIOU])', 'NJ', t))


def label_ok(lbl):
    m = re.match(r'^(\d+)/(\d{2})$', lbl or '')
    return (int(m.group(1)), 2000 + int(m.group(2)) if int(m.group(2)) < 90 else 1900 + int(m.group(2))) if m else None


def dmy(s):
    m = re.match(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', s or '')
    return date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat() if m else None


# ------------------------------------------------------------------ the Gazette index and the acts held as text
SG = list(csv.DictReader(open(os.path.join(B, 'sg.tsv'), encoding='utf-8'), delimiter='\t'))
for r in SG:
    r['T'] = U(r['title']); r['I'] = U(r['issuer']).rstrip('.,'); r['y'] = int(r['year']); r['d'] = dmy(r['date'])
    r['iss'] = int(r['issue'])
ACOM = json.load(open(os.path.join(B, 'acts.json'), encoding='utf-8'))
TX = json.load(open(os.path.join(B, 'texts.json'), encoding='utf-8'))
ACT_DIRS = {'zakon', 'pravilnik', 'uputstvo', 'poslovnik', 'pravilo', 'odluka', 'naredba', 'instrukcija', 'kodeks', 'statut', 'uredba'}


def act_dir(c):
    for f in c['files']:
        p = f.split('\t', 1)[1]
        parts = p.split('/')
        if len(parts) >= 4 and parts[0] in ACT_DIRS and re.match(r'sg\d+-', parts[2]):
            return '/'.join(parts[:3])
    return None


ACTS = {}
for c in reversed(ACOM):           # oldest first: the first commit of a folder is the act as published
    d = act_dir(c)
    if not d: continue
    a = ACTS.get(d)
    if a is None:
        k, y, sgx = d.split('/')
        ACTS[d] = a = {'dir': d, 'kind': k, 'y': int(y), 'iss': int(re.match(r'sg(\d+)', sgx).group(1)), 'title': c['an'], 'T': U(c['an']),
                       'ckind': c['kind'], 'pub': c['pub'][:10], 'inf': c['inf'][:10], 'enacted': c['enacted'][:10], 'prov': c['prov'], 'n': 0}
    a['n'] += 1
print('acts with text', len(ACTS), collections.Counter(a['kind'] for a in ACTS.values()))
LAST_PUB = max([r['d'] for r in SG if r['d']] + [a['pub'] for a in ACTS.values() if a['pub']])
FIRST_PUB = min(r['d'] for r in SG if r['d'])
PROFILE.update({'sg_index': len(SG), 'acts_text': len(ACTS), 'gazette_from': FIRST_PUB, 'gazette_to': LAST_PUB})
print('gazette', FIRST_PUB, LAST_PUB)

# ------------------------------------------------------------------ who issued it
ISSUER_RULES = [  # (group, regex on the issuer as the Gazette names it, upper case)
    ('ohr', r'VISOKI PREDSTAVNIK'),
    ('cc', r'^USTAVNI SUD BOSNE I HERCEGOVINE|^POVJERENSTVO ZA LJUDSKA PRAVA PRI USTAVNOM|^USTAVNI SUD BOSNE I HERCEGOVINE POVJERENSTVO'),
    ('court', r'EVROPSKI SUD|EUROPSKI SUD|ZASTUPNIKA/AGENTA|EVROPSKA KONVENCIJA|^SUD BOSNE|^SUD BIH|DOM ZA LJUDSKA PRAVA|USTAVNI SUD FEDERACIJE'),
    ('hjpc', r'VISOKO SUDSKO I TUŽILAČKO|VISOKOG SUDBENOG I TUŽITELJSKOG|VISOKOG SUDSKOG I TUŽILAČKOG'),
    ('com', r'^VIJEĆE MINISTARA'),
    ('pres', r'^PREDSJEDNIŠTVO BOSNE'),
    ('pa', r'PARLAMENTARN\w* SKUPŠTIN|PREDSTAVNIČK\w* DOM|ZASTUPNIČK\w* DOM|DOM NARODA PARLAMENTARNE|KOLEGIJ|PSBIH|ZAJEDNIČKA SLUŽBA PARLAMENTARNE|ZAJEDNIČKA KOMISIJA ZA ODBRANU|SEKRETARIJAT PARLAMENTARNE'),
    ('cik', r'CENTRALNA IZBORNA KOMISIJA|IZBORNO POVJERENSTVO|PRIVREMENO IZBORNO|PRIVREMENA IZBORNA|IZBORNO VIJEĆE ZA PRIGOVORE'),
    ('uio', r'INDIREKTNO OPOREZIVANJE|NEIZRAVNO OPOREZIVANJE'),
    ('kons', r'NACIONALNIH SPOMENIKA'),
    ('cb', r'^CENTRALNA BANKA'),
    ('kv', r'^KONKURENCIJSKO VIJEĆE'),
    ('reg', r'REGULATORN\w* KOMISIJA ZA ELEKTRIČNU|REGULATIVN\w* AGENCIJA ZA RADIJACIJSKU|REGULATORNA AGENCIJA ZA KOMUNIKACIJE|AGENCIJA ZA POŠTANSKI|REGULATORNI ODBOR|CIVILNO ZRAKOPLOVSTVO|CIVILNO VAZDUHOPLOVSTVO|NEZAVISNI OPERATOR|NEOVISNI OPERATOR|AGENCIJ\w* ZA PRUŽANJE USLUGA U ZRAČNOJ|SAVJET AGENCIJE ZA POŠTANSKI'),
    ('min', r'^MINISTARSTV|^MINISTARTSTV|^MINISTAR '),
    ('agency', r'^AGENCIJA|^BOSNA I HERCEGOVINA AGENCIJA|^URED |^UPRAVA |^INSTITUT|^DIREKCIJA|^KOMISIJA|^GRANIČNA POLICIJA|^DRŽAVNA (GRANIČNA|AGENCIJA|KOMISIJA)|^PRAVOBRANI|^INSTITUCIJA OMBUDSMENA|^OMBUDSMEN|^CENTAR ZA INFORMIRANJE|^VIJEĆE ZA|^SLUŽBA ZA|^IZVOZNO|^KOORDINA|^CENTRALNA/SREDIŠNJA|^CENTRALNA HARMONIZACIJSKA|^TUŽI|^TAJNIŠTVO|^ZAVOD ZA|^FOND|^BOSNA I HERCEGOVINA FOND|^BOSNA I HERCEGOVINA KOORDINACIONI|^ODBOR DRŽAVNE|^KOMITET|^VIJEĆE AGENCIJE|^DIREKCIJA ZA|^JAVNI RTV|^JAVNI RADIO|^POVJERENSTVO ZA IMENOVANJE'),
]


def issuer_group(I):
    for g, rx in ISSUER_RULES:
        if re.search(rx, I): return g
    return 'other'


VERB = re.compile(r'\b(donosi|donijelo je|donio je|donijela je|donijela|donijeli su|je donijelo|je donio|je donijela|je donijet|donijet je|usvojila je|usvojio je|'
                  r'usvojilo je|je usvojila|je usvojio|je usvojilo|utvrđuje|izdaje|propisuje|donosimo|objavljuje)\b', re.I)
TEXT_RULES = [  # (group, regex on the subject of the preamble's enacting clause)
    ('ohr', r'Visok\w* predstavnik'),
    ('pa', r'Parlamentarn\w* skupštin|Predstavnički dom|Zastupnički dom|Dom naroda|Kolegij'),
    ('pres', r'Predsjedništvo'),
    ('com', r'Vijeće ministara\b'),
    ('hjpc', r'Visoko sudsko i tužilačko|Visoko sudbeno i tužiteljsko|Visoko sudsko i tužiteljsko'),
    ('cc', r'Ustavni sud'),
    ('cik', r'[Cc]entraln\w* izborn\w* komisij|Središnj\w* izborn\w* povjerenstv'),
    ('uio', r'za (indirektno|neizravno) oporezivanje'),
    ('cb', r'Centraln\w* bank'),
    ('kv', r'Konkurencijsk\w* vijeć'),
    ('kons', r'nacionalnih spomenika'),
    ('reg', r'radijacijsk|[Rr]egulatorn\w* komisij\w* za električnu|Regulatorn\w* agencij\w* za komunikacije|Agencij\w* za poštanski|[Rr]egulatorn\w* odbor\w* željeznic|civilno (zrakoplovstvo|vazduhoplovstvo)|Direkcij\w* za civilno|[Rr]egulativn\w* agencij|za pružanje usluga u zračnoj'),
    ('min', r'\b([Mm]inistar|[Mm]inistrica|[Mm]inistarka|Ministarstvo)\b'),
    # nominative forms only: "na prijedlog Agencije ..." after "Vijeće ministara" must not win
    ('agency', r'\b(Agencija|[Dd]irektor|[Dd]irektorica|[Gg]eneralni direktor|Ured|Uprava|Institut|Direkcija|Zavod|Komisija|[Ss]tručno vijeće|[Uu]pravno vijeće|'
               r'[Uu]pravni odbor|Odbor|Služba|Fond|Kancelarija|Pravobranilaštvo|Ombudsmen\w*|Vijeće za \w+)\b'),
]


def issuer_from_text(head):
    """The institution named last before the enacting verb ("..., Vijeće ministara BiH, na 25. sjednici, donijelo je"), citations removed."""
    if not head: return 'unknown'
    h = re.sub(r'\([^()]{0,400}\)', ' ', head)
    m = VERB.search(h)
    subj = h[max(0, m.start() - 260):m.start()] if m else h
    best_g, best_end = 'unknown', -1
    for g, rx in TEXT_RULES:
        for mm in re.finditer(rx, subj):
            if mm.end() > best_end or (mm.end() == best_end and best_g == 'agency'):
                best_g, best_end = g, mm.end()
    return best_g


for r in SG:
    r['g'] = issuer_group(r['I'])
# the index files some runs of an issue under the High Representative although their titles are other institutions' standard acts
# (lists of medicines, the Presidency's reserve decisions, the Council of Ministers' allowances...): those become "other", and in an
# issue with two or more of them, so do its other entries that carry none of the High Representative's own forms
NOT_HR = re.compile(r'SPISAK LIJEKOVA|OVJERENE KANDIDATSKE|INTERVENTNOM KORIŠTENJU SREDSTAVA|ODOBRAVANJU SREDSTAVA IZ (BUDŽETSKE |TEKUĆE )?REZERV|KAPITALNIH ULAGANJA|'
                    r'PRERASPODJELI SREDSTAVA|NAKNADU ZA (PREKOVREMENI|PREVOZ)|VISINI NOVČANE NAKNADE|CIJENI OBRAZACA|PRIVREMENOM FINANSIRANJU')
HR_FORM = re.compile(r'KOJOM SE|KOJIM SE|NALOG|VISOK\w* PREDSTAVNIK|MEĐUNARODN|SMJENJ|ZABRAN|SUPERVIZOR')
_hr = [r for r in SG if r['g'] == 'ohr']
_bad_issues = {k for k, n in collections.Counter((r['y'], r['label']) for r in _hr if NOT_HR.search(r['T'])).items() if n >= 2}
misfiled = [r for r in _hr if NOT_HR.search(r['T']) or ((r['y'], r['label']) in _bad_issues and not HR_FORM.search(r['T']))]
for r in misfiled: r['g'] = 'other'
print('entries the index files under the High Representative but titled as other institutions\' acts:', len(misfiled), [(r['label'], r['T'][:50]) for r in misfiled])
PROFILE['ohr_misfiled'] = len(misfiled)
for d, a in ACTS.items():
    t = TX.get(d, {})
    a['g'] = 'pa' if a['kind'] == 'zakon' and a['ckind'] != 'publisher' else issuer_from_text(t.get('head', ''))
    if re.search(r'KOJOM SE (DONOSI|PROGLAŠAVA) ZAKON|ODLUKA VISOKOG PREDSTAVNIKA', a['T']): a['g'] = 'ohr'
print('index issuer groups', collections.Counter(r['g'] for r in SG).most_common())
print('text issuer groups', collections.Counter(a['g'] for a in ACTS.values()).most_common())
print('  other issuers (index):', collections.Counter(r['I'] for r in SG if r['g'] == 'other').most_common(12))

# ------------------------------------------------------------------ I. c01: what the Gazette publishes, by kind of act
KIND_WORDS = [('law', r'^ZAKON\b'), ('dec', r'^(ODLUK[AUE]|ODLUKA)\b'), ('rul', r'^(RJEŠENJ[EA]|ZAKLJUČ\w*|NALOG\w*)\b'),
              ('reg', r'^(PRAVILNI\w*|PRAVIL[OA]|UPUTSTV\w*|UPUT[UEA]|NAREDB\w*|INSTRUKCIJ\w*|POSLOVNI\w*|KODEKS\w*|STATUT\w*|UREDB\w*|METODOLOGIJ\w*|SMJERNIC\w*|KRITERIJ\w*|TARIF\w*|PRAVILA)\b')]


def title_kind(T):
    T = re.sub(r'^(IZMJEN\w*|DOPUN\w*|ISPRAVK\w*)( I (IZMJEN|DOPUN)\w*)? ', '', T) if re.match(r'^(IZMJENE|IZMJENU|DOPUNE|DOPUNU|IZMJENA) ', T) else T
    for k, rx in KIND_WORDS:
        if re.search(rx, T): return k
    return 'oth'


c01 = collections.defaultdict(collections.Counter)
for r in SG:
    k = 'court' if r['g'] in ('cc', 'court') else title_kind(r['T'])
    c01[r['y']][k] += 1
FOLD = {'zakon': 'law', 'odluka': 'dec'}
for a in ACTS.values():
    c01[a['y']][FOLD.get(a['kind'], 'reg')] += 1
OUT['c01'] = {'rows': [{'y': y, **c01[y]} for y in range(1997, 2027)], 'from': FIRST_PUB, 'to': LAST_PUB}
tot01 = collections.Counter()
for y in c01: tot01.update(c01[y])
print('c01', dict(tot01), sum(tot01.values()))

# ------------------------------------------------------------------ c02: who publishes, by year
c02 = collections.defaultdict(collections.Counter)
for r in SG: c02[r['g']][r['y']] += 1
for a in ACTS.values(): c02[a['g']][a['y']] += 1
OUT['c02'] = {'rows': [{'k': g, 'n': sum(v.values()), 'by': {str(y): n for y, n in sorted(v.items())}, 'first': min(v)} for g, v in c02.items()],
              'text_unknown': sum(1 for a in ACTS.values() if a['g'] == 'unknown'), 'text_n': len(ACTS)}
print('c02', sorted(((r['k'], r['n'], r['first']) for r in OUT['c02']['rows']), key=lambda x: -x[1]))

# ------------------------------------------------------------------ c03: when acts take effect, by kind
KIND3 = {'zakon': 'zakon', 'pravilnik': 'pravilnik', 'uputstvo': 'uputstvo', 'odluka': 'odluka', 'naredba': 'naredba', 'poslovnik': 'poslovnik', 'pravilo': 'pravilo'}
c03 = collections.defaultdict(collections.Counter)
for a in ACTS.values():
    if a['ckind'] == 'publisher' or not a['pub'] or not a['inf']: continue      # consolidated texts are dated on their issue day
    L = (D(a['inf']) - D(a['pub'])).days
    cat = 'before' if L < 0 else 'same' if L == 0 else 'next' if L == 1 else 'eighth' if L == 8 else 'later'
    c03[KIND3.get(a['kind'], 'other')][cat] += 1
    c03[KIND3.get(a['kind'], 'other')]['_n'] += 1
OUT['c03'] = [{'k': k, **v} for k, v in c03.items()]
print('c03', OUT['c03'])

# ------------------------------------------------------------------ c04: what became of the acts (registry statuses)
REG = json.load(open(os.path.join(R, 'registry', 'data', 'acts.json'), encoding='utf-8'))['acts']
c04 = collections.defaultdict(collections.Counter)
for a in REG:
    s = a['status']
    if s == 'withdrawn': continue
    # repealed first, then amended after its latest text (even if an earlier consolidated text exists), then consolidated
    st = 'repealed' if s.startswith('repealed') else 'amended' if s.startswith('amended') else 'consol' if (a.get('versions') or 1) > 1 else \
        'amending' if s == 'amending act' else 'force'
    c04[a['kind']][st] += 1
OUT['c04'] = [{'k': k, **v} for k, v in c04.items()]
PROFILE['registry_acts'] = sum(1 for a in REG if a['status'] != 'withdrawn')
# a later version is either an official consolidated text or, for an act repealed as a whole on a known day, the empty last version
PROFILE['consolidated'] = sum(1 for a in REG if (a.get('versions') or 1) - (1 if re.match(r'repealed \d{4}-', a['status']) else 0) > 1)
PROFILE['amended_by_any'] = sum(1 for a in REG if a.get('amended_by'))
print('c04', OUT['c04'], PROFILE['consolidated'])

# ------------------------------------------------------------------ II. c05: the Constitution, term by term
PARTS = ['preamble'] + ['art-%02d' % i for i in range(1, 13)] + ['annex-i', 'annex-ii']
TERMS = [('entity', r'\b[Ee]ntit(y|ies)\b'), ('fbih', r'\bFederation\b'), ('rs', r'\bRepublika Srpska\b'), ('bosniac', r'\bBosniacs?\b'), ('croat', r'\bCroats?\b'),
         ('serb', r'\bSerbs?\b'), ('others', r'\bOthers\b'), ('citizen', r'\b[Cc]itizens?\b|\b[Cc]itizenship\b')]
c05 = []
for p in PARTS:
    t = open(os.path.join(R, 'constitution', p + '.md'), encoding='utf-8').read()
    head = t.split('\n', 1)[0].lstrip('# ').strip()
    body = t.split('\n', 1)[1] if '\n' in t else ''
    c05.append({'p': p, 'head': head, 'words': len(re.findall(r"[A-Za-z][A-Za-z'-]*", body)), **{k: len(re.findall(rx, body)) for k, rx in TERMS}})
annex1 = open(os.path.join(R, 'constitution', 'annex-i.md'), encoding='utf-8').read()
OUT['c05'] = {'parts': c05, 'annex1_items': len(re.findall(r'^\s*\d+\.\s', annex1, re.M))}
print('c05', [(x['p'], x['words'], x['entity'], x['bosniac'] + x['croat'] + x['serb'], x['others'], x['citizen']) for x in c05], OUT['c05']['annex1_items'])

# ------------------------------------------------------------------ c06: the High Representative's decisions
HR_TERMS = [('westendorp', '1997-06-18', '1999-08-17'), ('petritsch', '1999-08-18', '2002-05-26'), ('ashdown', '2002-05-27', '2006-01-31'),
            ('schwarz', '2006-02-01', '2007-06-30'), ('lajcak', '2007-07-01', '2009-03-25'), ('inzko', '2009-03-26', '2021-07-31'),
            ('schmidt', '2021-08-01', '2026-06-30')]


def hr_of(d):
    for k, a, z in HR_TERMS:
        if a <= d <= z: return k
    return None


def ohr_type(T):
    if T.strip(' .') in ('', 'ODLUKU', 'ODLUKA', 'VISOKOG PREDSTAVNIKA', 'ODLUKA VISOKOG PREDSTAVNIKA', 'ODLUKU BOSNE I HERCEGOVINE'): return 'untitled'
    if re.search(r'UKIDA\w* ZABRAN|UKINE\w* (OSTATAK )?ZABRAN|UKIDANJ\w* ZABRAN|UKIDA SUSPENZIJ', T): return 'lift'
    if re.search(r'ZAKON|IZBORN\w* ZAKON', T) and re.search(r'DONOSI|DONOŠENJ|PROGLAŠ|ODLUK\w* O ZAKONU|^ZAKON|IZMJENAMA I DOPUNAMA (IZBORNOG )?ZAKON|O IZMJENI ZAKONA|PRIVREMEN\w* ZAKON|DOPUNI ZAKONA|IZMJEN\w* ZAKONA|ZAKON O', T) \
            and not re.search(r'PREDLAŽE ZAKON|PROVEDB\w* ODLUKE USTAVNOG|TUMAČENJ|PRIMJENI NALOGA|ISPRAVK', T): return 'law'
    if re.search(r'SMJENJUJE|SMJENI|SMJENJIVANJ|RAZRJEŠ\w* (DUŽNOSTI|SA )|ZABRAN\w* (OBAVLJANJ|VRŠENJ)|ZABRANJUJE|SUSPEND|SMJENJEN|UDALJAVANJ|S POLOŽAJA|SA POLOŽAJA|SA FUNKCIJE|S FUNKCIJE', T): return 'remove'
    if re.search(r'IMENOVANJ|IMENUJE|POSTAVLJENJ|PONOVNOM IMENOVANJ|PRODUŽ\w* MANDAT|PRODUŽENJU MANDATA', T): return 'appoint'
    return 'other'


OHR = []
law_key = lambda T: re.sub(r'\s*(\(|,\s*KOJI|,\s*U DODATKU|KOJI SE).*$', '', T[T.find('ZAKON'):]) if 'ZAKON' in T else None
ohr_idx = [r for r in SG if r['g'] == 'ohr' and 'LIKVIDATOR' not in r['I']]
dropped = 0
for r in ohr_idx:
    # an imposed law can be listed twice in one issue: the decision and, as its own entry, the law it enacts
    if r['T'].startswith('ZAKON') and any(o is not r and o['label'] == r['label'] and not o['T'].startswith('ZAKON') and law_key(o['T']) and
                                          (law_key(o['T']) in r['T'] or law_key(r['T']) in o['T']) for o in ohr_idx):
        dropped += 1; continue
    OHR.append({'d': r['d'], 'y': r['y'], 'lbl': r['label'], 't': ohr_type(r['T']), 'title': r['title'], 'src': 'index'})
print('c06: law entries listed beside their decision, not counted again:', dropped)
for a in ACTS.values():
    if a['g'] != 'ohr': continue
    t = a['T']
    if t == 'ODLUKA VISOKOG PREDSTAVNIKA':      # untitled: the operative title follows "donosim" after the preamble
        txt = U(TX.get(a['dir'], {}).get('long', '') or TX.get(a['dir'], {}).get('head', ''))
        m = re.search(r'\bDONOSIM\w*\s+(?:SLJEDEĆ\w*\s+)?((?:ODLUK\w*|NALOG\w*)\s+(?:KOJOM|KOJIM)\s+SE\s+.{10,230}?)(?=\s+(?:ČLAN\s+1|I\.\s|DIO\s|POGLAVLJE|\(1\))|$)', txt)
        if m: t = re.sub(r'^ODLUK\w*', 'ODLUKA', m.group(1).strip())
        else:   # the law it enacts, as the text names it
            m = re.search(r'(ZAKON\w* O (?:IZMJEN\w*|DOPUN\w*)[^"“”„(.;:]{5,160}?)\s*(?:\d|ČLAN|$)', txt)
            if m: t = 'ODLUKA KOJOM SE DONOSI ' + m.group(1).strip()
        print('  c06 untitled text decision', a['dir'], '->', t[:120])
        a['T'] = t      # so that the citation chains of chart 7 find the law it enacts
    OHR.append({'d': a['pub'], 'y': a['y'], 'lbl': '%d/%s' % (a['iss'], str(a['y'])[2:]), 't': ohr_type(t), 'title': t if t != U(a['title']) else a['title'], 'src': 'text'})
for o in OHR: o['hr'] = hr_of(o['d'])
OHR.sort(key=lambda o: o['d'])
OUT['c06'] = {'items': [[o['d'], o['t'], o['hr'], o['lbl'], o['title'][:190]] for o in OHR], 'terms': HR_TERMS}
print('c06', len(OHR), collections.Counter(o['t'] for o in OHR), collections.Counter(o['hr'] for o in OHR))
print('  other types:', [o['title'][:90] for o in OHR if o['t'] == 'other'][:40])

# ------------------------------------------------------------------ c07: the most-amended laws, from the Gazette numbers acts cite
ISSUES = set()
for r in SG: ISSUES.add((r['iss'], r['y']))
for a in ACTS.values(): ISSUES.add((a['iss'], a['y']))
LAWS7 = [  # key, regex on a cited name (lower case), regex on Gazette titles (upper case), bs name, en name
    ('izborni', r'izborn\w* zakon', r'IZBORN\w* ZAKON', 'Izborni zakon BiH', 'Election Law'),
    ('zkp', r'zakon\w* o krivičnom postupku', r'KRIVIČNOM POSTUPKU', 'Zakon o krivičnom postupku BiH', 'Criminal Procedure Code'),
    ('kz', r'^krivičn\w* zakon', r'KRIVIČN\w* ZAKON', 'Krivični zakon BiH', 'Criminal Code'),
    ('plate', r'zakon\w* o (plaćama|platama) i naknadama u institucijama', r'(PLAĆAMA|PLATAMA) I NAKNADAMA U INSTITUCIJAMA', 'Zakon o platama i naknadama u institucijama BiH', 'Law on Salaries and Allowances in the Institutions'),
    ('takse', r'zakon\w* o administrativnim taksama', r'ADMINISTRATIVN\w* TAKS', 'Zakon o administrativnim taksama', 'Law on Administrative Fees'),
    ('drsluzba', r'zakon\w* o državnoj službi u institucijama', r'DRŽAVNOJ SLUŽBI U INSTITUCIJAMA', 'Zakon o državnoj službi u institucijama BiH', 'Law on the Civil Service in the Institutions'),
    ('pdv', r'zakon\w* o porezu na doda\w* vrijednost', r'POREZU NA DODA\w* VRIJEDNOST', 'Zakon o porezu na dodanu vrijednost', 'Law on Value Added Tax'),
    ('ministarstva', r'zakon\w* o ministarstvima i drugim (organima|tijelima) uprave', r'MINISTARSTVIMA I DRUGIM (ORGANIMA|TIJELIMA) UPRAVE', 'Zakon o ministarstvima i drugim organima uprave BiH', 'Law on Ministries and Other Administrative Bodies'),
    ('saobracaj', r'zakon\w* o osnovama sigurnosti (saobraćaja|prometa) na (putevima|cestama)', r'OSNOVAMA SIGURNOSTI (SAOBRAĆAJA|PROMETA) NA (PUTEVIMA|CESTAMA)', 'Zakon o osnovama sigurnosti saobraćaja na putevima u BiH', 'Law on the Basics of Road Traffic Safety'),
    ('putne', r'zakon\w* o putnim ispravama', r'PUTNIM ISPRAVAMA', 'Zakon o putnim ispravama BiH', 'Law on Travel Documents'),
    ('nabavke', r'zakon\w* o javnim nabavkama', r'JAVNIM NABAVKAMA', 'Zakon o javnim nabavkama (2004.)', 'Law on Public Procurement (2004)'),
    ('carinska', r'zakon\w* o carinskoj tarifi', r'CARINSK\w* TARIF', 'Zakon o carinskoj tarifi', 'Law on the Customs Tariff'),
    ('akcize', r'zakon\w* o akcizama', r'AKCIZAMA', 'Zakon o akcizama u BiH', 'Law on Excise Duties'),
    ('indirektni', r'zakon\w* o sistemu indirektnog oporezivanja', r'SISTEMU INDIREKTNOG OPOREZIVANJA|SUSTAVU NEIZRAVNOG OPOREZIVANJA', 'Zakon o sistemu indirektnog oporezivanja', 'Law on the Indirect Taxation System'),
    ('policija', r'zakon\w* o policijskim službenicima', r'POLICIJSKIM SLUŽBENICIMA', 'Zakon o policijskim službenicima BiH', 'Law on Police Officers'),
    ('vm', r'zakon\w* o vijeću ministara', r'O (VIJEĆU|SAVJETU) MINISTARA', 'Zakon o Vijeću ministara BiH', 'Law on the Council of Ministers'),
    ('sudbih', r'zakon\w* o sudu bosne', r'O SUDU BOSNE', 'Zakon o Sudu BiH', 'Law on the Court of BiH'),
    ('vstv', r'zakon\w* o visokom sudskom', r'VISOKOM SUDSKOM', 'Zakon o VSTV-u BiH', 'Law on the HJPC'),
    ('drzavljanstvo', r'zakon\w* o državljanstvu', r'DRŽAVLJANSTVU', 'Zakon o državljanstvu BiH', 'Law on Citizenship'),
    ('upravi', r'^zakon\w* o upravi$', r'ZAKON\w* O UPRAVI\b', 'Zakon o upravi', 'Law on Administration'),
    ('finansiranje', r'zakon\w* o finansiranju institucija', r'FINANSIRANJU INSTITUCIJA|FINANCIRANJU INSTITUCIJA', 'Zakon o finansiranju institucija BiH', 'Law on the Financing of the Institutions'),
    ('carinska_pol', r'zakon\w* o carinskoj politici', r'CARINSKOJ POLITICI', 'Zakon o carinskoj politici', 'Law on Customs Policy'),
]
best = {}
NOT_LAW = re.compile(r'(pravilni\w*|uputstv\w*|uput\w*|odluk\w*|instrukcij\w*|naredb\w*|poslovni\w*|pravil\w*|uredb\w*|rješenj\w*|metodologij\w*|tarif\w*)\s+'
                     r'(o|za)\s+(primjen\w*|provođenj\w*|provedb\w*|sprovođenj\w*|izvršavanj\w*|izvršenj\w*|načinu primjene)\s*$', re.I)
for d, t in TX.items():
    pub = ACTS[d]['pub'] if d in ACTS else ''
    for name, nums, pre in t['cites']:
        nm = lat(name).lower()
        if NOT_LAW.search(lat(pre).lower()) or re.match(r'zakon\w* o (primjeni|provođenju)', nm): continue   # the numbers belong to a rulebook or the like
        m = list(re.finditer(r'(izborn\w+ zakon\w*|krivičn\w+ zakon\w*|zakon\w* o [^,;]*)', nm))
        if not m: continue
        nm = m[-1].group(1)
        nm = re.sub(r'^zakon\w* o (izmjen\w*|dopun\w*)( i (izmjen\w*|dopun\w*))? ', '', nm)   # "Zakona o izmjenama i dopunama Krivičnog zakona" cites the code itself
        nm = re.sub(r'\s+(bosne i hercegovine|u bosni i hercegovini|bih)\b.*$', '', nm).strip(' ,.')
        for key, rx, *_ in LAWS7:
            if re.search(rx, nm):
                seen, chain = set(), []
                for x in nums:
                    n_, yy = x.split('/'); n_ = int(n_); yv = 2000 + int(yy) if int(yy) < 90 else 1900 + int(yy)
                    if (n_, yv) in seen or (n_, yv) not in ISSUES: continue
                    seen.add((n_, yv)); chain.append((yv, n_))
                if key not in best or (len(chain), pub) > (len(best[key][0]), best[key][1]):
                    best[key] = (sorted(chain), pub, d)
                break
c07 = []
for key, rx, trx, nbs, nen in LAWS7:
    if key not in best: continue
    chain, pub, src = best[key]
    items = []
    for i, (yv, n_) in enumerate(chain):
        lbl = '%d/%s' % (n_, str(yv)[2:])
        here_idx = [r for r in SG if r['y'] == yv and r['iss'] == n_ and re.search(trx, r['T'])]
        here_txt = [x for x in ACTS.values() if x['y'] == yv and x['iss'] == n_ and re.search(trx, x['T'])]
        hr = any(r['g'] == 'ohr' for r in here_idx) or any(x['g'] == 'ohr' for x in here_txt)
        if i == 0:
            items.append([yv, lbl, 'orig_hr' if hr else 'orig']); continue
        pa = any(r['g'] == 'pa' and 'ISPRAVK' not in r['T'] for r in here_idx) or any(x['kind'] == 'zakon' for x in here_txt)
        corr = any('ISPRAVK' in r['T'] for r in here_idx) or any('ISPRAVK' in x['T'] for x in here_txt)
        com = any(r['g'] in ('com', 'min') for r in here_idx) or any(x['g'] in ('com', 'min') for x in here_txt)
        mk = 'hr' if hr else 'pa' if pa else 'corr' if corr else 'com' if com else 'unk'
        if mk == 'unk':
            print('   c07 unk', key, lbl, [(r['I'][:20], r['T'][:70]) for r in SG if r['y'] == yv and r['iss'] == n_][:6], [x['T'][:60] for x in ACTS.values() if x['y'] == yv and x['iss'] == n_][:4])
        items.append([yv, lbl, mk])
    if key == 'kz' and items and items[0][2] == 'orig':
        # the issue list of 3/03 cuts the title short; the repository's data/laws.csv records the 2003 code as imposed by the High Representative
        dl = list(csv.DictReader(open(os.path.join(R, 'data', 'laws.csv'), encoding='utf-8')))
        if any('Criminal Code' in r['title'] and 'imposed by the High Representative' in r['title'] for r in dl):
            items[0][2] = 'orig_hr'
    c07.append({'k': key, 'bs': nbs, 'en': nen, 'items': items, 'src': src, 'n': len(items) - 1})
c07.sort(key=lambda r: -r['n'])
OUT['c07'] = c07
for r in c07: print('c07', r['k'], r['n'], collections.Counter(i[2] for i in r['items']), ' '.join(i[1] + ':' + i[2] for i in r['items']))

# ------------------------------------------------------------------ III. c08: the laws of each year, and who made them
def law_cat(T):
    if re.search(r'O USVAJANJU ZAKONA', T): return 'adopt'
    if re.search(r'BUDŽET|PRORAČUN', T): return 'budget'
    if re.search(r'\b(IZMJEN\w*|DOPUN\w*)\b', T): return 'amend'
    return 'new'


LAWT = re.compile(r'^(ZAKON|OKVIRNI ZAKON|KRIVIČNI ZAKON|IZBORNI ZAKON|CARINSKA TARIFA)\b')
c08 = collections.defaultdict(collections.Counter)
c08_titles = collections.defaultdict(list)
for r in SG:
    if r['g'] == 'pa' and LAWT.search(r['T']) and not re.search(r'PREČIŠĆEN|ISPRAVK', r['T']):
        c08[r['y']][law_cat(r['T'])] += 1
for a in ACTS.values():
    if a['kind'] == 'zakon' and a['ckind'] != 'publisher' and not re.search(r'PREČIŠĆEN', a['T']):
        c08[a['y']][law_cat(a['T'])] += 1
for o in OHR:
    if o['t'] == 'law': c08[o['y']]['hr'] += 1
OUT['c08'] = [{'y': y, **c08[y]} for y in range(1997, 2027)]
print('c08', [(r['y'], dict((k, v) for k, v in r.items() if k != 'y')) for r in OUT['c08']])

# ------------------------------------------------------------------ c09: the two houses' votes on the same law
MON = [('jan', 1), ('feb', 2), ('mar', 3), ('apr', 4), ('maj', 5), ('jun', 6), ('jul', 7), ('aug', 8), ('avg', 8), ('sep', 9), ('okt', 10), ('nov', 11), ('dec', 12),
       ('sij', 1), ('velj', 2), ('ožu', 3), ('trav', 4), ('svib', 5), ('lip', 6), ('srp', 7), ('kol', 8), ('ruj', 9), ('list', 10), ('stud', 11), ('pros', 12)]


def last_date(ph):
    ph = ph.lower()
    m = re.findall(r'(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})', ph)
    if m:
        d_, m_, y_ = m[-1]; return date(int(y_), int(m_), int(d_))
    m = re.findall(r'(\d{1,2})\.?\s+([a-zčćžšđ]+)\s+(\d{4})', ph)
    if m:
        d_, mn, y_ = m[-1]
        for k, v in MON:
            if mn.startswith(k): return date(int(y_), v, int(d_))
    return None


c09 = []
for a in ACTS.values():
    if a['kind'] != 'zakon' or a['ckind'] == 'publisher': continue
    h = TX.get(a['dir'], {}).get('head', '')
    hr_ = re.search(r'sj[ec]dnic\w*\s+(?:Predstavničkog|Zastupničkog)\s+doma[^,]*?,?\s*održan\w*\s+(.{0,60}?\d{4})', h)
    hp_ = re.search(r'sj[ec]dnic\w*\s+Doma\s+naroda[^,]*?,?\s*održan\w*\s+(.{0,60}?\d{4})', h)
    if not (hr_ and hp_): continue
    x, z = last_date(hr_.group(1)), last_date(hp_.group(1))
    if not (x and z): continue
    c09.append([x.isoformat(), z.isoformat(), a['pub'], a['y'], a['title'][:150]])
OUT['c09'] = c09
gaps = [(D(r[1]) - D(r[0])).days for r in c09]
print('c09', len(c09), 'of', sum(1 for a in ACTS.values() if a['kind'] == 'zakon' and a['ckind'] != 'publisher'), 'median |gap|', statistics.median([abs(g) for g in gaps]),
      'same day', sum(1 for g in gaps if g == 0), 'HoP later', sum(1 for g in gaps if g > 0), 'HoR later', sum(1 for g in gaps if g < 0), 'max', max(gaps), min(gaps))

# ------------------------------------------------------------------ c10: bills that never became law
BILLS = json.load(open(os.path.join(B, 'bills.json'), encoding='utf-8'))


def proposer(p):
    p = p.lower()
    if 'vijeće ministara' in p: return 'com'
    if p.startswith('klub'): return 'club'
    if re.search(r'komisij|odbor|radna grupa|interresorn', p): return 'cmte'
    if re.search(r'poslani|delegat|izaslani|zastupni|zamjenik predsjedavaj', p): return 'mps'
    return 'other'


c10 = {'rows': collections.defaultdict(collections.Counter), 'years': collections.defaultdict(collections.Counter), 'const': [], 'lang': collections.Counter(), 'amend': collections.Counter()}
for b in BILLS:
    g = proposer(b['proposer']); c10['rows'][g][b['status']] += 1
    c10['years'][b['record_date'][:4]][g] += 1
    c10['lang']['sr' if 'srpski' in b['proposer'] else 'hr' if 'hrvatski' in b['proposer'] else '-'] += 1
    c10['amend']['amend' if re.search(r'izmjen|dopun', b['title'], re.I) else 'new'] += 1
    if re.search(r'amandman\w* .*na ustav|amandman\w* na ustav', b['title'], re.I):
        c10['const'].append([b['record_date'], b['status'], b['proposer'], re.sub(r'\s*-\s*\(u proceduri.*$', '', b['title'])])
OUT['c10'] = {'rows': {k: dict(v) for k, v in c10['rows'].items()}, 'years': {k: dict(v) for k, v in sorted(c10['years'].items())},
              'const': sorted(c10['const']), 'lang': dict(c10['lang']), 'amend': dict(c10['amend']), 'n': len(BILLS)}
print('c10', OUT['c10']['rows'], OUT['c10']['const'])

# ------------------------------------------------------------------ c11: when the state budget law was published
BUD = re.compile(r'^ZAKON O (IZVRŠENJU )?(BUDŽET|PRORAČUN)\w* INSTITUCIJA .*?ZA (\d{4})')
TEMP = re.compile(r'PRIVREMEN\w* (FINANSIRANJ|FINANCIRANJ)\w*')
c11 = {}
for r in SG:
    m = BUD.search(r['T'])
    if m and r['d']:
        y = int(m.group(3))
        if y not in c11 or r['d'] < c11[y]['pub']:
            c11[y] = {'y': y, 'pub': r['d'], 'lbl': r['label'], 'title': r['title'][:160]}
temp = collections.defaultdict(list)
for r in SG:
    if TEMP.search(r['T']) and r['d'] and r['g'] in ('com', 'pres', 'ohr') and not re.search(r'IZMJEN|DOPUN|OPERATIVNIM MJERAMA', r['T']):
        m = re.search(r'(\d{4})', r['T']); temp[int(m.group(1)) if m else r['y']].append(r['d'])
for a in ACTS.values():
    if TEMP.search(a['T']) and a['pub'] and not re.search(r'IZMJEN|DOPUN|OPERATIVNIM MJERAMA', a['T']):
        m = re.search(r'(\d{4})\.? GODIN', a['T']) or re.search(r'(\d{4})', a['T'])
        temp[int(m.group(1)) if m else a['y']].append(a['pub'])
OUT['c11'] = [{'y': y, **(c11.get(y) or {}), 'temp': sorted(temp.get(y, []))} for y in range(1997, 2027)]
for r in OUT['c11']: print('c11', r['y'], r.get('pub'), r.get('lbl'), len(r['temp']))

# ------------------------------------------------------------------ c12: who hands out the budget reserve
RES = re.compile(r'TEKUĆ\w* (BUDŽETSK\w* )?REZERV|BUDŽETSK\w* REZERV|REZERV\w* BUDŽETA|INTERVENTN\w* (TEKUĆ\w* )?(REZERV|PRIČUV)|TEKUĆ\w* PRIČUV|PRIČUV\w* PRORAČUNA|IZ REZERVI')
RG = {'com': 'com', 'pres': 'pres', 'pa': 'pa', 'min': 'min', 'ohr': 'ohr'}
c12 = collections.defaultdict(collections.Counter)
for r in SG:
    if RES.search(r['T']): c12[r['y']][RG.get(r['g'], 'other')] += 1
for a in ACTS.values():
    if RES.search(a['T']): c12[a['y']][RG.get(a['g'], 'other')] += 1
OUT['c12'] = [{'y': y, **c12[y]} for y in range(1997, 2027)]
print('c12', [(r['y'], dict((k, v) for k, v in r.items() if k != 'y')) for r in OUT['c12'] if len(r) > 1])

# ------------------------------------------------------------------ c13: the excise on cigarettes, decision by decision
num = lambda s: float(s.replace('.', '').replace(',', '.'))
c13 = []
for a in ACTS.values():
    if not re.search(r'MINIMALNE AKCIZE NA CIGARETE', a['T']): continue
    t = TX.get(a['dir'], {}).get('long', '')
    yv = re.search(r'(?:od|primjenjuj\w*)\s+(?:od\s+)?(?:dana\s+)?(?:1\.\s*januara|01\.01\.)\s*(\d{4})', t)
    packs = re.findall(r'(\d+,\d{2}) KM (?:po|za) (?:pakiranj|pakovanj|kutij)\w*', t)
    per1000 = re.findall(r'(\d+(?:\.\d{3})*,\d{2}) KM (?:za|na) 1\.000 komada', t)
    basis = 'popular' if re.search(r'najpopularnij', t) else 'weighted' if re.search(r'ponderi[rs]an', t) else '?'
    if not (yv and len(packs) >= 3): print('  c13 parse?', a['dir'], packs[:4]); continue
    c13.append({'y': int(yv.group(1)), 'spec': num(packs[0]), 'price': num(packs[1]), 'min': num(packs[2]), 'basis': basis,
                'spec1000': num(per1000[0]) if per1000 else None, 'pub': a['pub'], 'lbl': '%d/%s' % (a['iss'], str(a['y'])[2:])})
c13.sort(key=lambda r: r['y'])
OUT['c13'] = c13
print('c13', [(r['y'], r['spec'], r['min'], r['price'], r['basis']) for r in c13])

# ------------------------------------------------------------------ IV. the Constitutional Court's decisions (database, one commit per decision)
CC = {}
for line in open(os.path.join(B, 'cc.tsv'), encoding='utf-8'):
    an, ae, d = line.rstrip('\n').split('\t')
    i = ae.split('@')[0]
    if i in CC: continue
    m = re.match(r'^(.*?)\s+(AP|U)-(\d+)/(\d+)\s*$', an)
    if not m: print('  cc unparsed', an); continue
    cy = int(m.group(4)); cy = 1900 + cy if cy >= 90 else 2000 + cy
    CC[i] = {'dt': m.group(1), 't': m.group(2), 'no': int(m.group(3)), 'cy': cy, 'd': d[:10]}
DT = {'Odluka o dopustivosti': 'adm', 'Odluka o meritumu': 'mer', 'Odluka o privremenoj mjeri': 'int', 'Rješenje o neizvršenju': 'nonenf',
      'Odluka o obustavi postupka': 'stop', 'Rješenje, zaključak, obavještenje i ostali akti': 'misc'}
c14 = collections.defaultdict(collections.Counter)
for c in CC.values(): c14[int(c['d'][:4])][DT.get(c['dt'], 'misc')] += 1
OUT['c14'] = {'rows': [{'y': y, **c14[y]} for y in range(1997, 2027)], 'n': len(CC), 'ap': sum(1 for c in CC.values() if c['t'] == 'AP'), 'u': sum(1 for c in CC.values() if c['t'] == 'U'),
              'last': max(c['d'] for c in CC.values())}
print('c14', len(CC), collections.Counter(c['dt'] for c in CC.values()))

c15 = collections.defaultdict(collections.Counter)
for c in CC.values():
    if c['t'] != 'AP' or c['dt'] != 'Odluka o meritumu': continue
    y = int(c['d'][:4]); age = y - c['cy']
    if age < 0: continue
    c15[y][min(age, 4)] += 1
OUT['c15'] = [{'y': y, 'a': [c15[y][k] for k in range(5)]} for y in range(2004, 2027)]
# median age (decision year - filing year) of appeals decided on admissibility and on the merits, for the note
OUT['c15x'] = {k: statistics.median([int(c['d'][:4]) - c['cy'] for c in CC.values() if c['t'] == 'AP' and c['dt'] == dt]) for k, dt in (('adm', 'Odluka o dopustivosti'), ('mer', 'Odluka o meritumu'))}
print('c15', [(r['y'], r['a']) for r in OUT['c15']])

c16 = sorted([[c['d'], c['t'], c['no'], c['cy']] for c in CC.values() if DT.get(c['dt']) == 'nonenf'])
OUT['c16'] = c16
print('c16', len(c16), collections.Counter(r[1] for r in c16), collections.Counter(r[0][:4] for r in c16))

# ------------------------------------------------------------------ V. the Court of Bosnia and Herzegovina (its case pages)
SUD = json.load(open(os.path.join(B, 'sud.json'), encoding='utf-8'))
cc_titles = {}
for line in open(os.path.join(R, 'criminal-code', 'README.md'), encoding='utf-8'):
    m = re.match(r'\| Article (\d+)([a-z]?)\. ([^|]+?) \|', line)
    if m and not m.group(2): cc_titles[int(m.group(1))] = m.group(3).strip()
CASES = []
for s in SUD:
    dp = s.get('Datum potvrđivanja optužnice', '')
    m1 = re.match(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', dp)
    m2 = re.search(r'okončan\w*\s*:\s*(\d{1,2})\.(\d{1,2})\.(\d{4})', dp)
    sec = s.get('Odjel', '')
    sec = 's1' if re.match(r'Odjel I\b(?! I)', sec) else 's2' if re.match(r'Odjel II\b', sec) else 'other'
    ch = s.get('Optužnica', '')
    mo = re.search(r'[Kk]rivičn\w*\s+djel\w*\s*:?\s*(.+?)\s+(?:iz|po)\s+(?:člana|čl\.|članu)\s*(\d+)', ch)
    code = 'bih' if re.search(r'KZ\s*BiH|KZBiH|KZ BIH|Krivičnog zakona Bosne i Hercegovine(?! \(KZ ?F)|KZ SFRJ|preuzet', ch) else 'other'
    if re.search(r'KZ\s*SFRJ|SFRJ|preuzet', ch): code = 'sfrj'
    if re.search(r'KZ\s*F\s*BiH|KZ FBiH|Federacije', ch): code = 'fbih'
    if re.search(r'KZ\s*RS|Republike Srpske', ch): code = 'rs'
    if re.search(r'KZ\s*BD|Brčko', ch): code = 'bd'
    CASES.append({'case': s['case'], 'sec': sec, 'conf': date(int(m1.group(3)), int(m1.group(2)), int(m1.group(1))).isoformat() if m1 else None,
                  'fin': date(int(m2.group(3)), int(m2.group(2)), int(m2.group(1))).isoformat() if m2 else None,
                  'status': 'final' if 'pravosnažno' in s.get('Status on the official page', '') else 'open' if 'toku' in s.get('Status on the official page', '') else 'unk',
                  'acc': int(s['Broj optuženih']) if re.match(r'^\d+$', s.get('Broj optuženih', '') or '') else None,
                  'off': mo.group(1).strip(' "„”') if mo else None, 'art': int(mo.group(2)) if mo else None, 'code': code if mo else None})
c17 = collections.defaultdict(collections.Counter)
for c in CASES:
    if c['conf']: c17[int(c['conf'][:4])][c['sec']] += 1
OUT['c17'] = {'rows': [{'y': y, **c17[y]} for y in sorted(c17)], 'n': len(CASES), 'final': sum(1 for c in CASES if c['status'] == 'final'),
              'open': sum(1 for c in CASES if c['status'] == 'open'), 'acc': sum(c['acc'] or 0 for c in CASES),
              'acc_dist': dict(collections.Counter(min(c['acc'], 6) for c in CASES if c['acc']))}
print('c17', OUT['c17'])


# the first offence an indictment names, in groups; the article is the one of the Criminal Code of BiH (its English title from criminal-code/)
OFFENCES = [('genocide', r'genocid', 171), ('cah', r'protiv čovječnosti', 172), ('wcciv', r'ratn\w* zločin\w* protiv civiln', 173),
            ('wcpow', r'ratn\w* zločin\w* protiv ratnih zarobljenik', 175), ('terror', r'terori|paravojn|parapolicij', None),
            ('wcoth', r'ratn\w* zločin|ranjenik|običaja rata|ranjavanj\w* neprijatelj', None),
            ('org', r'kriminal', 250), ('assoc', r'udruživanj\w* radi (činjenj|vršenj)|dogovor radi činjenj', 249),
            ('drugs', r'opojn\w* drog', 195), ('tax', r'porezn\w* utaj|utaj\w* poreza|neplaćanj\w* poreza|carinsk\w* pr\w*evar|poreza na dodanu|pdv|akcizn|skladištenj\w* robe', None),
            ('smugp', r'kri\w*mčarenj\w* (osoba|ljudi|migranat)', 189), ('smugg', r'kri\w*mčar', '214–215'), ('traff', r'trgovin\w* (ljudima|osobama)|trgovin\w* ljud', 186),
            ('laund', r'pranj\w* novca', 209), ('bribe', r'oblika koristi|primanj\w* dara|davanj\w* dara|\bmit', '217–218'),
            ('abuse', r'zloupotreb\w* (službenog )?(položaj|ovlašt)|nesavjesn\w* rad|pronevjer', 220),
            ('forg', r'krivotvor|falsifik|prevar', None), ('arms', r'oružj|eksploziv|municij', None)]
off18 = collections.defaultdict(lambda: {'n': 0, 's1': 0, 's2': 0, 'other': 0, 'names': collections.Counter()})
for c in CASES:
    if not c['off']: continue
    o_ = re.sub(r'\s+', ' ', c['off'].lower())
    k = next((k for k, rx, _ in OFFENCES if re.search(rx, o_)), 'misc')
    o = off18[k]; o['n'] += 1; o[c['sec']] += 1; o['names'][c['off'][:80]] += 1
ART = {k: a for k, _, a in OFFENCES}
rows18 = [{'k': k, 'art': ART.get(k), 'en_code': cc_titles.get(ART.get(k)) if isinstance(ART.get(k), int) else None, 'n': o['n'], 's1': o['s1'], 's2': o['s2'], 'other': o['other'],
           'top': o['names'].most_common(3)} for k, o in off18.items()]
rows18.sort(key=lambda r: (r['k'] == 'misc', -r['n']))
OUT['c18'] = {'rows': rows18, 'n': sum(r['n'] for r in rows18), 'none': sum(1 for c in CASES if not c['off'])}
print('c18', [(r['k'], r['art'], r['en_code'], r['n'], r['s1'], r['s2'], r['other']) for r in rows18], OUT['c18']['n'], OUT['c18']['none'])
print('  c18 misc names', off18['misc']['names'].most_common(25))

c19 = collections.defaultdict(list)
for c in CASES:
    if c['conf'] and c['fin'] and c['sec'] in ('s1', 's2'):
        dd = (D(c['fin']) - D(c['conf'])).days
        if dd >= 0: c19[(c['sec'], int(c['conf'][:4]))].append(dd)
open19 = collections.Counter((c['sec'], int(c['conf'][:4])) for c in CASES if c['conf'] and c['status'] == 'open' and c['sec'] in ('s1', 's2'))
OUT['c19'] = [{'s': s, 'y': y, 'n': len(v), 'med': statistics.median(v), 'q1': statistics.quantiles(v, n=4)[0] if len(v) > 3 else min(v),
               'q3': statistics.quantiles(v, n=4)[2] if len(v) > 3 else max(v), 'open': open19[(s, y)]} for (s, y), v in sorted(c19.items())]
all19 = {s: [d for (ss, y), v in c19.items() if ss == s for d in v] for s in ('s1', 's2')}
OUT['c19x'] = {s: {'n': len(v), 'med': statistics.median(v)} for s, v in all19.items()}
print('c19', [(r['s'], r['y'], r['n'], r['med'], r['open']) for r in OUT['c19']], OUT['c19x'])

# ------------------------------------------------------------------ c20: the HJPC's appointments
def jsys(T):
    if re.search(r'SUD\w* BOSNE I HERCEGOVINE\b(?! I)|SUD\w* BIH\b|TUŽI\w* BOSNE I HERCEGOVINE|TUŽITELJSTV\w* BOSNE I HERCEGOVINE|TUŽILAŠTV\w* BIH|PRAVOBRANILAŠTV', T) and not re.search(r'FEDERACIJE|REPUBLIKE SRPSKE|BRČKO', T): return 'state'
    if re.search(r'BRČKO|BRCKO', T): return 'bd'
    if re.search(r'REPUBLIK\w* SRPSK|OSNOV\w* SUD|OKRUŽN\w*|VIŠ\w* PRIVREDN\w* SUD|PRIVREDN\w* SUD U (BANJ|DOBOJ|BIJELJIN|ISTOČN|TREBINJ)|REPUBLIČK\w* JAVN|POSEBN\w* ODJEL\w* ZA SUZBIJANJE', T): return 'rs'
    if re.search(r'OPĆINSK\w* SUD|OPCINSK|KANTONALN\w*|ŽUPANIJSK\w*|FEDERACIJ\w*|FEDERALN\w*|KANTONA\b|TUŽILAŠTV\w* (TUZLANSKOG|ZENIČKO|HERCEGOVAČKO|UNSKO|SREDNJOBOSANSKOG|BOSANSKO|POSAVSKOG|HNK|SBK)', T): return 'fbih'
    return 'other'


c20 = collections.defaultdict(collections.Counter)
kind20 = collections.Counter()
for r in SG:
    if r['g'] != 'hjpc': continue
    T = r['T']
    if not re.search(r'IMENOVANJ|IMENUJE', T) or re.search(r'PONIŠTENJ|IZMJEN|ISPRAVK|KRITERIJ|PRAVILNIK|POSLOVNIK|KOMISIJ\w* ZA|RAZRJEŠENJ|DISCIPLINSK|SEKRETARIJAT', T): continue
    s = jsys(T); job = 'pros' if re.search(r'TUŽI(LA|TE)', T) and not re.search(r'\bSUDIJ|\bSUCA\b|\bSUTKINJ', T) else 'judge'
    c20[r['y']][s + '_' + job] += 1; kind20[s] += 1
OUT['c20'] = [{'y': y, **c20[y]} for y in range(2002, 2027)]
print('c20', kind20, sum(kind20.values()))
print('  c20 other samples', [r['T'][:90] for r in SG if r['g'] == 'hjpc' and re.search(r'IMENOVANJ', r['T']) and jsys(r['T']) == 'other'][:15])

# ------------------------------------------------------------------ profile
PROFILE.update({
    'commits_cc': sum(1 for _ in open(os.path.join(B, 'cc.tsv'), encoding='utf-8')), 'cc_decisions': len(CC), 'bills': len(BILLS), 'sud_cases': len(CASES),
    'head': os.environ.get('HEAD_SHA', ''), 'built': date.today().isoformat(), 'gazette_items': sum(tot01.values()),
    'ohr': len(OHR), 'issues': len({(r['y'], r['iss']) for r in SG} | {(a['y'], a['iss']) for a in ACTS.values()}),
})
print('profile', PROFILE)
json.dump({'charts': OUT, 'profile': PROFILE}, open(os.path.join(B, 'data.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
