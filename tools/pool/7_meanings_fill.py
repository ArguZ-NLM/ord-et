"""Run after 5_meanings.py (and 6_readings.py): every pool word gets a meaning, and every meaning fits on one line.

1. A pool word with no meaning, or only an English one, takes the hand-written meaning in meanings_extra.json
   (key = base word|word class from COR; a compound without its own entry uses the whole word, e.g. træningskamp|sb).
2. Every Danish and English text is cut to one line: the first sentence, then the first part before ";",
   then without (…), then at the last comma, and only as a last resort at a whole word with " …".
Run with python3 -I from the folder with w/dl/cor1.5.1.0.tsv and the repo as ../ord-et (or pass the repo path).
"""
import collections, json, re, sys

REPO = sys.argv[1] if len(sys.argv) > 1 else '../ord-et'
LIMIT = 60
DL = 'w/dl/'

src = open(REPO + '/index.html', encoding='utf-8').read()
i = src.index('const AUTO = '); j = src.index('\n', i)
auto = json.loads(src[i + 13:j].rstrip(';'))
pool = [''.join(l.split(' ')[0].split('-')) for v in auto.values() for l in v.split('\n')]

forms = collections.defaultdict(list)
for line in open(DL + 'cor1.5.1.0.tsv', encoding='utf-8'):
    c = line.rstrip('\n').split('\t')
    if len(c) < 6: continue
    p = c[3].split('.')[0]
    if p in ('sb', 'vb', 'adj') and not c[3].endswith('.sms'): forms[c[4]].append(c[1] + '|' + p)

extra = {k: v for k, v in json.load(open(REPO + '/tools/pool/meanings_extra.json', encoding='utf-8')).items() if k != '_'}
M = json.load(open(REPO + '/meanings.json', encoding='utf-8'))
W, L = M['w'], M['l']

def one_line(t):
    t = re.sub(r'\s+', ' ', t).strip()
    # dictionary style: no "At"/"En"/"Et" in front, and the usual short forms
    t = re.sub(r'^(At|En|Et) (?=\w)', '', t)
    t = t.replace('for eksempel', 'fx').replace('eller lignende', 'o.l.').replace('blandt andet', 'bl.a.')
    if t[:1].isupper() and not t[1:2].isupper(): t = t[:1].lower() + t[1:]
    if len(t) > LIMIT: t = re.split(r'(?<=[.!?])\s+(?=[A-ZÆØÅ(„"])', t)[0]
    if len(t) > LIMIT: t = t.split('; ')[0]
    if len(t) > LIMIT: t = re.sub(r'\s*\([^)]*\)', '', t).strip()
    if len(t) > LIMIT:
        c = t.rfind(', ', 0, LIMIT)
        if c >= 20: t = t[:c]
        else: t = t[:t.rfind(' ', 0, LIMIT - 2)].rstrip(' ,;:–-') + ' …'
    if t.endswith('.') and not t.endswith('..'): t = t[:-1]
    return t

st = collections.Counter()
for w in dict.fromkeys(pool):
    k = W.get(w)
    if isinstance(k, str) and L.get(k, [''])[0]: continue
    cands = ([k] if isinstance(k, str) else []) + list(dict.fromkeys(forms.get(w, []))) + [w + '|sb']
    hit = next((c for c in cands if c in extra), None)
    if hit:
        L[hit] = [extra[hit][0], extra[hit][1] or L.get(hit, ['', ''])[1]]
        W[w] = hit; st['filled'] += 1
    else:
        st['still none' if not isinstance(k, str) else 'english only'] += 1
for k, v in L.items():
    L[k] = [one_line(v[0]), one_line(v[1])]
L = {k: v for k, v in L.items() if v[0] or v[1]}
json.dump({'w': W, 'l': L}, open(REPO + '/meanings.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(dict(st), 'longest', max(len(v[0]) for v in L.values()))
