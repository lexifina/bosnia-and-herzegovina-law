"""Bosnia and Herzegovina (state level): laws of the Parliamentary Assembly as published in Službeni glasnik BiH.

Reads a local copy of the Official Gazette publisher's act index (sluzbenilist.ba search results: gazette issue,
issue date, issuer, title, act link) and of each act's text page (the document part of /page/akt/<id>, Bosnian), and
writes corpus.d parts (SCHEMA.md in scripts/gitlaw_common). Deterministic: the same inputs give the same bytes.

    python -X utf8 parse_acts.py --src <folder with index.jsonl, fetched.jsonl, raw/> [--report holds.jsonl]

Input formats: index.jsonl rows {"series", "issue", "yy", "date" (issue date), "issuer", "title", "akt"};
fetched.jsonl rows {"akt", "sha256", "retrieved"}; raw/<sha1(akt)[:2]>/<sha1(akt)>.html.gz = the page's document part;
optional unfetchable.json {akt: reason}: act links whose page the publisher does not serve (a server error on every
attempt), so their text can never be read.

What becomes an act here: a law the Parliamentary Assembly adopted (issuer PARLAMENTARNA SKUPŠTINA BOSNE I
HERCEGOVINE, title beginning ZAKON), as published, one version, in force on the day its own final article names,
counted from the gazette issue date ("osmog dana od dana objavljivanja" = issue date + 8). The enacting formula above
the title is kept as the preamble; the signatures below the text are not part of the law and are cut.

An act is held back, not published (the reason is written to the report), when:
- a later act in the gazette index is titled as amending, repealing or correcting it (ZAKON O IZMJENI/IZMJENAMA/
  DOPUNI/DOPUNAMA ... ZAKONA O <its subject>, ZAKON O PRESTANKU VAŽENJA ..., ISPRAVKA ...);
  (a title only similar to its own does not count when that amending text's citation of its target names another
  act's gazette issue and never this one);
- a later text held cites it by name with its gazette number followed by later issues (its amendments), or in a
  sentence saying it ceases to be valid ("prestaje važiti ..."), or a Constitutional Court decision that finds
  provisions unconstitutional or strikes them cites it; for an amending law, a later law or such a court decision
  citing the amending law itself, or a correction naming it (unless the correction names another gazette issue);
- its title is not of the form ZAKON O ... (codes such as KRIVIČNI ZAKON are amended under other names);
- its own final article does not name a day this parser can read;
- its articles do not split cleanly (none, a number twice, numbers not consecutive, an empty article).
An act is judged only when every text that could change it and that the publisher serves is held; for a text listed
as unfetchable only its title is checked.

A repeal is published, not held, when one later act repeals the whole act ("Danom stupanja na snagu ovog ...
prestaje važiti <its name> (<its gazette number>)", or "Ovim ... stavlja se van snage ..."), nothing else changed
it before, and the repealing act's own in-force day reads (or, for "Početkom primjene ovog ...", the date its last
article says it applies from): the act then has a second version with no units on that day, credited to the
repealing act.
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
from difflib import SequenceMatcher
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


def code_target(title: str) -> str | None:
    """An amending law of a code named without "ZAKON O" (ZAKON O IZMJENAMA ... IZBORNOG / KRIVIČNOG ZAKONA ...)."""
    m = re.match(r"^ZAKON\s+O\s+(?:IZMJEN\w*|DOPUN\w*)(?:\s+I\s+(?:IZMJEN\w*|DOPUN\w*))*\s+(\w+\s+ZAKONA\b.*)$", norm(title).upper())
    return f"zakon:{subject(m.group(1))}" if m else None


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


def split(page: str, word: str = "ZAKON", quoted: bool = False, lenient: bool = False) -> tuple[dict, str, str | None]:
    """(units, title, adoption day) from the document part of the act page.

    quoted: an amending act whose centred article headings include the articles it inserts or rewrites. A heading
    right after "... glasi:" / "... glase:", and the headings that follow it in sequence, belong to the article quoting
    them; the act's own articles must then run 1, 2, 3 ... (a heading that could be either is held as ambiguous)."""
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
    own_n, in_q, q_last = 0, False, None
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
        if m and title_parts and quoted and cur is not None:
            n = int(m.group(1))
            prev = (units[cur]["lines"] + pending)[-1]
            intro = bool(re.search(r"\bgla(?:si|se)\s*:\s*\"?$", prev))
            cont = in_q and n in (q_last, q_last + 1)
            own_next = not m.group(2) and n == own_n + 1
            named_nums = re.findall(r"\b(?:[Čč]lan\w*|čl\.)\s+(\d+)", prev) if intro else []
            if intro and named_nums and str(n) not in named_nums:
                # "... glasi:" naming other articles: this heading is not the one quoted (its text is missing from
                # the page), so it must be the act's own next article
                intro = False
            elif intro and own_next and not named_nums:
                raise Hold("article_numbers_ambiguous")  # "... glasi:" naming no article, then the own next number
            if intro or cont:
                if own_next and not intro:
                    raise Hold("article_numbers_ambiguous")
                units[cur]["lines"].extend(pending + strongs)  # the quoted heading (and caption) as lines
                pending.clear()
                in_q, q_last = True, n
                continue
            if not own_next:
                raise Hold("article_numbers_not_consecutive")
            in_q = False
        if m and title_parts:
            if not m.group(2):
                own_n = int(m.group(1))
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
        if quoted and in_q:
            units[cur]["lines"].append(joined)  # a centred line of the quoted text
        elif not title_parts:
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
    if nums != list(range(1, len(nums) + 1)) and not lenient:
        raise Hold("article_numbers_not_consecutive")
    for k in arts:
        if out[k]["text"].count("\n") < 2:
            raise Hold(f"empty_article:{k}")
    tail_t = " ".join(lines_of(tail))
    m = re.search(r"(\d{1,2})\.\s*(" + "|".join(MONTHS) + r")\s+(\d{4})\.?\s*godine", tail_t)
    adopted = date(int(m.group(3)), MONTHS[m.group(2)], int(m.group(1))).isoformat() if m else None
    return out, title, adopted


