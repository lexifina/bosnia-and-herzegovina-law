# How this repository was made (Bosnia and Herzegovina)

This file is written by the build on 2026-10-30, the day the source data was retrieved.

## Sources

| Source | Address | Retrieved | Licence |
| --- | --- | --- | --- |
| Constitutional Court of Bosnia and Herzegovina, Constitution (English) | <https://www.ustavnisud.ba/public/down/USTAV_BOSNE_I_HERCEGOVINE_engl.pdf> | 2026-10-29 | Official public text; no licence statement found |
| Prosecutor's Office of Bosnia and Herzegovina, Criminal Code (unofficial consolidated English text) | <https://www.tuzilastvobih.gov.ba/files/docs/zakoni/Criminal_Code_of_BH_-_Consolidated_text_47_14.pdf> | 2026-10-30 | Official public text; no licence statement found |

Every word of law in this repository comes from these sources. Lexifina reads them and records each act's dated versions, and the laws that made each change, in one corpus file. This repository is built from that file.

## What is in it

| Act | Title | Versions | Span |
| --- | --- | ---: | --- |
| `constitution` | Constitution of Bosnia and Herzegovina | 1 | 1995-12-14 to 1995-12-14 |
| `criminal-code` | Criminal Code of Bosnia and Herzegovina | 1 | 2017-05-04 to 2017-05-04 |

The build made 2 commits:

| Commits | Kind |
| ---: | --- |
| 2 | first version of an act |
| 0 | one law on its in-force day |
| 0 | changes no amendment note explains, credited to the publisher |

Other counts:
- 0 commits on the branch `future`: laws not yet in force on 2026-10-30.
- 0 commits dated 1 January 1970: in force before 1970, with the real day in their `In-force` trailer.
- 3 laws in the record.
- 3 tags.

## Dates

Each commit is dated at noon (Europe/Sarajevo) on the day the change took effect. The other dates, enacted and published, are trailers.

When a law gives no date of its own, the default rule applies: Constitution Article XII(1): it enters into force upon signature of the General Framework Agreement (Paris, 14 December 1995) https://www.ustavnisud.ba/public/down/USTAV_BOSNE_I_HERCEGOVINE_engl.pdf

## How the history is built

`tools/build.py` turns the corpus into this history in one pass: one commit per law, on the day it took effect. The same corpus always gives the same commit hashes. `tools/check_repo.py` reads every version back from git and compares it with the corpus. `tools/on.py` shows the law as it stood on any date. The corpus format is described in `tools/SCHEMA.md`.

- Corpus: sha256 `486206a9eb89cc47e6647ae45548f35d595b7049809792d7d0284cc95fbb0432` (406682 bytes).
- Builder blob hashes (`git hash-object`): `build.py` `a4faa25af85facb64b956b372f6b528aafdd7ec1`, `check.py` `3e59cb6f05eccb94a9ec14431a7f6781221e83ef`, `on.py` `644a6c0857fbcc72562032b58d57aa113fee0641`.
- Python 3.12.10; git version 2.46.0.windows.1.

## Checks

Not yet run for this build.

No second build of this corpus has been compared yet.

## Decisions made by hand

- The source is a 2006 English PDF from the Constitutional Court, so the repository holds one version, the Constitution as signed on 14 December 1995 (Article XII(1): in force on signature). Amendment I of 26 March 2009 is not in it and is not in the record.
- One file per Article and per Annex; the numbered sections stay as lines inside each file. The three declarations at the end (signatures) are not units.
- Criminal Code: one version, dated 2017-05-04 (the Last-Modified date of the file on the Prosecutor's Office site), credited to the publisher as 'oldest version available'; the code was adopted in 2003 and in force from 1 March 2003. The text is unofficial and consolidated only to OG 47/14.
- Criminal Code: page numbers, typesetting artefacts and the footnote on amendments were removed; wrapped lines were joined into numbered paragraphs.
- Not added: a civil code and a commercial code. Civil and commercial law is made by the two entities (Federation of BiH, Republika Srpska) and the Brcko District, not by the state, so there is no state-level code to record.

## What AI did and did not do

The scripts that read the sources and build this repository were written by Claude Code running Claude Opus 5.5 (`claude-opus-5-5`) under Lexifina's direction.

No model wrote, translated or corrected legal text. No model runs at build time. Every word of law in this repository comes from the official sources above.

The commit messages are written by `build.py` from the source data.

Model use at data-build time:
- none
