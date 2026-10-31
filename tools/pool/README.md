# The word pool and the meanings

`index.html` (`const AUTO`, and the hand-made `BUILTIN` lists) and `meanings.json` are built by these scripts.
Run them from a folder that has the data in `w/dl/`, with `python3 -I`, in order.

## Data (all free)
| file in `w/dl/` | what | licence |
|---|---|---|
| `cor1.5.1.0.tsv` | Det Centrale Ordregister – every word in Retskrivningsordbogen with all its forms, base word and grammatical tag (https://ordregister.dk/files/) | CC0 (Dansk Sprognævn) |
| `cor.sem.1.0.tsv` | COR.SEM – category and related words per sense (same place) | CC BY-SA 4.0 (DSL) |
| `dannet/` | DanNet CSV, `dannet-csv.zip` from https://github.com/kuhumcst/DanNet/releases | CC BY-SA 4.0 (DSL & CST) |
| `kaikki.org-dictionary-Danish.jsonl` | English Wiktionary, Danish entries (https://kaikki.org/dictionary/Danish/) | CC BY-SA 4.0 |
| `dawiktionary-latest-pages-articles.xml` | Danish Wiktionary dump (https://dumps.wikimedia.org/dawiktionary/latest/) | CC BY-SA 4.0 |
| `wordfreq_da.txt` | word frequencies from the `wordfreq` Python package (`top_n_list('da', …)`), "word count" per line | CC BY-SA 4.0 |

## Rules a word must pass (`3_check.py`)
1. It is a form in COR. Its base word, word class and inflection come from COR – nothing is guessed.
2. Its ending matches its COR tag and is one of the endings in the rule book (verbs: the root is the infinitive without -e, e.g. `skriv-er`, `spill-er`).
3. Every split inside the stem (compound, prefix, suffix) is confirmed: by Wiktionary's etymology, or by DanNet/COR.SEM naming the part
   (the word is a kind of the second part, or both parts are named). A linking letter must match COR's compound form (`tids-`, `børne-`).
   Common verbs with a prefix (`for-klar-e`) and `u-` + adjective count as regular.
4. Words Wiktionary calls borrowed are one root. Loan prefixes (`bio-`, `mikro-`) are never split off.
5. A stem that *could* be split but is not confirmed → the word is dropped. So is a word that also is a function word (`hans`, `mens`),
   a word another common reading would split differently (`bønner`, `arbejderne`), a word where verb stem + e and a noun in -e compete
   (`spise-bord` / `spis-e-bord`), and words on the school blocklist.

`4_build_pool.py` writes the pool (most common first) and removes hand-made examples that fail; `5_meanings.py` writes `meanings.json`
(DanNet for the right word class, else Danish Wiktionary, else DanNet's text cut at the last whole word; English from Wiktionary).
