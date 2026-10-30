# Bosnia and Herzegovina: law history in git

The Constitution of Bosnia and Herzegovina as a git repository: one file per Article and Annex, so `git blame` and `git log` work on the text. It follows the shared design of [lexifina/global-law](https://github.com/lexifina/global-law), which places it at `ba/`.

**What is in it now**

| Folder | Law | Versions | History |
| --- | --- | ---: | --- |
| `constitution/` | Constitution of Bosnia and Herzegovina (Annex 4 to the General Framework Agreement for Peace, Dayton/Paris) | 1 | As signed on 14 December 1995 |
| `criminal-code/` | Criminal Code of Bosnia and Herzegovina (2003), unofficial consolidated English text to Official Gazette 47/14 | 1 | Oldest version available: the Prosecutor's Office of BiH file, dated 4 May 2017; files `art-NNN` (letter suffixes as `art-202-b`) and `div-NNN` (part and chapter headings) |

**Language.** The text is the English original, which is the authentic text of Annex 4; the Constitutional Court also publishes it in Bosnian, Croatian and Serbian.

## Dates and limits

- One version, dated **14 December 1995**: under Article XII(1) the Constitution entered into force on signature of the General Framework Agreement. The commit is credited to Annex 4 of the Agreement.
- **Amendment I (26 March 2009, Brcko District) is not in this record.** The source is the Constitutional Court's English PDF, created in 2006, which predates it. The amended Bosnian text and later changes are a later build.
- Files: `art-01.md` is Article I, `annex-ii.md` is Annex II, `preamble.md` is the preamble. Each Article keeps its numbered sections as lines. The signed declarations at the end are not files.
- The PDF's own typesetting is kept; for example, Article I(4) reads "Movement of Goods. Services. Capital. and Persons." with its headings run together.

## Criminal Code

The text is the English consolidation posted by the Prosecutor's Office of BiH, which labels it unofficial; the Official Gazette text in the local languages prevails. It runs to amendment 47/14, so later amendments are not in it. The version date is the file's last-modified date. There is no civil or commercial code in this record: civil and commercial law is made by the entities and the Brcko District, not by the state.

## Source

Prosecutor's Office of Bosnia and Herzegovina (https://www.tuzilastvobih.gov.ba), Criminal Code consolidated text, retrieved 30 October 2026. Constitutional Court of Bosnia and Herzegovina (https://www.ustavnisud.ba), Constitution of Bosnia and Herzegovina, English PDF, retrieved 29 October 2026.

No AI model wrote or changed legal text. This is not legal advice and not an official publication; for anything that matters, read the original.