def in_force(units: dict, published: str, adopted: str | None = None, title: str | None = None) -> tuple[str, str]:
    arts = [u["text"].replace("\n", " ") for k, u in units.items() if u["kind"] == "art"]
    text = " ".join(arts)
    # This law's own clause: outside quotation marks (provisions quoted into another act are not its own), or in
    # its last article where the quotation marks of earlier articles are unbalanced.
    clauses = [m.group(1) for m in IN_FORCE.finditer(text) if text.count('"', 0, m.start()) % 2 == 0]
    last = [m.group(1) for m in IN_FORCE.finditer(arts[-1]) if not arts[-1][:m.start()].rstrip().endswith('"')]
    if not clauses and last:
        clauses = last
    full = None
    if not clauses:
        # The act names itself another way in its last article ("Zakon stupa ...", "Izmjene i dopune Pravilnika
        # stupaju ...", "Ovaj Pravilnik, stupa ..."): a sentence of the last article, outside quotation marks.
        clauses = own_clause(arts[-1], title)
        if not clauses:
            raise Hold("in_force_clause_missing")
    else:
        # the clause up to the end of its sentence, numeric dates included ("stupa na snagu 01.01.2015. godine")
        m = list(IN_FORCE.finditer(text if clauses is not last else arts[-1]))
        m = [x for x in m if x.group(1) == clauses[-1]]
        if m:
            full = (text if clauses is not last else arts[-1])[m[-1].start(1):m[-1].start(1) + 160]
    c = clauses[-1].strip()
    try:
        return read_day(c, published, adopted)
    except Hold as h:
        if not str(h).startswith("in_force_unreadable"):
            raise
        # Second reading, for clauses the first one cannot read: spelling variants and numeric dates.
        return read_day(variants(full or c), published, adopted, second=True)


