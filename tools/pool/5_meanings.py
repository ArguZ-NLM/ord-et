"""meanings.json: what each pool word means, only from published sources, for the word's own word class.

Base word and word class: from COR (the form's own grammatical tag). When a form belongs to more than one base word
(livet: liv or live), the split's own reading tag decides if it has one (snit-t-et sb=snit), else the more common
base word (wordfreq).
Danish, in this order, always for that word class:
  1. Danish Wiktionary, first definition in the section for that word class: the main meaning (CC BY-SA 4.0)
  2. DanNet, complete definition of the word's most connected sense (synset-indegree.edn) (DSL & CST, CC BY-SA 4.0)
  3. DanNet, definition cut short by DanNet itself (ends in …)
A form COR knows under a base word the sources do not have (gymnasiet: COR gymnasie, Wiktionary gymnasium)
uses the base word that English Wiktionary names for that form ("definite singular of gymnasium").
English: English Wiktionary via kaikki.org, first gloss for that word class (CC BY-SA 4.0).
No Danish text → the page shows the English one, marked "på engelsk". No text at all → no meaning is shown.
Nothing is written by hand. Every text is shortened to one line (60 characters): the first sentence, then the part
before ";", then without (…), then up to a comma, and only as a last resort cut at a whole word with " …".

Run with python3 -I (wordfreq installed) from a folder with w/dl/: cor1.5.1.0.tsv, dannet/ (dannet-csv.zip), synset-indegree.edn,
dawiktionary-latest-pages-articles.xml, kaikki.org-dictionary-Danish.jsonl. Repo path as argument (default ../ord-et).
"""
import collections, csv, html, json, re, sys
from wordfreq import zipf_frequency

REPO = sys.argv[1] if len(sys.argv) > 1 else '../ord-et'
DL = 'w/dl/'
LIMIT = 60
POS = ('sb', 'vb', 'adj')

# ---------- pool ----------
src = open(REPO + '/index.html', encoding='utf-8').read()
i = src.index('const AUTO = '); j = src.index('\n', i)
auto = json.loads(src[i + 13:j].rstrip(';'))
b = src[src.index('const BUILTIN = ['):i]
pool, tagged = [], {}
for v in auto.values():
    for line in v.split('\n'):
        first = line.split(' / ')[0].split(' ')
        w = ''.join(first[0].split('-')); pool.append(w)
        if len(first) > 2 and '=' in first[2]: cls, base = first[2].split('='); tagged[w] = base + '|' + cls
for m in re.finditer(r'^\s*([a-zæøå][a-zæøå|+\-·]*)(\s+[FRABLD]+)?\s*(;|/|$)', b, re.M):
    w = re.sub(r'[|+\-·]', '', m.group(1))
    if len(w) > 1: pool.append(w)
pool = list(dict.fromkeys(pool))

# ---------- COR: base word + word class of each form ----------
forms = collections.defaultdict(list)
for line in open(DL + 'cor1.5.1.0.tsv', encoding='utf-8'):
    c = line.rstrip('\n').split('\t')
    if len(c) < 6: continue
    p = c[3].split('.')[0]
    if p in POS and not c[3].endswith('.sms'):
        k = c[1] + '|' + p
        if k not in forms[c[4]]: forms[c[4]].append(k)

# ---------- DanNet ----------
d = DL + 'dannet/'
syn = {r[0]: r[1] for r in csv.reader(open(d + 'synsets.csv', encoding='utf-8')) if len(r) > 1}
dwords = {r[0]: (r[1], r[2]) for r in csv.reader(open(d + 'words.csv', encoding='utf-8'))}
DN = {'sb': 'noun', 'vb': 'verb', 'adj': 'adjective'}
indeg = {m.group(1): int(m.group(2)) for m in re.finditer(r':dn/(synset-[\w-]+) (\d+)', open(DL + 'synset-indegree.edn').read())}
dannet = collections.defaultdict(list)          # "lemma|pos" -> [(-indegree, sense no, text)]
for r in csv.reader(open(d + 'senses.csv', encoding='utf-8')):
    if r[2] in dwords and syn.get(r[1]):
        m = re.match(r'sense-(\d+)(?:-i(\d+))?$', r[0])
        lem, dp = dwords[r[2]]
        p = next((k for k, v in DN.items() if v == dp), None)
        if m and p: dannet[lem + '|' + p].append((-indeg.get(r[1], 0), int(m.group(1)), syn[r[1]]))

# ---------- Danish Wiktionary: first definition per word class ----------
WK = {'noun': 'sb', 'verb': 'vb', 'adj': 'adj'}
def wclean(s):
    s = html.unescape(s).strip()
    s = re.sub(r"^''\(?([^'()]+)\)?''\s*:?\s*", r'(\1) ', s)
    s = re.sub(r'<ref.*?(</ref>|/>)', '', s, flags=re.S); s = re.sub(r'<[^>]+>', '', s)
    s = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r'\1', s)
    s = re.sub(r'\{\{(?:l|term|ord)\|[^|}]*\|([^|}]*)[^}]*\}\}', r'\1', s)
    s = re.sub(r'\{\{[^{}]*\}\}', '', s); s = s.replace("'''", '').replace("''", '')
    s = re.sub(r'^\((grundbetydning|generelt|almindeligt)\) ', '', s)
    return re.sub(r'\s+', ' ', s).strip(' ;,:')
