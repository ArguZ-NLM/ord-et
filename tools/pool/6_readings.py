"""Second pass over the pool in index.html (run after 4_build_pool.py): doubled consonants and words with two readings.

1. Doubled consonant (snit -> snittet): the root stays the word you look up (snit), the ending stays the ending (-et),
   and the extra letter that only shows the short vowel is its own piece, type D:  snit-t-et RDB.
   Only when COR's base word ends in the root without the doubled letter (noun/adjective snit, ven, smuk).
2. A word that COR also reads another way gets every reading as an accepted alternative, tagged with its word class
   and base word (`sb=snit`, `vb=snitte`):
     snittet  -> snit-t-et RDB sb=snit / snitt-et RB vb=snitte        (noun snit, verb snitte)
     tjener   -> tjen-er RB vb=tjene / tjen-er RA sb=tjener           (he serves / a waiter: -er is inflection or derivation)
3. Run with python3 -I from the folder with w/dl/cor1.5.1.0.tsv; it rewrites `const AUTO` in index.html in place.
"""
import collections, json, sys

DL = 'w/dl/'
HTML = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
VOW = set('aeiouyæøå')
# -er nouns that are not "one who / a thing that …" made from the verb: tier (a coin), sveder (a sweater)
NOT_AGENT = {'tier', 'sveder'}
# words COR has as a Danish form, but which a student reads as a name or an English word (signe, header, hamlet),
# or which are too rare to explain: left out of the pool
DROP = set('''signe trine hamlet hamle helmer sander pepper ripper header trigger border popper batter tracker dos res bios
solutions yankees hyper spins stede tilstede sparre mande age'''.split())

forms = collections.defaultdict(list); para = collections.defaultdict(lambda: collections.defaultdict(list)); lem = {}; pos = {}
for line in open(DL + 'cor1.5.1.0.tsv', encoding='utf-8'):
    c = line.rstrip('\n').split('\t')
    if len(c) < 6: continue
    cid, lemma, _, tag, form, status = c[:6]
    lid = '.'.join(cid.split('.')[:2]); p = tag.split('.')[0]
    if p not in ('sb', 'vb', 'adj') or tag.endswith('.sms'): continue
    lem[lid] = lemma; pos[lid] = p; para[lid][tag].append(form); forms[form].append((lid, tag))

def stem(lid):
    if pos[lid] == 'vb':
        inf = (para[lid].get('vb.inf.akt') or [lem[lid]])[0]; imp = (para[lid].get('vb.imp') or [inf])[0]
        if inf.endswith('e') and imp in (inf[:-1], inf[:-2]) and len(inf) > 2: return inf[:-1]
        return imp or inf
    return lem[lid]

def rewrite(line):
    sp, ty = line.split(' ')[:2]
    segs = sp.split('-'); w = ''.join(segs)
    rd = forms.get(w, [])
    alts = [(segs, ty, None)]
    # 1 + 2: doubled consonant on the last root, when only inflection follows
    ri = max(i for i, t in enumerate(ty) if t == 'R')
    g = segs[ri]
    if ri < len(segs) - 1 and set(ty[ri + 1:]) == {'B'} and len(g) >= 3 and g[-1] == g[-2] and g[-1] not in VOW:
        dbl = [l for l, _ in rd if stem(l).endswith(g[:-1]) and not stem(l).endswith(g)]
        plain = [l for l, _ in rd if stem(l).endswith(g)]
        if dbl:
            d = dbl[0]
            new = (segs[:ri] + [g[:-1], g[-1]] + segs[ri + 1:], ty[:ri] + 'RD' + ty[ri + 1:], f'{pos[d]}={lem[d]}')
            if plain:
                p = plain[0]
                alts = [new, (segs, ty, f'{pos[p]}={lem[p]}')]
            else:
                alts = [(new[0], new[1], None)]
    # 2: verb in the present tense that is also a noun in -er (tjener, spiller, leder)
    if ty.endswith('RB') and segs[-1] in ('er', 'r') and w not in NOT_AGENT:
        nouns = [l for l, t in rd if pos[l] == 'sb' and lem[l] == w and t == 'sb.fk.sg.ubest']
        verbs = [l for l, t in rd if pos[l] == 'vb' and t == 'vb.præs.akt']
        if nouns and verbs:
            alts = [(a[0], a[1], a[2] or f'vb={lem[verbs[0]]}') for a in alts]
            alts.append((segs, ty[:-1] + 'A', f'sb={w}'))
    return ' / '.join('-'.join(s) + ' ' + t + (' ' + r if r else '') for s, t, r in alts)

src = open(HTML, encoding='utf-8').read()
i = src.index('const AUTO = '); j = src.index('\n', i)
auto = json.loads(src[i + 13:j].rstrip(';'))
changed = 0
for k, v in auto.items():
    out = []
    for line in v.split('\n'):
        if ''.join(line.split(' ')[0].split('-')) in DROP: changed += 1; continue
        if ' / ' in line or 'D' in line.split(' ')[1]: out.append(line); continue   # already done
        n = rewrite(line); changed += n != line; out.append(n)
    auto[k] = '\n'.join(out)
open(HTML, 'w', encoding='utf-8').write(src[:i] + 'const AUTO = ' + json.dumps(auto, ensure_ascii=False) + ';' + src[j:])
print(changed, 'words rewritten')