def own_clause(last: str, title: str | None) -> list[str]:
    """In-force clauses of the last article whose subject is the act itself, outside quotation marks."""
    out = []
    t = subject(title or "")
    for m in re.finditer(r"(?:^|(?<=[.:]\s)|(?<=\)\s))([^.\"]{0,300}?)\s*,?\s+stupaj?u?\s+na\s+snagu\s+([^\"]*?(?:\"[^\"]*\"[^\".]*)*)(?=\.\s|\.$|$)", last):
        if last.count('"', 0, m.start()) % 2:
            continue
        subj = re.sub(r"^#\s*Član\s+\d+\w?\.\s*", "", m.group(1)).strip()
        subj = re.sub(r"^\([^)]*\)\s*", "", subj).strip()
        s = subject(subj)
        if re.fullmatch(r"(?:(?:ovaj|ovo|ova|ove|taj)\s+)?(?:pravilnika?|pravlnik|zakon|uputstvo|upustvo|poslovnik|pravilo)", s) or \
                re.fullmatch(r"(?:ove?\s+|ova\s+)?(?:izmjen[ae]|dopun[ae])(?:\s+i\s+(?:izmjen[ae]|dopun[ae]))?\s+(?:pravilnika|zakona|uputstva|poslovnika|pravila)"
                             r"(?:\s+o\s+.+)?", s) or \
                (t and len(s) >= 20 and re.sub(r"^(?:ovaj|ovo|ova|ove|taj)\s+", "", s)[:40] == t[:40]):
            out.append(m.group(2))
    return out


def variants(c: str) -> str:
    """Spelling variants of an in-force clause, for the second reading only."""
    c = c.replace("lј", "lj").replace("nј", "nj").replace("Ј", "J").replace("ođ", "od").strip()
    c = re.sub(r"\bobavljivanja\b", "objavljivanja", c)
    c = re.sub(r"\bobjave\b", "objavljivanja", c)
    c = re.sub(r"^(\w+)\s*\(\s*(?:\d+|osam|osmi|osmog)\s*\)", r"\1", c)  # "osmog (8) dana", "8 (osam) dana"
    c = re.sub(r"^(?:osam|osmi)\s+dana?\b", "osmog dana", c)
    c = re.sub(r"^prvi\s+dan\b", "prvog dana", c)
    c = re.sub(r"^dan\s+nakon\b", "prvog dana nakon", c)
    c = re.sub(r"^prvog\s+narednog\s+dana\b", "narednog dana", c)
    c = re.sub(r"\bdana\s+od\s+objavljivanja\b", "dana od dana objavljivanja", c)
    c = re.sub(r"\bnakon\s+dana\s+objavljivanja\b", "nakon objavljivanja", c)
    c = re.sub(r"^objavljivanjem\b", "danom objavljivanja", c)
    # the day it was signed (the signature block's day), when no other condition or day is attached
    if not re.search(r"saglasnost|\d{1,2}\.\s*\d{1,2}\.\s*\d{4}", c):
        c = re.sub(r"^dan[ao]m\s+(?:potpisivanja|donošenja)\b", "danom donošenja", c)
    return c


def read_day(c: str, published: str, adopted: str | None, second: bool = False) -> tuple[str, str]:
    # matching only: some texts mix Cyrillic ј into Latin lj/nj, and say "objave" for "objavljivanja"
    c = c.replace("lј", "lj").replace("nј", "nj").replace("Ј", "J")
    c = re.sub(r"\bobjave\b", "objavljivanja", c)
    c = re.sub(r"^osam\s+dana", "osmog dana", c)
    p = date.fromisoformat(published)
    if second:
        # "narednog dana od dana donošenja": counted from the day it was made (signature block), not after publication
        m = re.match(r"^(" + "|".join(ORD) + r")a?\s+dana\s+(?:od\s+dana|nakon|po|poslije)\s+(?:njegovog\s+)?donošenja\b", c)
        if m:
            if adopted and adopted <= published:
                return (date.fromisoformat(adopted) + timedelta(days=ORD[m.group(1)])).isoformat(), "adoption_days"
            raise Hold("in_force_on_adoption_day_unknown")
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