dawik = {}
x = open(DL + 'dawiktionary-latest-pages-articles.xml', encoding='utf-8').read()
for t, body in re.findall(r'<title>(.*?)</title>.*?<text[^>]*>(.*?)</text>', x, re.S):
    if ':' in t: continue
    body = html.unescape(body)
    # the Danish section ends where the next language starts: {{=sv=}} or {{-cs-}}
    m = re.search(r'\{\{=da=\}\}(.*?)(?=\{\{=[a-z-]+=\}\}|\{\{-[a-z]{2,3}-\}\}|$)', body, re.S)
    if not m: continue
    cur = None
    for line in m.group(1).split('\n'):
        # word class headings: {{-noun-|da}} or ===Substantiv===
        h = re.match(r'\{\{-(noun|verb|adj)-\|da\}\}', line) or re.match(r'=+\s*(Substantiv|Verbum|Adjektiv)\s*=+', line)
        if h: cur = {'noun': 'sb', 'verb': 'vb', 'adj': 'adj', 'Substantiv': 'sb', 'Verbum': 'vb', 'Adjektiv': 'adj'}[h.group(1)]; continue
        if re.match(r'\{\{-[a-z]+-\|da\}\}|=+\s*[A-ZÆØÅ][a-zæøå]+\s*=+\s*$', line) and not re.match(r'=+\s*(Etymologi|Udtale)', line):
            cur = None; continue   # another word class (adverb, name …)
        if cur and re.match(r'#[^:*#]', line):
            dd = wclean(line[1:])
            if len(dd) > 2 and not re.match(r'(bøjningsform|flertal|ental|datid|nutid|form) af\b', dd, re.I):
                dawik.setdefault(t + '|' + cur, dd)
del x

# ---------- English Wiktionary (kaikki) ----------
KK = {'noun': 'sb', 'verb': 'vb', 'adj': 'adj'}
BAD = re.compile(r'(Only used|see |Alternative|Obsolete|Archaic|Misspelling|Clipping|Abbreviation|initialism)', re.I)
enwik, formof = {}, collections.defaultdict(list)   # formof: "gymnasiet" -> ["gymnasium|sb"]
for line in open(DL + 'kaikki.org-dictionary-Danish.jsonl', encoding='utf-8'):
    e = json.loads(line); p = KK.get(e.get('pos'))
    if not p: continue
    k = e['word'] + '|' + p
    for s in e.get('senses', []):
        fo = s.get('form_of') or s.get('alt_of')
        if fo:
            t = fo[0]['word'] + '|' + p
            if t not in formof[e['word']]: formof[e['word']].append(t)
            continue
        if 'form-of' in s.get('tags', []) or k in enwik: continue
        if s.get('glosses') and not BAD.match(s['glosses'][-1]): enwik[k] = s['glosses'][-1]

# ---------- text ----------
def tidy(t):
    t = t.replace('e.l.', 'eller lignende'); t = re.sub(r'\bel\.', 'eller', t); t = re.sub(r'\bbl\.a\.', 'blandt andet', t)
    t = re.sub(r'\bevt\.', 'eventuelt', t); t = re.sub(r'\bpers\.', 'person', t); t = re.sub(r'\bvedr\.', 'vedrørende', t)
    return t
def one_line(t, da=True):
    t = re.sub(r'\s+', ' ', t).strip()
    if da:
        t = re.sub(r'^(At|En|Et) (?=\w)', '', t)
        t = t.replace('for eksempel', 'fx').replace('eller lignende', 'o.l.').replace('blandt andet', 'bl.a.')
        if t[:1].isupper() and not t[1:2].isupper(): t = t[:1].lower() + t[1:]
    cut = t.endswith('…'); t = t.rstrip(' …')
    if len(t) > LIMIT: t = re.split(r'(?<=[.!?])\s+(?=[A-ZÆØÅa-zæøå(„"])', t)[0]
    if len(t) > LIMIT: t = t.split('; ')[0]
    if len(t) > LIMIT: t = re.sub(r'\s*\([^)]*\)', '', t).strip()
    if len(t) > LIMIT:
        c = t.rfind(', ', 0, LIMIT)
        if c >= 20: t = t[:c]
        else: t = t[:t.rfind(' ', 0, LIMIT - 2)].rstrip(' ,;:–-'); cut = True
    t = t.rstrip('.') if not t.endswith('..') else t
    return t + (' …' if cut else '')
def danish(k):
    if k in dawik: return dawik[k], 'wiktionary'
    ss = sorted(dannet.get(k, []))
    full = [s for s in ss if not s[2].endswith('…')]
    if full: return tidy(full[0][2]), 'dannet'
    if ss: return tidy(ss[0][2]), 'dannet (cut)'
    return '', None

# ---------- choose the base word and build ----------
def readings(w):
    rs = list(forms.get(w, []))
    if w in tagged and tagged[w] in rs: return [tagged[w]] + [r for r in rs if r != tagged[w]]
    return sorted(rs, key=lambda k: -zipf_frequency(k.split('|')[0], 'da'))
W, L, st = {}, {}, collections.Counter()
for w in pool:
    rs = readings(w) or [w + '|sb']
    # the most likely reading that has any text (a Danish one, else English): never a less likely base word
    # just because it happens to have a Danish text
    pick = next((k for k in rs if danish(k)[0] or k in enwik), None)
    if not pick:   # the base word under another spelling, as English Wiktionary names it for this form or base word
        alt = formof.get(w, []) + [t for r in rs for t in formof.get(r.split('|')[0], []) if t.split('|')[1] == r.split('|')[1]]
        pick = next((k for k in alt if danish(k)[0] or k in enwik), None)
    if not pick: st['none'] += 1; continue
    if pick not in L:
        da, s = danish(pick)
        L[pick] = [one_line(da) if da else '', one_line(enwik.get(pick, ''), False)]
        st['src ' + (s or 'english only')] += 1
    W[w] = pick
json.dump({'w': W, 'l': L}, open(REPO + '/meanings.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(len(pool), 'words;', len(W), 'with a meaning;', dict(st))
