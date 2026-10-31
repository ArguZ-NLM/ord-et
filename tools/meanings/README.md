Builds `meanings.json` (word meanings shown after a word is solved).

Sources, both CC BY-SA 4.0:
- English Wiktionary, Danish entries, as JSON from kaikki.org: https://kaikki.org/dictionary/Danish/kaikki.org-dictionary-Danish.jsonl
- Danish Wiktionary dump: https://dumps.wikimedia.org/dawiktionary/latest/dawiktionary-latest-pages-articles.xml.bz2 (unzipped)

Put both in `w/dl/`, write the word list to `w/words.txt`, run the scripts 1–3 in order with `python3 -I`, then keep one sense per language as in the git history. `4_fix_pool.py` lists the pool fixes made from Wiktionary (missing participle endings in compounds, loanwords split as compounds).

Danish texts: `5_dannet.py` (run last) prefers DanNet (https://github.com/kuhumcst/DanNet/releases, `dannet-csv.zip`, CC BY-SA 4.0), whose definitions are written by the editors of Den Danske Ordbog. DanNet cuts about 60% of them at 50 characters; for those, the Danish Wiktionary text is used when there is one, else the cut text up to its last whole word. The word class with most DanNet senses decides which sense is shown, in both languages.