REPEAL = re.compile(r"\bprestaj[eu]\s+(?:da\s+)?važi(?:ti)?\b|\bprestaj[eu]\s+važnost|\bstavlja(?:ju)?\s+se\s+van\s+snage|"
                    r"\bvan\s+snage\s+(?:se\s+)?stavlja")
SENTENCE_END = re.compile(r"(?<=[a-zčćžšđ)\"])\.\s+(?=[A-ZČĆŽŠĐ])|\bČlan\s+\d+\w?\.\s")


def repeals(flat: str, start: int, end: int) -> bool:
    """The sentence holding a citation says that what it names ceases to be valid ("prestaje važiti ..."); not when
    the citation names the event it is timed by ("... danom stupanja na snagu Zakona o ...")."""
    if re.search(r"(?:stupanja|stupanjem)\s+na\s+snagu\s*$|primjen\w*\s*$", flat[max(0, start - 40):start]):
        return False
    return repeal_sentence(flat, start, end) is not None


PARTIAL = re.compile(r"\b(?:[Čč]lan\w*|čl\.|stav\w*|tačk\w*|alinej\w*|odredb\w*|dodat\w*|dio|dijel\w*|poglavlj\w*|"
                     r"aneks\w*|prilog\w*|izuzev|osim|tabel\w*)\b", re.I)


def repeal_sentence(flat: str, start: int, end: int) -> tuple[int, int] | None:
    """(start, end) of the sentence holding the citation at start:end when it says what it names ceases to be valid."""
    if re.search(r"(?:stupanja|stupanjem)\s+na\s+snagu\s*$|primjen\w*\s*$", flat[max(0, start - 40):start]):
        return None
    a = max(0, start - 400)
    b = min(len(flat), end + 200)
    before = [m.end() for m in SENTENCE_END.finditer(flat, a, start)]
    after = SENTENCE_END.search(flat, end, b)
    s, e = (before[-1] if before else a), (after.start() if after else b)
    return (s, e) if REPEAL.search(flat[s:e]) else None


def repeal_kind(flat: str, start: int, end: int) -> list[bool]:
    """[whole, on its own day] for a repeal sentence: the whole act ceases to be valid (no article, annex or exception
    named next to the citation), and it does so on the day the repealing act takes effect ("Danom stupanja na snagu
    ovog ...", "Stupanjem na snagu ovog ...", "Ovim pravilnikom ..."), not on a day of application or a date."""
    s, e = repeal_sentence(flat, start, end)
    sent = flat[s:e]
    m = REPEAL.search(sent)
    cs, ce = start - s, end - s
    near = sent[m.end():cs] if m.end() <= cs else sent[ce:m.start()]
    whole = not PARTIAL.search(near) and not PARTIAL.search(sent[ce:ce + 40].split(",")[0]) and \
        not PARTIAL.search(sent[max(0, cs - 30):cs])
    sent = re.sub(r"^\s*(?:\(\d+\)\s*)?\([^)]{0,80}\)\s*", "", sent)  # the article's caption, "(Prestanak primjene)"
    own_day = not re.search(r"primjen|istek|\brok\w*|\d{1,2}\.\s*\d{1,2}\.\s*\d{4}|\d{4}\.\s*godine", sent) and \
        all(re.match(r"\s+ov(?:og|oga|e|im)\b", sent[x.end():]) for x in re.finditer(r"na\s+snagu", sent))
    # "Početkom primjene ovog Pravilnika ...": on the day the repealing act starts to apply (read from its own text)
    on_application = bool(re.match(r"^(?:\(\d+\)\s*)?(?:Početkom|Danom\s+početka)\s+primjene\s+ov(?:og|e)\s+\w+\s*,?\s*"
                                   r"(?:prestaj|stavlja)", sent)) and \
        not re.search(r"istek|\brok\w*|\d{1,2}\.\s*\d{1,2}\.\s*\d{4}|\d{4}\.\s*godine|na\s+snagu", sent)
    return [whole, own_day, on_application]


