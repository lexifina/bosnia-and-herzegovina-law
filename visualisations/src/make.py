"""Rebuild visualisations/pravo-bosne-i-hercegovine-u-20-grafikona.html from this repository.

    python visualisations/src/make.py [--repo PATH] [--ref REF]

Everything is read from git objects of REF (default: origin/main if present, else HEAD), so it works in a blobless or
--no-checkout clone; missing blobs of the folders it reads are fetched in batches first (git fetch --stdin), the way git
itself fetches promisor objects. Scratch output goes to visualisations/src/.build/:
  1. git log of caselaw/ (Constitutional Court decisions: author = decision type and case number) -> cc.tsv
  2. git log of the act folders, with trailers and the files each commit touches             -> acts.json
  3. the Gazette index: sluzbeni-glasnik/<year>/<issue>/<item>/README.md                      -> sg.tsv
  4. bills (bill/**/record.json) and Court of BiH case pages (sudska-praksa/sud-bih/)         -> bills.json, sud.json
  5. the preamble or single text of every act: the issuer's words, both houses' sessions,
     the laws it cites with their Gazette numbers, and the excise decisions' text             -> texts.json
  6. the Constitution, the Criminal Code's article list and registry/data/acts.json           -> repo/
  7. prep.py turns those into data.json; build.py fills page.tpl.html with it.
Memory stays small: logs and blobs are streamed one record at a time.
"""
import argparse, csv, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument('--repo', default=os.path.abspath(os.path.join(HERE, '..', '..')))
ap.add_argument('--ref', default=None, help='default: origin/main if present, else HEAD')
ap.add_argument('--out', default=os.path.join(HERE, '..', 'pravo-bosne-i-hercegovine-u-20-grafikona.html'))
a = ap.parse_args()
B = os.path.join(HERE, '.build')
os.makedirs(os.path.join(B, 'repo'), exist_ok=True)
ENV = dict(os.environ, GIT_NO_LAZY_FETCH='1')   # never fetch blob by blob; missing ones are fetched in batches below


def git(*args, inp=None):
    return subprocess.run(['git', '-C', a.repo, *args], check=True, capture_output=True, input=inp, env=ENV).stdout


def stream(*args):
    p = subprocess.Popen(['git', '-C', a.repo, *args], stdout=subprocess.PIPE, env=ENV)
    for raw in p.stdout:
        yield raw.decode('utf-8', 'replace').rstrip('\n')
    if p.wait():
        sys.exit('git ' + ' '.join(args[:2]) + ' failed')


ref = a.ref or ('origin/main' if subprocess.run(['git', '-C', a.repo, 'rev-parse', '--verify', '-q', 'origin/main'], capture_output=True).returncode == 0 else 'HEAD')
sha = git('rev-parse', ref).decode().strip()
print('ref', ref, sha)
ACT_DIRS = ['zakon', 'pravilnik', 'uputstvo', 'poslovnik', 'pravilo', 'odluka', 'naredba', 'instrukcija', 'kodeks', 'statut', 'uredba']


def tree(*paths):
    """(oid, path) of every blob under the paths, from the tree objects (no blob is needed)."""
    out = []
    for line in git('ls-tree', '-r', ref, '--', *paths).decode('utf-8').splitlines():
        meta, path = line.split('\t', 1)
        out.append((meta.split()[2], path))
    return out


# ------------------------------------------------------------------ 0. the blobs this build reads
SG = [x for x in tree('sluzbeni-glasnik') if x[1].endswith('/README.md')]
BILLS = [x for x in tree('bill') if x[1].endswith('/record.json')]
SUD = [x for x in tree('sudska-praksa/sud-bih') if x[1].endswith('/README.md')]
ACTF = [x for x in tree(*ACT_DIRS) if x[1].rsplit('/', 1)[-1] in ('uvod.md', 'tekst.md')]
FIXED = [x for x in tree('constitution', 'criminal-code/README.md', 'registry/data/acts.json', 'data/laws.csv')]
want = [o for o, _ in SG + BILLS + SUD + ACTF + FIXED]
have = git('cat-file', '--batch-check=%(objectname) %(objecttype)', inp=('\n'.join(want) + '\n').encode()).decode().splitlines()
missing = [ln.split()[0] for ln in have if ln.endswith('missing')]
print('blobs needed', len(want), 'missing', len(missing))
for i in range(0, len(missing), 5000):
    subprocess.run(['git', '-C', a.repo, '-c', 'fetch.negotiationAlgorithm=noop', 'fetch', '-q', 'origin', '--no-tags', '--no-write-fetch-head',
                    '--recurse-submodules=no', '--filter=blob:none', '--stdin'], input=('\n'.join(missing[i:i + 5000]) + '\n').encode(), check=True)


