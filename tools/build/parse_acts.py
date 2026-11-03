"""Bosnia and Herzegovina (state level): laws of the Parliamentary Assembly as published in Službeni glasnik BiH.

Reads a local copy of the Official Gazette publisher's act index (sluzbenilist.ba search results: gazette issue,
issue date, issuer, title, act link) and of each act's text page (the document part of /page/akt/<id>, Bosnian), and
writes corpus.d parts (SCHEMA.md in scripts/gitlaw_common). Deterministic: the same inputs give the same bytes.

    python -X utf8 parse_acts.py --src <folder with index.jsonl, fetched.jsonl, raw/> [--report holds.jsonl]

Input formats: index.jsonl rows {"series", "issue", "yy", "date" (issue date), "issuer", "title", "akt"};
fetched.jsonl rows {"akt", "sha256", "retrieved"}; raw/<sha1(akt)[:2]>/<sha1(akt)>.html.gz = the page's document part.

What becomes an act here: a law the Parliamentary Assembly adopted (issuer PARLAMENTARNA SKUPŠTINA BOSNE I
HERCEGOVINE, title beginning ZAKON), as published, one version, in force on the day its own final article names,
counted from the gazette issue date ("osmog dana od dana objavljivanja" = issue date + 8). The enacting formula above
the title is kept as the preamble; the signatures below the text are not part of the law and are cut.

An act is held back, not published (the reason is written to the report), when:
- a later act in the gazette index is titled as amending, repealing or correcting it (ZAKON O IZMJENI/IZMJENAMA/
  DOPUNI/DOPUNAMA ... ZAKONA O <its subject>, ZAKON O PRESTANKU VAŽENJA ..., ISPRAVKA ...);
- a later text held cites it by name with its gazette number followed by later issues (its amendments), or a
  Constitutional Court decision that finds provisions unconstitutional or strikes them cites it; for an amending law,
  a later law or such a court decision citing the amending law itself, or a correction naming it;
- its title is not of the form ZAKON O ... (codes such as KRIVIČNI ZAKON are amended under other names);
- its own final article does not name a day this parser can read;
- its articles do not split cleanly (none, a number twice, numbers not consecutive, an empty article).
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import html
import json
import re
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARTS = HERE / "corpus.d"
AKT_URL = "https://www.sluzbenilist.ba/page/akt/{akt}"
ISSUER = "PARLAMENTARNA SKUPŠTINA BOSNE I HERCEGOVINE"
MONTHS = {m: i for i, m in enumerate(["januara", "februara", "marta", "aprila", "maja", "juna", "jula", "augusta",
                                       "septembra", "oktobra", "novembra", "decembra"], 1)}
MONTHS.update({"avgusta": 8, "agusta": 8})
ORD = {"prvog": 1, "drugog": 2, "trećeg": 3, "četvrtog": 4, "petog": 5, "šestog": 6, "sedmog": 7, "osmog": 8,
       "devetog": 9, "desetog": 10, "petnaestog": 15, "dvadesetog": 20, "tridesetog": 30, "narednog": 1, "sljedećeg": 1}
ART = re.compile(r"^Član\s+(\d+)\s*([a-z])?\s*\.?$")
HEADING = re.compile(r"^(?:POGLAVLJE|Poglavlje|DIO|Dio|GLAVA|Glava|ODJELJAK|Odjeljak|ODSJEK|Odsjek|[IVXLC]+\s*[.\-])")
# Title word -> (slug kind, law kind for the commit). Laws come from the Parliamentary Assembly; rulebooks,
# instructions, rules of procedure and rules from the institutions that issue them.
KINDS = {"ZAKON": ("zakon", "law"), "PRAVILNIK": ("pravilnik", "decree"), "UPUTSTVO": ("uputstvo", "decree"),
         "POSLOVNIK": ("poslovnik", "decree"), "PRAVILO": ("pravilo", "decree")}
KIND_WORDS = "ZAKON|PRAVILNIK|UPUTSTVO|POSLOVNIK|PRAVILO"
STEMS = ("pravilnik", "uputstv", "poslovnik", "pravil", "zakon")  # longest first: "pravilnik" before "pravil"
AMENDS = re.compile(r"^(?:(?:" + KIND_WORDS + r")\s+O\s+(?:IZMJEN\w*|DOPUN\w*)(?:\s+I\s+(?:IZMJEN\w*|DOPUN\w*))*\s+|"
                    r"(?:" + KIND_WORDS + r")\s+O\s+PRESTANKU\s+(?:VAŽENJA|VAŽNOSTI)\s+|ISPRAVK\w*\s+|"
                    r"(?:IZMJEN\w*|DOPUN\w*)(?:\s+I\s+(?:IZMJEN\w*|DOPUN\w*))*\s+)(.+)$")
TARGET = re.compile(r"\b(ZAKONA?|PRAVILNIKA?|UPUTSTVA|UPUTSTVO|POSLOVNIKA?|PRAVILA|PRAVILO)\s+O\s+")
CITE = re.compile(r"(Pravilnik|Uputstv|Poslovnik|Pravil|Zakon)\w*\s+o\s+([^()\"]{3,250}?)\s*\(\s*[\"„“]?Službeni\s+glasnik\s+BiH"
                  r"[\"“”]?\s*,?\s*(?:br\.|broj)\s*([0-9/,.\s i]+)\)")
IN_FORCE = re.compile(r"(?:Ovaj|Ovo|Ova|Taj)\s+(?:[Zz]akon|[Pp]ravilnik|[Uu]putstvo|[Pp]oslovnik|[Pp]ravilo)\s+stupa\s+na\s+snagu\s+([^.]*)")


class Hold(Exception):
    pass


def norm(s: str) -> str:
    s = s.replace(" ", " ").replace("­", "").replace("\t", " ")
    s = s.replace("–", "-").replace("—", "-").replace("„", '"').replace("“", '"').replace("”", '"')
    s = s.replace("’", "'").replace("‘", "'")
    return re.sub(r"[ \r\n\f\v]+", " ", s).strip()


def subject(s: str) -> str:
    s = norm(s).lower()
    s = re.sub(r"\s+", " ", s).strip(" .,;:")
    return s[:80]


def stem(word: str) -> str:
    w = word.lower()
    return next((x for x in STEMS if w.startswith(x)), w)


def own_subject(title: str) -> str | None:
    m = re.match(r"^(\w+)\s+O\s+(.+)$", norm(title).upper())
    return f"{stem(m.group(1))}:{subject(m.group(2))}" if m and m.group(1) in KINDS else None


def target_subject(title: str) -> str | None:
    m = AMENDS.match(norm(title).upper())
    if not m:
        return None
    t = TARGET.search(m.group(1))
    return f"{stem(t.group(1))}:{subject(m.group(1)[t.end():])}" if t else None


def similar(a: str, b: str, n: int) -> bool:
    """Same kind of act, and one subject starts with the first n characters of the other."""
    ka, sa = a.split(":", 1)
    kb, sb = b.split(":", 1)
    return ka == kb and (sa.startswith(sb[:n]) or sb.startswith(sa[:n]))


def issues_in(s: str, default_yy: str | None = None) -> list[tuple[int, int]]:
    out = []
    for n, yy in re.findall(r"(\d{1,3})\s*/\s*(\d{2,4})", s):
        y = int(yy)
        y = y + (2000 if y < 50 else 1900) if y < 100 else y
        out.append((int(n), y))
    return out


def lines_of(fragment: str) -> list[str]:
    fragment = re.sub(r"<!--.*?-->", "", fragment, flags=re.S)
    fragment = re.sub(r"<(style|script|head|title)\b.*?</\1>", "", fragment, flags=re.S | re.I)
    fragment = re.sub(r"</t[dh]>", " | ", fragment, flags=re.I)
    fragment = re.sub(r"<br\s*/?>|</?(?:p|div|tr|li|ul|ol|table|h\d|body|html)\b[^>]*>", "\n", fragment, flags=re.I)
    t = html.unescape(re.sub(r"<[^>]+>", "", fragment))
    out = []
    for line in t.split("\n"):
        line = norm(line)
        line = re.sub(r"(?:\s*\|\s*)+$", "", line).strip()
        line = re.sub(r"^(?:\|\s*)+", "", line).strip()
        if line and not re.fullmatch(r"[|\s]+", line):
            out.append(line)
    return out


def split(page: str, word: str = "ZAKON") -> tuple[dict, str, str | None]:
    """(units, title, adoption day) from the document part of the act page."""
    end = page.find('<div class="col-md-3')
    main, tail = (page[:end], page[end:]) if end > 0 else (page, "")
    main = re.sub(r'<div class="row" style="display: none">.*?</div>\s*</div>\s*</div>', "", main, count=1, flags=re.S)
    main = re.sub(r"^\s*<h1>.*?</h1>", "", main, count=1, flags=re.S)
    # Structural blocks: <p class="text-center"> ... </p>, each a list of its <strong> parts.
    pieces: list[tuple[str, object]] = []
    pos = 0
    for m in re.finditer(r'<p class="text-center">(.*?)</p>', main, flags=re.S):
        pieces.append(("text", main[pos:m.start()]))
        strongs = [norm(html.unescape(re.sub(r"<[^>]+>", "", s))) for s in re.findall(r"<strong>(.*?)</strong>", m.group(1), flags=re.S)]
        pieces.append(("center", [s for s in strongs if s]))
        pos = m.end()
    pieces.append(("text", main[pos:]))
    title_parts: list[str] = []
    pre: list[str] = []
    units: dict[str, dict] = {}
    order: list[str] = []
    pending: list[str] = []
    cur = None
    for kind, val in pieces:
        if kind == "text":
            ls = lines_of(val)
            if not ls:
                continue
            if cur is None:
                if title_parts:
                    if pending:
                        raise Hold("text_before_first_article")
                    raise Hold("text_before_first_article")
                pre.extend(ls)
            else:
                if pending:
                    units[cur]["lines"].extend(pending)
                    pending.clear()
                units[cur]["lines"].extend(ls)
            continue
        strongs = val
        if not strongs:
            continue
        if cur is None and not title_parts and strongs[0].upper().startswith(word):
            title_parts = strongs
            continue
        m = ART.match(strongs[0])
        if m and title_parts:
            key = f"art-{int(m.group(1)):03d}" + (f"-{m.group(2)}" if m.group(2) else "")
            if key in units:
                raise Hold(f"duplicate_unit:{key}")
            for j, h in enumerate(pending, 1):
                hk = f"{cur}-zz-heading-{j}" if cur else f"0-heading-{j}"
                units[hk] = {"label": h, "kind": "heading", "lines": [f"# {h}"]}
                order.append(hk)
            pending.clear()
            label = f"Član {m.group(1)}{m.group(2) or ''}."
            units[key] = {"label": label, "kind": "art", "lines": [f"# {label}"] + strongs[1:]}
            order.append(key)
            cur = key
            continue
        joined = " ".join(strongs)
        if not title_parts:
            pre.append(joined)
        elif HEADING.match(joined) or (joined == joined.upper() and re.search(r"[A-ZČĆŽŠĐ]{3}", joined)):
            pending.append(joined)
        elif cur is not None:
            units[cur]["lines"].append(joined)  # a centred line inside an article (the publisher's markup)
        else:
            pending.append(joined)
    if pending:
        if cur is None:
            raise Hold("no_articles")
        units[cur]["lines"].extend(pending)
    if not title_parts:
        raise Hold("no_title")
    title = norm(" ".join(title_parts))
    out = {}
    if pre:
        out["uvod"] = {"label": "Uvod", "kind": "preamble", "text": "\n".join(pre) + "\n"}
    for k in order:
        out[k] = {"label": units[k]["label"], "kind": units[k]["kind"], "text": "\n".join(units[k]["lines"]) + "\n"}
    arts = [k for k in out if out[k]["kind"] == "art"]
    if not arts:
        raise Hold("no_articles")
    nums = [int(k[4:7]) for k in arts if len(k) == 7]
    if nums != list(range(1, len(nums) + 1)):
        raise Hold("article_numbers_not_consecutive")
    for k in arts:
        if out[k]["text"].count("\n") < 2:
            raise Hold(f"empty_article:{k}")
    tail_t = " ".join(lines_of(tail))
    m = re.search(r"(\d{1,2})\.\s*(" + "|".join(MONTHS) + r")\s+(\d{4})\.?\s*godine", tail_t)
    adopted = date(int(m.group(3)), MONTHS[m.group(2)], int(m.group(1))).isoformat() if m else None
    return out, title, adopted


def in_force(units: dict, published: str, adopted: str | None = None) -> tuple[str, str]:
    arts = [u["text"].replace("\n", " ") for k, u in units.items() if u["kind"] == "art"]
    text = " ".join(arts)
    # This law's own clause: outside quotation marks (provisions quoted into another act are not its own), or in
    # its last article where the quotation marks of earlier articles are unbalanced.
    clauses = [m.group(1) for m in IN_FORCE.finditer(text) if text.count('"', 0, m.start()) % 2 == 0]
    last = [m.group(1) for m in IN_FORCE.finditer(arts[-1]) if not arts[-1][:m.start()].rstrip().endswith('"')]
    if not clauses and last:
        clauses = last
    if not clauses:
        raise Hold("in_force_clause_missing")
    c = clauses[-1].strip()
    # matching only: some texts mix Cyrillic ј into Latin lj/nj, and say "objave" for "objavljivanja"
    c = c.replace("lј", "lj").replace("nј", "nj").replace("Ј", "J")
    c = re.sub(r"\bobjave\b", "objavljivanja", c)
    c = re.sub(r"^osam\s+dana", "osmog dana", c)
    p = date.fromisoformat(published)
    if re.match(r"^(?:danom|na\s+dan|s\s+danom|sa\s+danom)\s+(?:njegovog\s+)?donošenja", c):
        # in force on the day it was made: that day comes from the signature block, and must not follow publication
        if adopted and adopted <= published:
            return adopted, "adoption"
        raise Hold("in_force_on_adoption_day_unknown")
    if re.match(r"^(?:danom|na\s+dan|s\s+danom|sa\s+danom)\s+(?:njegovog\s+|njegova\s+)?objavljivanja", c):
        return published, "publication"
    m = re.match(r"^(" + "|".join(ORD) + r")a?\s+dana\s+(?:od\s+dana|nakon|po|poslije)\s+(?:njegovog\s+|njegova\s+)?objavljivanja", c)
    if m:
        return (p + timedelta(days=ORD[m.group(1)])).isoformat(), "days"
    m = re.match(r"^(\d{1,3})\s*\.?\s*-?\s*(?:t?oga?|ga)?\s+dana\s+(?:od\s+dana|nakon|po|poslije)\s+(?:njegovog\s+)?objavljivanja", c)
    if m:
        return (p + timedelta(days=int(m.group(1)))).isoformat(), "days"
    m = re.match(r"^(?:dana\s+|s\s+|sa\s+)?(\d{1,2})\.\s*(" + "|".join(MONTHS) + r")\s+(\d{4})", c) or \
        re.match(r"^(?:dana\s+|s\s+|sa\s+)?(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})", c)
    if m:
        mo = MONTHS.get(m.group(2)) or int(m.group(2))
        return date(int(m.group(3)), mo, int(m.group(1))).isoformat(), "date"
    raise Hold("in_force_unreadable:" + c[:100])


def raw_path(src: Path, akt: str) -> Path:
    h = hashlib.sha1(akt.encode()).hexdigest()
    return src / "raw" / h[:2] / f"{h}.html.gz"


COUNTRY = {
    "code": "BA", "name": "Bosnia and Herzegovina", "slug": "bosnia-and-herzegovina", "lang": "bs",
    "tz": "Europe/Sarajevo", "future_branch": "future",
    "publisher": {"name": "JP NIO Službeni list Bosne i Hercegovine", "email": "sllist@sllist.invalid"},
    "default_in_force_rule": {
        "text": "Each law of Bosnia and Herzegovina names its own day in its final article, almost always the eighth "
                "day after its publication in Službeni glasnik BiH; that day is used.",
        "source": "https://www.sluzbenilist.ba/"},
    "licence_note": "Official texts of laws are not protected by copyright in Bosnia and Herzegovina. Text from "
                    "Službeni glasnik BiH, as shown by JP NIO Službeni list BiH (sluzbenilist.ba)."}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--report")
    ap.add_argument("--out", help="folder for the parts (default corpus.d beside this script)")
    ap.add_argument("--cache", help="file to keep each text's citations in between runs (same text and parser = same)")
    ap.add_argument("--rejects", help="JSON {akt: reason}: acts held back by hand or by a failed read-back check")
    a = ap.parse_args()
    src = Path(a.src)
    rows = []
    for line in (src / "index.jsonl").read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    fetched = {}
    for line in (src / "fetched.jsonl").read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        fetched[r["akt"]] = r
    me = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    cache, new_cache = {}, {}
    if a.cache and Path(a.cache).exists():
        try:
            c = json.loads(gzip.decompress(Path(a.cache).read_bytes()).decode("utf-8"))
            cache = c["entries"] if c.get("parser") == me else {}
        except Exception:
            cache = {}
    rejects = json.loads(Path(a.rejects).read_text(encoding="utf-8")) if a.rejects and Path(a.rejects).exists() else {}
    rows = [r for r in rows if r.get("series") == "Službeni glasnik BiH"]
    # Later titles that amend, repeal or correct a subject.
    named: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        ts = target_subject(r["title"])
        if ts:
            named[ts].append(r["date"])
    # Citations of (subject, issue) in every text held, with the citing act's date and whether it is a court decision.
    cites: dict[tuple[str, int, int], list[tuple[str, bool]]] = defaultdict(list)
    texts: dict[str, str] = {}
    for r in rows:
        if not r.get("akt") or r["akt"] not in fetched:
            continue
        f = raw_path(src, r["akt"])
        if not f.exists():
            continue
        texts[r["akt"]] = None  # read again only for the acts judged below
        ck = f"{r['akt']}:{fetched[r['akt']].get('sha256')}"
        if ck in cache:
            new_cache[ck] = cache[ck]
            for key, n_, y_, *rest in cache[ck]:
                cites[(key, n_, y_)].append((r["date"], *rest))
            continue
        found = []
        page = gzip.decompress(f.read_bytes()).decode("utf-8")
        flat = norm(html.unescape(re.sub(r"<[^>]+>", " ", page)))
        court = "USTAVNI SUD" in r["issuer"].upper()
        # A court decision that finds a provision unconstitutional or strikes it changes the text it names.
        operative = flat[:flat.find(" I. Uvod")] if " I. Uvod" in flat else flat[:4000]  # the ruling, not its reasons
        # Only abstract review (case "U ..."): appeals ("AP ...") quash court rulings, never legislation.
        struck = court and bool(re.search(r"predmetu\s+broj\s+U[\s-]*\d", operative)) and bool(re.search(r"Utvrđuje se da[^.]{0,600}?\bni(?:je|su)\s+u\s+skladu|\b(?:U|u)kida(?:ju)? se\b|"
                                          r"prestaj(?:e|u) (?:da )?važi", operative))
        kind = "court" if court else "law" if r["title"].upper().startswith("ZAKON") else "other"
        for m in CITE.finditer(flat):
            lst = issues_in(m.group(3))
            for k, iss in enumerate(lst):
                # (citing day, citing kind, citing act, court struck something, issues listed after this one)
                found.append([f"{stem(m.group(1))}:{subject(m.group(2))}", iss[0], iss[1], kind, r["akt"], struck, len(lst) - k - 1])
        new_cache[ck] = found
        for key, n_, y_, *rest in found:
            cites[(key, n_, y_)].append((r["date"], *rest))
    parts: dict[tuple, dict] = defaultdict(lambda: {"laws": {}, "acts": []})
    holds = []
    def first_word(r):
        return (norm(r["title"]).upper().split() or [""])[0]

    laws = [r for r in rows if r.get("akt") and first_word(r) in KINDS and "USTAVNI SUD" not in r["issuer"].upper()
            and (first_word(r) != "ZAKON" or r["issuer"].upper().startswith(ISSUER))]
    # Texts that can amend or strike a law (laws and Constitutional Court decisions): an act is judged only when every
    # such text published on or after its day is held, so a citation not yet read can never be missed.
    missing = defaultdict(list)
    for r in rows:
        if r.get("akt") and r["akt"] not in texts:
            for w in KINDS:
                if w != "ZAKON" or first_word(r) == "ZAKON" or "USTAVNI SUD" in r["issuer"].upper():
                    missing[w].append(r["date"])
    complete_from = {w: max(missing[w], default="0000") for w in KINDS}
    missing_days = missing["ZAKON"]
    seen_slugs = set()
    for r in sorted(laws, key=lambda x: (x["date"], x["issue"], x["akt"])):
        title = norm(r["title"])
        pub = r["date"]
        year = int(pub[:4])
        own = (r["issue"], 2000 + int(r["yy"]) if len(r["yy"]) == 2 else int(r["yy"]))
        try:
            if r["akt"] in rejects:
                raise Hold("rejected:" + str(rejects[r["akt"]])[:200])
            if r["akt"] not in texts:
                raise Hold("text_not_fetched")
            word = first_word(r)
            kslug, lkind = KINDS[word]
            if pub <= complete_from[word]:
                raise Hold("awaiting_later_texts:" + complete_from[word])
            amending = target_subject(title) is not None
            subj = own_subject(title)
            if not amending and not subj:
                raise Hold("title_form")
            if amending:
                ts = target_subject(title)
                corr = [x for x in rows if x["date"] >= pub and x is not r and x["title"].upper().startswith("ISPRAVK")
                        and subject(x["title"]).find(re.sub(r"^\w+ o ", "", subject(title))[:60]) >= 0]
                if corr:
                    raise Hold("correction_named")
                # A later text citing this amending law itself by name and issue (not the principal law's list).
                tk, tsub = ts.split(":", 1)
                own_cites = [c for (s, n, y), lst in cites.items() if (n, y) == own and s.split(":", 1)[0] == stem(word)
                             and re.match(r"^(?:izmjen|dopun)", s.split(":", 1)[1]) and tsub[:40] in s for c in lst if c[2] != r["akt"] and c[0] >= pub
                             and (c[1] == "law" or (c[1] == "court" and c[3]))]
                if own_cites:
                    raise Hold("amending_law_cited_later:" + ",".join(sorted({c[0] for c in own_cites})[:3]))
            else:
                later = [d for d in named.get(subj, []) if d >= pub]
                later += [d for s, lst in named.items() if s != subj and similar(s, subj, 50) for d in lst if d >= pub]
                if later:
                    raise Hold("named_as_amended:" + ",".join(sorted(set(later))[:3]))
                # A later citation that lists issues after this one names its amendments; a court decision that
                # strikes provisions changes it. A citation of this issue alone (a regulation's legal basis) does not.
                by_cite = [c for (s, n, y), lst in cites.items() if (n, y) == own and similar(s, subj, 40)
                           for c in lst if c[2] != r["akt"] and c[0] >= pub and (c[4] > 0 or (c[1] == "court" and c[3]))]
                if by_cite:
                    raise Hold("cited_later:" + ",".join(sorted({c[0] for c in by_cite})[:3]))
            page = gzip.decompress(raw_path(src, r["akt"]).read_bytes()).decode("utf-8")
            units, text_title, adopted = split(page, word)
            if subject(text_title).replace(" ", "") != subject(title).replace(" ", ""):
                raise Hold("title_mismatch:" + text_title[:100])
            day, how = in_force(units, pub, adopted)
            if adopted and not (adopted <= pub <= (date.fromisoformat(adopted) + timedelta(days=90)).isoformat()):
                raise Hold(f"adoption_day_inconsistent:{adopted}")
        except Hold as h:
            holds.append({"akt": r["akt"], "sg": f"{r['issue']}/{r['yy']}", "date": pub, "title": title[:160], "reason": str(h)})
            continue
        pk = (40, "zakoni") if kslug == "zakon" else (50, kslug)
        slug = f"{kslug}-{year}-sg{r['issue']:03d}-{hashlib.sha1(r['akt'].encode()).hexdigest()[:6]}"
        if slug in seen_slugs:
            holds.append({"akt": r["akt"], "sg": f"{r['issue']}/{r['yy']}", "title": title[:160], "reason": "slug_collision"})
            continue
        seen_slugs.add(slug)
        nice = title[0] + title[1:].lower() if title.isupper() else title
        nice = re.sub(r"\bbosne i hercegovine\b", "Bosne i Hercegovine", nice)
        label = f'{nice} ("Službeni glasnik BiH", br. {r["issue"]}/{r["yy"]})'
        url = AKT_URL.format(akt=r["akt"])
        note = None
        if re.search(r"primjenj\w+\s+(?:će\s+se\s+)?(?:se\s+)?(?:od|počev)", " ".join(u["text"] for u in units.values() if u["kind"] == "art")[-600:]):
            note = "Njegov završni član određuje i poseban dan primjene."
        parts[(pk, year)]["laws"][slug] = {"label": label, "title": nice, "kind": lkind, "enacted": adopted, "published": pub,
                                     "url": url, "temporary_until": None, "restores": None, "note": None}
        parts[(pk, year)]["acts"].append({
            "slug": slug, "short": nice, "title": nice, "url": url, "first_law": slug, "earlier_laws": [],
            "versions": [{"from": day, "source_url": url, "sha256": fetched[r["akt"]]["sha256"], "units": units,
                          "credits": {}, **({"note": note} if note else {})}]})
        parts[(pk, year)].setdefault("_retrieved", set()).add(fetched[r["akt"]].get("retrieved"))
    out_dir = Path(a.out) if a.out else PARTS
    out_dir.mkdir(exist_ok=True)

    def write(f: Path, p: dict, publish_line: str):
        body = json.dumps(p, ensure_ascii=False, indent=1) + "\n"
        if not f.exists() or f.read_text(encoding="utf-8") != body:
            tmp = f.with_suffix(".tmp")
            tmp.write_text(body, encoding="utf-8", newline="\n")
            tmp.replace(f)
        pf = f.with_suffix(".PUBLISH")
        if not pf.exists():
            pf.write_text(publish_line + "\n", encoding="utf-8", newline="\n")

    write(out_dir / "00-drzava.json", {"country": COUNTRY, "acts": []},
          "Country metadata for the state-level laws parsed by parse_acts.py.")
    written = []
    for pk, year in sorted(parts):
        p = parts[(pk, year)]
        p["acts"].sort(key=lambda x: x["slug"])
        ret = p.pop("_retrieved", set())
        p["sources"] = [{"name": "Službeni glasnik BiH (JP NIO Službeni list BiH, sluzbenilist.ba)",
                         "url": "https://www.sluzbenilist.ba/", "retrieved": max(x for x in ret if x),
                         "licence": "Official texts of laws; not protected by copyright",
                         "notes": "Gazette issue, issue date, issuer and title from the publisher's search; each act's "
                                  "Bosnian text from its page."}]
        p["decisions"] = [
            "A law of the Parliamentary Assembly is published here as published in Službeni glasnik BiH, in its "
            "Bosnian text; the enacting formula is kept as the preamble, the signatures below the text are cut.",
            "Its one version takes effect on the day its own final article names, counted from the gazette issue date "
            "(\"osmog dana od dana objavljivanja\" = issue date + 8); a separate day of application is only noted.",
            "A law is published only when no later act in the gazette index is titled as amending, repealing or "
            "correcting it and no later text held cites it by name and gazette number; an amending law only when no "
            "correction names it and no Constitutional Court decision cites it.",
            "Articles follow the publisher's centred article headings (Član N.); a centred line directly under one is "
            "its caption."]
        p["ai_use"] = ["none"]
        f = out_dir / f"{pk[0]}-{pk[1]}-{year}.json"
        write(f, p, "Parsed from Službeni glasnik BiH (sluzbenilist.ba) texts; one version, as published; in-force day "
                    "from the law's own final article and the gazette issue date; held back: laws named as amended or "
                    "cited later (parse_acts.py).")
        written.append((f.name, len(p["acts"])))
    # Parts of years that no longer hold any act (all held back now) are removed, so a stale part is never read.
    keep = {n for n, _ in written}
    for old in [*out_dir.glob("40-zakoni-*.json"), *out_dir.glob("50-*.json")]:
        if old.name not in keep:
            old.unlink()
            old.with_suffix(".PUBLISH").unlink(missing_ok=True)
    if a.cache:
        tmp = Path(a.cache + ".tmp")
        tmp.write_bytes(gzip.compress(json.dumps({"parser": me, "entries": new_cache}, ensure_ascii=False).encode("utf-8"), 1))
        tmp.replace(a.cache)
    if a.report:
        Path(a.report).write_text("".join(json.dumps(h, ensure_ascii=False) + "\n" for h in holds), encoding="utf-8")
    print(json.dumps({"texts_missing_laws_or_court": len(missing_days)}), file=__import__("sys").stderr)
    reasons = defaultdict(int)
    for h in holds:
        reasons[h["reason"].split(":")[0]] += 1
    print(json.dumps({"laws_seen": len(laws), "published": sum(n for _, n in written), "held": len(holds),
                      "held_by_reason": dict(reasons), "parts": written}, ensure_ascii=False))


if __name__ == "__main__":
    main()
