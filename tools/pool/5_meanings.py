"""meanings.json from the verified pool: each word's base word and word class come from COR (via the pool build).
Danish: DanNet sense of that word class (complete text), else Danish Wiktionary, else DanNet cut at the last whole word.
English: English Wiktionary gloss of the same word class."""
import csv, json, re, collections
info = json.load(open('w/pool_info.json'))
d = 'w/dl/dannet/'
syn = {r[0]: r[1] for r in csv.reader(open(d + 'synsets.csv')) if len(r) > 1}
words = {r[0]: (r[1], r[2]) for r in csv.reader(open(d + 'words.csv'))}
by = collections.defaultdict(list)
for r in csv.reader(open(d + 'senses.csv')):
    if r[2] in words and syn.get(r[1]):
        m = re.match(r'sense-(\d+)(?:-i(\d+))?$', r[0])
        if m: by[words[r[2]][0]].append((int(m.group(1)), int(m.group(2) or 0), words[r[2]][1], syn[r[1]]))
en = json.load(open('w/en.json')); da = json.load(open('w/da.json'))
DN = {'sb': 'noun', 'vb': 'verb', 'adj': 'adjective'}
KK = {'sb': 'noun', 'vb': 'verb', 'adj': 'adj'}
def tidy(t):
    t = t.replace('e.l.', 'eller lignende'); t = re.sub(r'\bel\.', 'eller', t); t = re.sub(r'\bbl\.a\.', 'blandt andet', t)
    t = re.sub(r'\bevt\.', 'eventuelt', t); t = re.sub(r'\bpers\.', 'person', t); t = re.sub(r'\bfx\b', 'for eksempel', t)
    if t.endswith('…'):
        t = t[:-1]; t = t[:t.rfind(' ')] if ' ' in t else t
        t = t.rstrip(' ,;(') + ' …'
    return t[:1].upper() + t[1:]
def danish(lemma, p):
    ss = sorted(s for s in by.get(lemma, []) if s[2] == DN[p])
    if ss and not ss[0][3].endswith('…'): return tidy(ss[0][3])
    if da.get(lemma): return da[lemma][0]
    if ss: return tidy(ss[0][3])
    return ''
def english(lemma, p):
    return en['enpos'].get(lemma, {}).get(KK[p], '')
W, L, st = {}, {}, collections.Counter()
for w, i in info.items():
    lem, p = i['lemma'], i['pos']
    key = lem + '|' + p
    if key not in L:
        L[key] = [danish(lem, p), english(lem, p)]
    if L[key][0] or L[key][1]:
        W[w] = key; st['word'] += 1
    else:
        # no entry for the word itself: explain its parts (compounds), each with its own entry
        parts = []
        for part in i['parts']:
            for pp in ('sb', 'vb', 'adj'):
                k2 = part + '|' + pp
                t = [danish(part, pp), english(part, pp)] if part in by or part in en['enpos'] or part in da else ['', '']
                if t[0] or t[1]: L[k2] = t; parts.append(k2); break
        if len(parts) >= 2 and len(parts) == len(i['parts']): W[w] = parts; st['parts'] += 1
        else: st['none'] += 1
L = {k: v for k, v in L.items() if v[0] or v[1]}
print(st, 'entries', len(L), 'danish', sum(1 for v in L.values() if v[0]))
json.dump({'w': W, 'l': L}, open('/Users/saschaawhaber/ord-et/meanings.json', 'w'), ensure_ascii=False, separators=(',', ':'))
for w in ['siver', 'øget', 'huset', 'sognepræsten', 'kendte', 'slår', 'vejen', 'udløbsdatoen', 'lærere', 'skriver']:
    k = W.get(w); print(w, k, [L.get(x) for x in (k if isinstance(k, list) else [k])] if k else None)