def application_day(units: dict) -> str | None:
    """The day an act's last article says it starts to apply, when it names a date ("a primjenjuje se od 1.1.2026.")."""
    arts = [u["text"].replace("\n", " ") for u in units.values() if u["kind"] == "art"]
    m = re.search(r"primjenj\w*\s+(?:će\s+)?(?:se\s+)?(?:od|počev\s+od)\s+(?:dana\s+)?(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})", arts[-1]) or \
        re.search(r"primjenj\w*\s+(?:će\s+)?(?:se\s+)?(?:od|počev\s+od)\s+(?:dana\s+)?(\d{1,2})\.\s*(" + "|".join(MONTHS) + r")\s+(\d{4})", arts[-1])
    if not m:
        return None
    return date(int(m.group(3)), MONTHS.get(m.group(2)) or int(m.group(2)), int(m.group(1))).isoformat()


def same_name(cited: str, title: str) -> bool:
    """A full name cited ("... o <name>") is this act's title: the same after their common start, or differing only
    in a short tail (spelling); not two names that end in different words ("... političkih stranaka" / "...
    nezavisnih kandidata")."""
    a = re.sub(r"\W+", "", cited.lower())
    b = re.sub(r"\W+", "", re.sub(r"^\w+\s+o\s+", "", norm(title).lower()))
    p = 0
    while p < min(len(a), len(b)) and a[p] == b[p]:
        p += 1
    ta, tb = a[p:], b[p:]
    return not (len(ta) >= 8 and len(tb) >= 8 and SequenceMatcher(None, ta, tb).ratio() < 0.6)


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
    named: dict[str, list[tuple[str, str | None]]] = defaultdict(list)
    for r in rows:
        ts = target_subject(r["title"])
        if ts:
            named[ts].append((r["date"], r.get("akt")))
    # Each issue's acts by subject: to tell which act an amending text's citation points to.
    at_issue: dict[tuple[int, int], list[tuple[str, str | None]]] = defaultdict(list)
    for r in rows:
        s = own_subject(r["title"])
        if s:
            at_issue[(r["issue"], 2000 + int(r["yy"]) if len(r["yy"]) == 2 else int(r["yy"]))].append((s, r.get("akt")))
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
            # the full name repealed (subjects are cut at 80 characters, too short to tell some acts apart)
            # and whether it is the whole act, on the repealing act's own in-force day
            rep = kind != "court" and repeals(flat, m.start(), m.end()) and \
                [norm(m.group(2)).lower().strip(" .,;:")] + repeal_kind(flat, m.start(), m.end())
            for k, iss in enumerate(lst):
                # (citing day, citing kind, citing act, court struck something, issues listed after this one,
                #  the citing sentence repeals what it names)
                found.append([f"{stem(m.group(1))}:{subject(m.group(2))}", iss[0], iss[1], kind, r["akt"], struck, len(lst) - k - 1, rep])
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
    # A text the publisher's page does not serve (listed in unfetchable.json) can never be read: the gate does not
    # wait for it, and only its title counts (the amendment and repeal titles above); a text read later counts fully.
    unfetchable = {}
    if (src / "unfetchable.json").exists():
        unfetchable = json.loads((src / "unfetchable.json").read_text(encoding="utf-8"))
    missing = defaultdict(list)
    for r in rows:
        if r.get("akt") and r["akt"] not in texts and r["akt"] not in unfetchable:
            for w in KINDS:
                if w != "ZAKON" or first_word(r) == "ZAKON" or "USTAVNI SUD" in r["issuer"].upper():
                    missing[w].append(r["date"])
    complete_from = {w: max(missing[w], default="0000") for w in KINDS}
    missing_days = missing["ZAKON"]
    cited_by: dict[str, set[tuple[str, int, int]]] = defaultdict(set)  # citing act -> (subject, issue) it cites
    per_cite: dict[tuple[str, str], set[tuple[int, int]]] = defaultdict(set)
    for (s, n, y), lst in cites.items():
        for c in lst:
            cited_by[c[2]].add((s, n, y))
            per_cite[(s, c[2])].add((n, y))
    multi = {k for k, v in per_cite.items() if len(v) > 1}  # (subject, citing act) cited with several issues

    def other_act(x_akt: str | None, ts: str, subj: str, own: tuple[int, int], akt: str) -> bool:
        """The amending text x (held) cites its target under issues that are another act of that subject, and never
        this act's issue: its title names another act, not this one."""
        if not x_akt or x_akt not in texts:
            return False
        iss = {(n, y) for s, n, y in cited_by.get(x_akt, ()) if similar(s, ts, 40)}
        if not iss or own in iss:
            return False
        return any(similar(s2, ts, 40) and a2 != akt for i in iss for s2, a2 in at_issue.get(i, ()))
    row_of = {}
    for r in rows:
        if r.get("akt"):
            row_of.setdefault(r["akt"], r)

    def read_act(r: dict, lenient: bool = False) -> tuple[dict, str | None, str, str]:
        """(units, adoption day, in-force day, how) of an act's text; raises Hold. lenient: only its days are wanted
        (a repealing act), so article numbering with a gap does not matter."""
        title, word = norm(r["title"]), first_word(r)
        if word not in KINDS:
            raise Hold("kind:" + word[:20])
        page = gzip.decompress(raw_path(src, r["akt"]).read_bytes()).decode("utf-8")
        try:
            units, text_title, adopted = split(page, word)
        except Hold as h:
            if lenient and str(h).startswith("article_numbers_not_consecutive"):
                units, text_title, adopted = split(page, word, lenient=True)
            # an amending act whose centred headings include the articles it quotes: split again, quote-aware
            elif not (str(h).startswith(("article_numbers_not_consecutive", "duplicate_unit"))
                      and re.search(r"\b(?:IZMJEN|DOPUN)", title.upper())):
                raise
            else:
                units, text_title, adopted = split(page, word, quoted=True)
        if subject(text_title).replace(" ", "") != subject(title).replace(" ", ""):
            raise Hold("title_mismatch:" + text_title[:100])
        day, how = in_force(units, r["date"], adopted, title)
        if adopted and not (adopted <= r["date"] <= (date.fromisoformat(adopted) + timedelta(days=90)).isoformat()):
            raise Hold(f"adoption_day_inconsistent:{adopted}")
        return units, adopted, day, how

    def law_entry(r: dict, adopted: str | None) -> tuple[str, dict]:
        """An act's key and its record in "laws" (the same for the act itself and for an act it is credited to)."""
        title = norm(r["title"])
        kslug, lkind = KINDS[first_word(r)]
        key = f"{kslug}-{int(r['date'][:4])}-sg{r['issue']:03d}-{hashlib.sha1(r['akt'].encode()).hexdigest()[:6]}"
        nice = title[0] + title[1:].lower() if title.isupper() else title
        nice = re.sub(r"\bbosne i hercegovine\b", "Bosne i Hercegovine", nice)
        label = f'{nice} ("Službeni glasnik BiH", br. {r["issue"]}/{r["yy"]})'
        return key, {"label": label, "title": nice, "kind": lkind, "enacted": adopted, "published": r["date"],
                     "url": AKT_URL.format(akt=r["akt"]), "temporary_until": None, "restores": None, "note": None}

    seen_slugs = set()
    for r in sorted(laws, key=lambda x: (x["date"], x["issue"], x["akt"])):
        title = norm(r["title"])
        pub = r["date"]
        year = int(pub[:4])
        own = (r["issue"], 2000 + int(r["yy"]) if len(r["yy"]) == 2 else int(r["yy"]))
        repealers = []
        try:
            if r["akt"] in rejects:
                raise Hold("rejected:" + str(rejects[r["akt"]])[:200])
            if r["akt"] not in texts:
                raise Hold("text_not_fetched")
            word = first_word(r)
            kslug, lkind = KINDS[word]
            if pub <= complete_from[word]:
                raise Hold("awaiting_later_texts:" + complete_from[word])
            ts = target_subject(title) or code_target(title)
            amending = ts is not None
            subj = own_subject(title)
            if not amending and not subj:
                raise Hold("title_form")
            if amending:
                # a correction titled with this law's name counts, unless it names another gazette issue ("(br. 17/24)")
                corr = [x for x in rows if x["date"] >= pub and x is not r and x["title"].upper().startswith("ISPRAVK")
                        and subject(x["title"]).find(re.sub(r"^\w+ o ", "", subject(title))[:60]) >= 0
                        and not ((iss := issues_in(" ".join(re.findall(r"\(\s*br(?:oj|\.)\s*([^)]*)\)", x["title"], flags=re.I))))
                                 and own not in iss)]
                if corr:
                    raise Hold("correction_named")
                # A later text citing this amending law itself by name and issue (not the principal law's list).
                tk, tsub = ts.split(":", 1)
                own_cites = [c for (s, n, y), lst in cites.items() if (n, y) == own and s.split(":", 1)[0] == stem(word)
                             and re.match(r"^(?:izmjen|dopun)", s.split(":", 1)[1]) and tsub[:40] in s for c in lst if c[2] != r["akt"] and c[0] >= pub
                             and (c[1] == "law" or (c[1] == "court" and c[3]))
                             # a code's amending law: a citation listing several issues names the code, not this law
                             and not (ts == code_target(title) and (s, c[2]) in multi)]
                if own_cites:
                    raise Hold("amending_law_cited_later:" + ",".join(sorted({c[0] for c in own_cites})[:3]))
            else:
                later = [d for d, _ in named.get(subj, []) if d >= pub]
                # a similar title (not the same) counts unless that amending text's own citation shows another act
                later += [d for s, lst in named.items() if s != subj and similar(s, subj, 50) for d, x in lst if d >= pub
                          and not other_act(x, s, subj, own, r["akt"])]
                if later:
                    raise Hold("named_as_amended:" + ",".join(sorted(set(later))[:3]))
                # A later citation that lists issues after this one names its amendments; a court decision that
                # strikes provisions changes it; a sentence saying it ceases to be valid repeals it. A citation of this
                # issue alone otherwise (a regulation's legal basis) does not.
                by_cite = [c for (s, n, y), lst in cites.items() if (n, y) == own and similar(s, subj, 40)
                           for c in lst if c[2] != r["akt"] and c[0] >= pub and (c[4] > 0 or (c[1] == "court" and c[3]))]
                if by_cite:
                    raise Hold("cited_later:" + ",".join(sorted({c[0] for c in by_cite})[:3]))
                by_rep = [c for (s, n, y), lst in cites.items() if (n, y) == own and similar(s, subj, 40)
                          for c in lst if c[2] != r["akt"] and c[0] >= pub and c[5] and same_name(c[5][0], title)]
                if by_rep:
                    # Published with its repeal as a last, empty version, when the repeal is of the whole act, by one
                    # act, on that act's own in-force day (read below); otherwise held.
                    if not all(c[5][1] for c in by_rep):
                        raise Hold("repealed_later_in_part:" + ",".join(sorted({c[0] for c in by_rep})[:3]))
                    on_app = not all(c[5][2] for c in by_rep)
                    if on_app and not all(len(c[5]) > 3 and c[5][3] for c in by_rep):
                        raise Hold("repealed_later_day_unknown:" + ",".join(sorted({c[0] for c in by_rep})[:3]))
                    events = {(row_of[c[2]]["date"], row_of[c[2]]["issue"]) for c in by_rep}
                    if len(events) > 1:
                        raise Hold("repealed_by_several:" + ",".join(sorted(d for d, _ in events)[:3]))
                    repealers = sorted({c[2] for c in by_rep})
            units, adopted, day, how = read_act(r)
            repeal = None
            if repealers:
                # the repealing act's own in-force day, read from its text like any act's (the first of its listings
                # in the gazette index that reads)
                errs = []
                for ak in repealers:
                    try:
                        r_units, r_adopted, r_day, r_how = read_act(row_of[ak], lenient=True)
                        if on_app:
                            app = application_day(r_units)
                            if not app or app < r_day:
                                raise Hold(f"application_day_unknown:{app}")
                            r_day, r_how = app, "application"
                        repeal = (row_of[ak], r_adopted, r_day, r_how)
                        break
                    except (Hold, KeyError) as e:
                        errs.append(str(e)[:60])
                if repeal is None:
                    raise Hold("repealing_act_day_unknown:" + ";".join(errs)[:120])
                if repeal[2] < day:
                    raise Hold(f"repeal_before_in_force:{repeal[2]}")
        except Hold as h:
            holds.append({"akt": r["akt"], "sg": f"{r['issue']}/{r['yy']}", "date": pub, "title": title[:160], "reason": str(h)})
            continue
        pk = (40, "zakoni") if kslug == "zakon" else (50, kslug)
        slug = f"{kslug}-{year}-sg{r['issue']:03d}-{hashlib.sha1(r['akt'].encode()).hexdigest()[:6]}"
        if slug in seen_slugs:
            holds.append({"akt": r["akt"], "sg": f"{r['issue']}/{r['yy']}", "title": title[:160], "reason": "slug_collision"})
            continue
        seen_slugs.add(slug)
        _, law = law_entry(r, adopted)
        nice, url = law["title"], law["url"]
        note = None
        if re.search(r"primjenj\w+\s+(?:će\s+se\s+)?(?:se\s+)?(?:od|počev)", " ".join(u["text"] for u in units.values() if u["kind"] == "art")[-600:]):
            note = "Njegov završni član određuje i poseban dan primjene."
        parts[(pk, year)]["laws"][slug] = law
        versions = [{"from": day, "source_url": url, "sha256": fetched[r["akt"]]["sha256"], "units": units,
                     "credits": {}, **({"note": note} if note else {})}]
        if repeal:
            # the repeal: every unit removed, on the repealing act's in-force day, credited to it
            rr, r_adopted, r_day, r_how = repeal
            rk, rlaw = law_entry(rr, r_adopted)
            parts[(pk, year)]["laws"][rk] = rlaw
            when = "početka primjene" if r_how == "application" else "stupanja na snagu"
            versions.append({"from": r_day, "source_url": rlaw["url"], "sha256": fetched[rr["akt"]]["sha256"], "units": {},
                             "credits": {k: [rk] for k in sorted(units)},
                             "note": f"Prestao je važiti {r_day}, danom {when} akta {rlaw['label']}, koji to određuje.",
                             **({"same_day": True} if r_day == day else {})})
            parts[(pk, year)].setdefault("_retrieved", set()).add(fetched[rr["akt"]].get("retrieved"))
        parts[(pk, year)]["acts"].append({
            "slug": slug, "short": nice, "title": nice, "url": url, "first_law": slug, "earlier_laws": [],
            "versions": versions})
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
            "its caption.",
            "An act that a later act repeals as a whole (\"prestaje važiti ...\" naming it with its gazette number), on "
            "that act's own in-force day, and that nothing else changed before, gets a last version with no units on "
            "that day, credited to the repealing act; any other repeal holds the act back."]
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
