"""How many Bosnian "do <date>" limits does global-law's lapsed-limit pattern miss? Law texts at the pin only.
    python -X utf8 do_gap_check.py
"""
import json, os, re, subprocess, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.join(HERE, "gl", "vulnerabilities", "scripts")
sys.path.insert(0, os.path.join(SCR, "ingest"))
import textscan as T  # noqa: E402

CFG = json.load(open(os.path.join(HERE, "config.json"), encoding="utf-8"))
NOT_LAW = tuple(CFG["not_law"])
GIT = os.path.join(SCR, "sources", "corpus", CFG["repo"] + ".git")
PIN = json.load(open(os.path.join(SCR, "pins.json"), encoding="utf-8"))["corpora"][0]["sha"]

BS = r"januara|februara|marta|aprila|maja|juna|jula|augusta|avgusta|septembra|oktobra|novembra|decembra"
# every "do <date>" a Bosnian drafter writes: 31.12.2015, 31. 12. 2015, 31. decembra 2015, 1. jula 2026
ANY = re.compile(rf"(?i)\bdo\s+(?:\d{{1,2}}\.\s*\d{{1,2}}\.\s*\d{{4}}|\d{{1,2}}/\d{{1,2}}/\d{{4}}|\d{{1,2}}\.?\s*(?:{BS})\s*\d{{4}})")

files = [p for p in subprocess.run(["git", "-C", GIT, "ls-tree", "-r", "--name-only", PIN], capture_output=True, text=True,
                                   encoding="utf-8").stdout.splitlines() if p.endswith(".md") and not p.startswith(NOT_LAW)]
caught = missed = 0
how = Counter()
ex = []
B = 400
for i in range(0, len(files), B):
    batch = files[i:i + B]
    inp = "".join(f"{PIN}:{p}\n" for p in batch)
    out = subprocess.run(["git", "-C", GIT, "cat-file", "--batch"], input=inp.encode("utf-8"), capture_output=True).stdout
    pos = 0
    for p in batch:
        nl = out.index(b"\n", pos)
        size = int(out[pos:nl].split()[2])
        text = out[nl + 1: nl + 1 + size].decode("utf-8", "replace")
        pos = nl + 1 + size + 1
        for m in ANY.finditer(text):
            hit = T.LIMIT.match(text, m.start())
            if hit:
                caught += 1
            else:
                missed += 1
                mm = re.search(rf"(?i)({BS})", m.group(0))
                how[mm.group(1).lower() if mm else "spaced numeric"] += 1
                if len(ex) < 8:
                    ex.append((p, m.group(0)))
print("law-text files:", len(files))
print("'do <date>' forms:", caught + missed, "caught:", caught, "missed:", missed)
print(how.most_common())
for e in ex:
    print(e)
