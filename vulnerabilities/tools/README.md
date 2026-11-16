# Tools

The scripts behind this Bosnia-and-Herzegovina-only run of global-law's vulnerability detectors. They run inside a copy of
[global-law/vulnerabilities/scripts](https://github.com/lexifina/global-law/tree/main/vulnerabilities/scripts) (Python 3.11+,
`pip install duckdb pyarrow`), with a bare clone of this repository at `sources/corpus/bosnia-and-herzegovina-law.git`, a
blobless bare clone of global-law at `sources/global-law.git`, and a `pins.json` that names only bosnia-and-herzegovina-law and
its commit. `build_vulns.py`, `flags_chart.py`, `late_ext_select.py`, `late_ext_rebut.py`, `do_gap_check.py`, `redo.py` and `config.json`
sit three folders above the scripts.

| Script | What it does |
| --- | --- |
| `run.sh` | Indexes the history and texts, maps paths to the folders since a move of act folders (`map_moved.py`), adds this repository's history rows, and runs the detectors |
| `add_root.py` | Builds the history rows from this repository's own commits (global-law replays it only up to an earlier commit), so the history detectors read every change |
| `run_triage.sh` | The model review: the 40 strongest flags per category, the 40 strongest lapsed time limits in law texts, and the empty periods (none here) |
| `late_ext_select.py` | Chooses the empty periods for global-law's review of that category |
| `late_ext_rebut.py` | Adds the second, arguing-against pass to the empty-period review, as `triage.py` does for the other categories |
| `build_vulns.py` | Builds `data/flags.csv`, `data/reviewed.csv` and `data/by_category.csv` from the findings and the model review |
| `flags_chart.py` | Draws the chart at the top of the READMEs, in Bosnian and English, light and dark |
| `do_gap_check.py` | Counts the "do <date>", "do dana <date>", "zaključno sa <date>" and "do kraja <year>. godine" phrases in law texts that the lapsed-time-limit pattern does not read |
| `patch_detectors.py` | Fixes blind spots found in runs on several country repositories in the copy of global-law's scripts (`python -X utf8 patch_detectors.py <scripts dir>`; a fix already in place is skipped) |
| `patch_detectors_vi.py` | The same for Vietnamese dates, references and amounts (found by the Vietnam run); it changes nothing here, but `redo.py` runs it on every repository |
| `patch_es.py` | The same for Spanish dates and for "marco" and "escudo" read as currencies; it changes nothing here either |
| `patch_ca.py` | The same for Catalan dates and time limits, the Catalan peseta, and "sucre" (sugar) read as the Ecuadorian sucre; it changes nothing here either |
| `map_moved.py` | Rewrites the paths in the history table to each act's folder since a repository moved its act folders (`data/paths.json`), so that an act's history is not split in two at the move; `run.sh` runs it after the history is indexed. This repository has not moved its folders, and it rewrote no path |
| `patch_build_r7.py` | Brings a country's `build_vulns.py` up to date: lapsed-limit reviews matched on 400 characters of context, not 80, each retroactive-date row given the first file of its act as its path, and a file deleted before a move of folders linked under its old folder (already applied to the `build_vulns.py` here) |
| `redo.py` | Runs the patches, then again only the scans and detectors the fixes change, the model review of lapsed time limits, references to deleted provisions and empty periods, and the build (`python -X utf8 redo.py <run folder> [--keep-reviews] [--full]`; `--full` runs every step again through `run.sh`, `map_moved.py` among them, sends every category to the model and keeps every review already made; `EMBED_FONTS` names the script that embeds the chart's fonts) |
| `config.json` | The repository, the Bosnian category names, the folders that are not law, and the chart's labels |

The model review needs `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` and `LLM_AUTH` set for an OpenAI-compatible Responses API.

Two changes to the shared scripts were needed here:

- `add_root.py` counts as law the commits whose `Kind:` is `decree` (the Gazette's rulebooks, instructions, decisions and orders, 3,633 commits), `treaty` (the Constitution), `regulation` and `instruction` (four acts of the Indirect Taxation Authority) and `publisher` (consolidated texts, among them the Criminal Code), as well as `law`. Without them the history detectors would read 215 law commits instead of 3,889. `court` (Constitutional Court decisions), `case-law`, `bill` and `as-enacted` (here the Competition Council's rulings) keep their own kind and are left out.
- `run.sh` takes `LE_WORKERS` and `LE_GREP_THREADS` from the environment when they are set (default 6), so a run on a busy machine can use fewer processes.

The run was then repeated with `redo.py`. Of `patch_detectors.py`'s fixes, two change this repository's flags: lapsed time limits now read the Bosnian month names "januara", "februara", "marta", "juna" and "jula", numeric dates written with spaces ("31. 12. 2010"), "do dana" and "zaključno sa" before a date and "do kraja 2015. godine", and "najkasnije" ranks a limit as a deadline (lapsed time limits went from 1,134 to 1,547 flags; `do_gap_check.py` now finds no phrase of these forms in law texts that is not read, where it found 178 "do <date>" phrases before); and "DM" counts as a currency only in capitals, which removed two "dm²" and a link id ending in "3dM" (dead currencies went from 19 to 16). A second run, `redo.py --keep-reviews` for fixes made for other countries, changed no flag here; it keeps every review already made and sent the 40 strongest lapsed time limits not yet reviewed to the model (80 reviewed in all). A third, also with `--keep-reviews`, after the fifth round of fixes (the sharded scans split their work by a stable checksum over sorted rows, so no act is read twice or skipped; ties among the strongest flags are broken the same way every time; "lira" only at the start of a word), left the lapsed time limits at 1,547, removed "kontrolira 1%" from the dead currencies (16 to 15) and sent 34 more lapsed time limits to the model (114 reviewed in all).

A last run, `redo.py --full`, repeated every step with the current `patch_detectors.py`, keeping every review already made
(`map_moved.py` rewrote no path here). What changed for this repository:

- References to repealed placeholders (`detectors/placeholder_ref.py`, twelfth round): "brisan" counts only as a whole word
  ("brisan", "brisana", "brisano"), so "Brisanje izrečene sankcije" and "Brisanje upisa" (the erasure of a sanction, of a
  register entry) no longer make an article in force read as deleted. Two of the three references are gone; the one left is
  an amending act's own "brisan". Dead fines (`detectors/dead_fine.py`, run again for the first time since the first round)
  found nothing, as before.
- Currencies (`detectors/currency_scan.py`, sixth round): the Latvian "lati" and "latu" only as words, which took out
  "isplatu 65.200,00 eura" in a Constitutional Court decision and "latiničnim" in a rulebook: dead currencies went from 15
  to 13, none of them in law texts. The other new currency fixes ("BEF" only in capitals, no "liraglutid", no Swiss
  "frank", francs CFP, French "lire" and "sucre", the dinar left out for French, Arabic and Serbian texts) change nothing
  here; no language is set for this repository, so the Yugoslav dinars in a Constitutional Court decision still count.
- Lapsed time limits stay at 1,547 and the other categories as they were. The model reviewed 26 more lapsed time limits
  (140 in all); three more survived, each checked by hand (see EDGE-CASES).
- `build_vulns.py` (`patch_build_r7.py`, applied after the run, as `redo.py` does not apply it): lapsed-limit reviews are
  matched on 400 characters of context, not 80, which changed no match here, and each retroactive-date row names the first
  file of its act in `path`, which leaves all 1,203 of them in law texts.
