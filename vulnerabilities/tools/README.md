# Tools

The scripts behind this Bosnia-and-Herzegovina-only run of global-law's vulnerability detectors. They run inside a copy of
[global-law/vulnerabilities/scripts](https://github.com/lexifina/global-law/tree/main/vulnerabilities/scripts) (Python 3.11+,
`pip install duckdb pyarrow`), with a bare clone of this repository at `sources/corpus/bosnia-and-herzegovina-law.git`, a
blobless bare clone of global-law at `sources/global-law.git`, and a `pins.json` that names only bosnia-and-herzegovina-law and
its commit. `build_vulns.py`, `flags_chart.py`, `late_ext_select.py`, `late_ext_rebut.py`, `do_gap_check.py` and `config.json`
sit three folders above the scripts.

| Script | What it does |
| --- | --- |
| `run.sh` | Indexes the history and texts, adds this repository's history rows, and runs the detectors |
| `add_root.py` | Builds the history rows from this repository's own commits (global-law replays it only up to an earlier commit), so the history detectors read every change |
| `run_triage.sh` | The model review: the 40 strongest flags per category, the 40 strongest lapsed time limits in law texts, and the empty periods (none here) |
| `late_ext_select.py` | Chooses the empty periods for global-law's review of that category |
| `late_ext_rebut.py` | Adds the second, arguing-against pass to the empty-period review, as `triage.py` does for the other categories |
| `build_vulns.py` | Builds `data/flags.csv`, `data/reviewed.csv` and `data/by_category.csv` from the findings and the model review |
| `flags_chart.py` | Draws the chart at the top of the READMEs, in Bosnian and English, light and dark |
| `do_gap_check.py` | Counts the "do <date>" phrases in law texts that the lapsed-time-limit pattern does not read |
| `config.json` | The repository, the Bosnian category names, the folders that are not law, and the chart's labels |

The model review needs `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` and `LLM_AUTH` set for an OpenAI-compatible Responses API.

Two changes to the shared scripts were needed here:

- `add_root.py` counts as law the commits whose `Kind:` is `decree` (the Gazette's rulebooks, instructions, decisions and orders, 3,633 commits), `treaty` (the Constitution), `regulation` and `instruction` (four acts of the Indirect Taxation Authority) and `publisher` (consolidated texts, among them the Criminal Code), as well as `law`. Without them the history detectors would read 215 law commits instead of 3,889. `court` (Constitutional Court decisions), `case-law`, `bill` and `as-enacted` (here the Competition Council's rulings) keep their own kind and are left out.
- `run.sh` takes `LE_WORKERS` and `LE_GREP_THREADS` from the environment when they are set (default 6), so a run on a busy machine can use fewer processes.