class Blobs:
    """git cat-file --batch, one blob at a time."""
    def __init__(self):
        self.p = subprocess.Popen(['git', '-C', a.repo, 'cat-file', '--batch'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, env=ENV)

    def get(self, oid):
        self.p.stdin.write((oid + '\n').encode()); self.p.stdin.flush()
        hdr = self.p.stdout.readline().split()
        if len(hdr) < 3 or hdr[1] == b'missing':
            sys.exit('blob missing: ' + oid)
        body = self.p.stdout.read(int(hdr[2])); self.p.stdout.read(1)
        return body.decode('utf-8', 'replace')


BL = Blobs()

# ------------------------------------------------------------------ 1. Constitutional Court decisions (commit authors)
with open(os.path.join(B, 'cc.tsv'), 'w', encoding='utf-8', newline='') as f:
    n = 0
    for line in stream('log', ref, '--format=%an%x09%ae%x09%(trailers:key=In-force,valueonly,separator=)', '--', 'caselaw'):
        f.write(line + '\n'); n += 1
print('cc commits', n)

# ------------------------------------------------------------------ 2. act commits with trailers and files
rows, cur = [], None
FMT = '@@C%x09%H%x09%an%x09%ae%x09%(trailers:key=Kind,valueonly,separator=)%x09%(trailers:key=Enacted,valueonly,separator=)%x09' \
      '%(trailers:key=Published,valueonly,separator=)%x09%(trailers:key=In-force,valueonly,separator=)%x09%(trailers:key=Provisions,valueonly,separator=)'
for line in stream('log', ref, '--no-renames', '--format=' + FMT, '--name-status', '--', *ACT_DIRS):
    if line.startswith('@@C\t'):
        if cur: rows.append(cur)
        f = line.split('\t')
        cur = {'h': f[1], 'an': f[2], 'ae': f[3], 'kind': f[4], 'enacted': f[5], 'pub': f[6], 'inf': f[7], 'prov': f[8], 'files': []}
    elif line.strip() and cur is not None:
        cur['files'].append(line)
if cur: rows.append(cur)
json.dump(rows, open(os.path.join(B, 'acts.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('act commits', len(rows))

# ------------------------------------------------------------------ 3. the Gazette index
with open(os.path.join(B, 'sg.tsv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter='\t')
    w.writerow(['year', 'issue', 'item', 'title', 'issuer', 'label', 'date', 'of'])
    for oid, path in SG:
        body = BL.get(oid)
        _, y, iss, it, _ = path.split('/')
        t = re.search(r'^Naslov: (.*)$', body, re.M)
        d = re.search(r'^Donosilac: (.*)$', body, re.M)
        g = re.search(r'broj (\S+) \(([\d.]+)\)\s*,\s*akt (\d+) od (\d+)', body)
        w.writerow([y, iss, it, t.group(1).strip() if t else '', d.group(1).strip().rstrip('.') if d else '',
                    g.group(1) if g else '', g.group(2) if g else '', g.group(4) if g else ''])
print('gazette items', len(SG))

# ------------------------------------------------------------------ 4. bills and Court of BiH case pages
json.dump([json.loads(BL.get(o)) for o, _ in BILLS], open(os.path.join(B, 'bills.json'), 'w', encoding='utf-8'), ensure_ascii=False)
sud = []
for oid, path in SUD:
    body = BL.get(oid)
    rec = {'path': path, 'case': body.split('\n')[0].lstrip('# ').strip()}
    for m in re.finditer(r'^- ([^:\n]+?)\s*:\s*(.*)$', body, re.M):
        rec.setdefault(m.group(1).strip(), m.group(2).strip())
    sud.append(rec)
json.dump(sud, open(os.path.join(B, 'sud.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('bills', len(BILLS), 'court of BiH cases', len(sud))

# ------------------------------------------------------------------ 5. act texts: preamble, citations, sessions, excise
CIT = re.compile(r'((?:Izborn\w+ zakon\w*|Krivičn\w+ zakon\w*|Zakon\w*)(?: [^"“”„(]{0,160}?)?)\s*\(\s*["“”„]{1,2}\s*Službeni glasnik BiH\s*["“”]{1,2}\s*,?\s*'
                 r'(?:br\.|broj|brojevi)\s*:?\s*([0-9/,\si\-–.]+?)\)', re.I)
texts = {}
for oid, path in ACTF:
    d, name = '/'.join(path.split('/')[:3]), path.rsplit('/', 1)[-1]
    body = re.sub(r'\s+', ' ', BL.get(oid))
    rec = texts.setdefault(d, {'src': None, 'head': '', 'cites': []})
    if name == 'uvod.md' or not rec['src']:          # the preamble, when the act has one, else the single text
        rec['src'], rec['head'] = name, body[:3000]
    for m in CIT.finditer(body):
        nums = re.findall(r'(\d{1,3})\s*/\s*(\d{2})\b', m.group(2))
        if nums:   # name, Gazette numbers, and the words just before the name (to tell "Pravilnik o primjeni Zakona ..." apart)
            rec['cites'].append([m.group(1).strip()[:200], ['%d/%s' % (int(x), yy) for x, yy in nums], body[max(0, m.start() - 70):m.start()]])
    if re.search(r'MINIMALNE AKCIZE NA CIGARETE|ODLUKA VISOKOG PREDSTAVNIKA', body[:900]):
        rec['long'] = body[:14000]
json.dump(texts, open(os.path.join(B, 'texts.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('act texts', len(texts), 'citations', sum(len(v['cites']) for v in texts.values()))

# ------------------------------------------------------------------ 6. fixed files
for oid, path in FIXED:
    out = os.path.join(B, 'repo', *path.split('/'))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8', newline='\n').write(BL.get(oid))
BL.p.stdin.close(); BL.p.wait()

# ------------------------------------------------------------------ 7. prep + build
env = dict(os.environ, HEAD_SHA=sha)
subprocess.run([sys.executable, '-X', 'utf8', os.path.join(HERE, 'prep.py'), B], check=True, env=env)
subprocess.run([sys.executable, '-X', 'utf8', os.path.join(HERE, 'build.py'), os.path.join(B, 'data.json'), os.path.abspath(a.out)], check=True)
