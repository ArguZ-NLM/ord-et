Builds `meanings.json` (word meanings shown after a word is solved).

Sources, both CC BY-SA 4.0:
- English Wiktionary, Danish entries, as JSON from kaikki.org: https://kaikki.org/dictionary/Danish/kaikki.org-dictionary-Danish.jsonl
- Danish Wiktionary dump: https://dumps.wikimedia.org/dawiktionary/latest/dawiktionary-latest-pages-articles.xml.bz2 (unzipped)

Put both in `w/dl/`, write the word list to `w/words.txt`, run the three scripts in order with `python3 -I`, then keep one sense per language as in the last commit.
