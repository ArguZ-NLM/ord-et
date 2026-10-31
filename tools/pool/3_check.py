"""Rebuild the word pool from authoritative data.

Every word must be an official form in COR (Det Centrale Ordregister, Dansk Sprognævn, CC0).
Its inflection is read from COR (lemma + grammatical form), not guessed.
Every split inside the stem (compound, prefix, suffix) must be possible by COR
(both parts are COR words; a linking letter must match COR's official compound form)
AND confirmed by Wiktionary's etymology or by DanNet (definition or hypernym names the part).
A word whose stem *could* be split but whose split is not confirmed is dropped.
"""
import csv, json, re, collections, sys

DL = 'w/dl/'
F_LIST = ['under', 'over', 'for', 'ind', 'gen', 'mis', 'med', 'til', 'be', 'ud', 'op', 'af', 'om', 'an', 'u']
A_LIST = ['skab', 'else', 'ning', 'inde', 'dom', 'hed', 'ing', 'lig', 'som', 'bar', 'løs', 'ske', 'ig', 'er']
B_SET = {'e', 'er', 'r', 'en', 'n', 'et', 't', 'ne', 'ene', 's', 'ede', 'te', 'de', 'ende', 'est', 'st', 'ere'}
VOW = set('aeiouyæøå')

# ---------- COR ----------
forms = collections.defaultdict(list)     # form -> [(lid, tag)]
lem = {}                                   # lid -> lemma
pos = {}                                   # lid -> sb|vb|adj
para = collections.defaultdict(lambda: collections.defaultdict(list))  # lid -> tag -> [forms]
sms = collections.defaultdict(list)        # lid -> compound forms
by_lemma = collections.defaultdict(list)   # lemma -> [lid]
GENERATED = set()                          # (form, lid, tag) that COR marks U: generated comparison/adverb forms
FUNCTION_FORMS = set()                     # forms that are also adverbs, pronouns … (hans, mens, under, fire)
LOAN_PREFIX = set()                        # super-, mikro-, anti- … (not in the rule book: words with them are dropped)
for line in open(DL + 'cor1.5.1.0.tsv', encoding='utf-8'):
    c = line.rstrip('\n').split('\t')
    if len(c) < 6: continue
    cid, lemma, _, tag, form, status = c[:6]
    lid = '.'.join(cid.split('.')[:2])
    p = tag.split('.')[0]
    # status U is only used for regular comparison and adverb forms of adjectives (højere, billigste): kept
    if p == 'præfiks':
        LOAN_PREFIX.add(form.rstrip('-'))
    if p not in ('sb', 'vb', 'adj'):
        # adverbs, prepositions, numerals …: possible first parts of compounds (hjemme-side, tre-kant)
        if p in ('adv', 'præp', 'talord', 'pron', 'konj', 'udråbsord', 'art', 'infmærke'): FUNCTION_FORMS.add(form)
        if p in ('adv', 'præp', 'talord', 'pron', 'konj') and re.fullmatch(r'[a-zæøå]+', lemma):
            olid = 'X.' + lemma; lem[olid] = lemma; pos[olid] = 'other'
            if olid not in by_lemma[lemma]: by_lemma[lemma].append(olid)
        continue
    lem[lid] = lemma; pos[lid] = p
    if lid not in by_lemma[lemma]: by_lemma[lemma].append(lid)
    if tag.endswith('.sms'):
        sms[lid].append(form.rstrip('-')); continue
    para[lid][tag].append(form)
    forms[form].append((lid, tag))
    if status == 'U': GENERATED.add((form, lid, tag))

def stem(lid):
    if pos[lid] == 'vb':
        inf = (para[lid].get('vb.inf.akt') or [lem[lid]])[0]
        imp = (para[lid].get('vb.imp') or [inf])[0]
        # skrive -> skriv, spille -> spill (imp spil); ske, se, gå -> the whole word
        if inf.endswith('e') and imp in (inf[:-1], inf[:-2]) and len(inf) > 2: return inf[:-1]
        return imp if imp else inf
    return lem[lid]

stems = collections.defaultdict(set)       # stem string -> lids
for lid in lem:
    if pos[lid] == 'other': continue      # adverbs etc. only as first parts of compounds (looked up by_lemma)
    stems[stem(lid)].add(lid); stems[lem[lid]].add(lid)
    for imp in para[lid].get('vb.imp', []): stems[imp].add(lid)
sms_index = collections.defaultdict(set)   # official compound form -> noun lids
for lid, ff in sms.items():
    for f in ff: sms_index[f].add(lid)

# ---------- frequency ----------
FREQ = {}
for l in open(DL + 'wordfreq_da.txt', encoding='utf-8'):
    p = l.split()
    if len(p) == 2: FREQ[p[0]] = int(p[1])

# ---------- evidence: Wiktionary etymology ----------
ETY = collections.defaultdict(list)        # word -> list of part-sets
for l in open(DL + 'kaikki.org-dictionary-Danish.jsonl', encoding='utf-8'):
    e = json.loads(l)
    for t in e.get('etymology_templates', []):
        if t['name'] in ('af', 'affix', 'compound', 'com', 'suffix', 'suf', 'prefix', 'pre', 'surf', 'confix', 'con'):
            a = t.get('args', {})
            if a.get('1') != 'da': continue
            raw = [re.sub(r'<.*?>', '', v).strip() for k, v in sorted(a.items()) if k.isdigit() and k != '1']
            raw = [r for r in raw if r]
            kind = 'suf' if t['name'] in ('suffix', 'suf') else 'pre' if t['name'] in ('prefix', 'pre') else None
            if raw: ETY[e['word']].append((kind, raw))

BORROWED = set()
for l in open(DL + 'kaikki.org-dictionary-Danish.jsonl', encoding='utf-8'):
    if '"bor' not in l and 'borrowing' not in l: continue
    e = json.loads(l)
    names = [t['name'] for t in e.get('etymology_templates', [])]
    if any(n in ('bor', 'ubor', 'lbor', 'slbor', 'bor+', 'learned borrowing') for n in names[:2]) and \
       not any(n in ('af', 'affix', 'compound', 'com', 'suffix', 'suf', 'prefix', 'pre', 'surf') for n in names):
        BORROWED.add(e['word'])

# ---------- evidence: DanNet ----------
D = DL + 'dannet/'
syn_def = {r[0]: r[1] for r in csv.reader(open(D + 'synsets.csv', encoding='utf-8')) if len(r) > 1}
wd = {r[0]: r[1] for r in csv.reader(open(D + 'words.csv', encoding='utf-8'))}
word_syns = collections.defaultdict(set); syn_words = collections.defaultdict(set)
for r in csv.reader(open(D + 'senses.csv', encoding='utf-8')):
    if r[2] in wd: word_syns[wd[r[2]]].add(r[1]); syn_words[r[1]].add(wd[r[2]])
hyper = collections.defaultdict(set)
for r in csv.reader(open(D + 'relations.csv', encoding='utf-8')):
    if len(r) >= 3 and r[1].endswith('hypernym') and not r[1].endswith('_hypernym'):
        hyper[r[0]].add(r[2])

# ---------- evidence: COR.SEM (Dansk Sprognævn / DSL): category and related words per sense ----------
SEM_HYP = collections.defaultdict(set); SEM_REL = collections.defaultdict(set)
for line in open(DL + 'cor.sem.1.0.tsv', encoding='utf-8'):
    c = line.rstrip('\n').split('\t')
    if len(c) < 14: continue
    w = c[5]
    SEM_HYP[w] |= {x.strip() for x in re.split(r'[|;]', c[10]) if x.strip()}
    SEM_REL[w] |= {x.strip() for x in re.split(r'[|;]', c[12] + '|' + c[13]) if x.strip() and ' ' not in x.strip()}

def tokens(lemma):
    out = set()
    for s in word_syns.get(lemma, ()):
        out |= set(re.findall(r'[a-zæøåé]+', syn_def.get(s, '').lower()))
    return out

def hyper_words(lemma):
    out = set()
    for s in word_syns.get(lemma, ()):
        frontier = {s}
        for _ in range(2):
            nxt = set()
            for f in frontier: nxt |= hyper.get(f, set())
            for h in nxt: out |= syn_words.get(h, set())
            frontier = nxt
    return out

def ety_says(lemma, a, b, kind='com'):
    """Wiktionary lists both parts in one template. kind: 'com' (two words), 'pre' (b is the prefix's word), 'suf' (b is a suffix)"""
    for k, raw in ETY.get(lemma, []):
        bare = {r.strip('-') for r in raw}
        if kind == 'com':
            # the head must be a word, not a suffix (-lig) or interfix (-s-)
            heads = {r for r in raw if not r.startswith('-')}
            firsts = {r for r in raw if not r.endswith('-')}      # und- is a prefix, not a word
            if k not in ('suf', 'pre') and firsts & a and heads & b: return True
        elif kind == 'suf':
            sufs = {r.strip('-') for r in raw if r.startswith('-')} | ({raw[-1].strip('-')} if k == 'suf' else set())
            if bare & a and sufs & b: return True
        elif kind == 'pre':
            pres = {r.strip('-') for r in raw if r.endswith('-') and not r.startswith('-')} | ({raw[0].strip('-')} if k == 'pre' or raw[0] in F_LIST else set())
            if pres & a and bare & b: return True
    return False

def dannet_head(lemma, head_forms):
    """DanNet's definition or a hypernym (2 levels) names the head part (the word itself does not count)"""
    heads = {h for h in head_forms if len(h) >= 3}
    if not heads: return False
    for t in tokens(lemma) | hyper_words(lemma):
        if lemma in t: continue
        for h in heads:
            if t == h or (len(h) >= 4 and len(t) > len(h) and (t.startswith(h) or t.endswith(h))): return True
    return False

def named(lemma, part_forms, pool):
    ps = {p for p in part_forms if len(p) >= 3}
    for t in pool:
        if lemma in t: continue
        for p in ps:
            if t == p or (len(p) >= 4 and len(t) > len(p) and (t.startswith(p) or t.endswith(p))): return True
    return False

def dannet_exact(lemma, part_forms):
    """DanNet's definition or category uses the part as a whole word (udløb: vandløb is not enough … but løb is)"""
    ps = {p for p in part_forms if len(p) >= 3}
    hyp = hyper_words(lemma) | SEM_HYP.get(lemma, set())
    pool = tokens(lemma) | hyp
    return any(p in pool for p in ps) or any(h.endswith(p) and len(h) > len(p) + 2 for h in hyp for p in ps)

def dannet_compound(lemma, a_forms, b_forms):
    """DanNet names both parts, or has the second part as the word's category (lastbil is a kind of bil)"""
    defs, hyp = tokens(lemma), hyper_words(lemma) | SEM_HYP.get(lemma, set())
    rel = SEM_REL.get(lemma, set())
    return named(lemma, b_forms, defs | hyp | rel) and named(lemma, a_forms, defs | hyp | rel)

# ---------- stem analysis ----------
memo = {}
DEBUG = False   # True prints each stem analysis
def analyze(lid, depth=0):
    """-> (segs, types, parts) | 'atomic' handled as 1 seg | None when a possible split is unconfirmed"""
    if lid in memo: return memo[lid]
    if pos[lid] == 'other': return ([lem[lid]], ['R'], [lem[lid]])
    if lem[lid] in BORROWED:            # låneord deles ikke (computer, database, biologi)
        memo[lid] = ([stem(lid)], ['R'], [lem[lid]]); return memo[lid]
    memo[lid] = None
    s, L = stem(lid), lem[lid]
    confirmed, possible = [], False
    ambiguous = set()      # first parts that could be a verb stem + e or a noun in -e (spise-bord / spis-e-bord)

    def sub(lid2):
        return analyze(lid2, depth + 1) if depth < 4 else ([stem(lid2)], ['R'], [lem[lid2]])

    for f in LOAN_PREFIX:
        if len(f) >= 3 and s.startswith(f) and len(s) - len(f) >= 3 and (s[len(f):] in stems or s[len(f):] in forms): possible = True
    # prefix
    for f in F_LIST:
        if s.startswith(f) and len(s) - len(f) >= 2:
            rest = s[len(f):]
            for lid2 in stems.get(rest, ()):
                possible = True
                regular = (pos[lid] == 'vb' and pos[lid2] == 'vb' and FREQ.get(lem[lid2], 0) >= 100) or \
                          (f == 'u' and pos[lid] == 'adj' and pos[lid2] == 'adj')
                if regular or ety_says(L, {f}, {lem[lid2], rest}, 'pre') or (len(rest) >= 3 and rest not in A_LIST and dannet_exact(L, {lem[lid2], rest})):
                    r = sub(lid2)
                    if r: confirmed.append(([f] + r[0], ['F'] + r[1], [lem[lid2]], 'pre'))
    # suffix
    for a in A_LIST:
        if s.endswith(a) and len(s) - len(a) >= 2:
            root = s[:-len(a)]
            for lid2 in stems.get(root, ()):
                if lid2 == lid: continue
                possible = True
                if ety_says(L, {lem[lid2], root}, {a}, 'suf') or dannet_head(L, {lem[lid2]} if len(root) >= 3 else set()) and a in ('hed', 'lig', 'ning', 'else', 'skab'):
                    r = sub(lid2)
                    if r: confirmed.append((r[0] + [a], r[1] + ['A'], [lem[lid2]], 'suf'))
    # compound: first part = official compound form (COR) of a noun, a verb stem (+e), an adjective, or any other word
    for i in range(2, len(s) - 2):
        p1, p2 = s[:i], s[i:]
        if p1 in F_LIST: continue      # for, med, over … are always prefixes (forstavelser), never roots
        if p1 in LOAN_PREFIX: possible = True; continue   # bio-, mikro- … are not in the rule book
        heads = stems.get(p2, set())
        if len(p2) >= 4 and len(p1) >= 3 and not heads and (p1 in stems or p1 in sms_index or p1 in by_lemma):
            if p2 in forms or any(p2.endswith(a) and p2[:-len(a)] in stems for a in A_LIST) or any(p2.startswith(f) and p2[len(f):] in stems for f in F_LIST):
                possible = True
        if not heads or len(p2) < 3: continue
        firsts = []   # (root1, link, lid1, official): official = p1 is listed by COR as the word's compound form
        for lid1 in stems.get(p1, set()) | set(by_lemma.get(p1, [])):
            if pos[lid1] == 'sb':
                if p1 in sms.get(lid1, []): firsts.append((p1, None, lid1, True))
                elif not sms.get(lid1) and p1 == lem[lid1] and len(p1) >= 3: firsts.append((p1, None, lid1, True))   # no listed compound form: the word itself (tand-, post-)
            elif pos[lid1] == 'adj' and p1 == lem[lid1] and len(p1) >= 3:
                firsts.append((p1, None, lid1, True))
            elif pos[lid1] == 'vb' and p1 == stem(lid1) and len(p1) >= 2:
                firsts.append((p1, None, lid1, False))      # gå-tur, tø-sne (only Wiktionary or the category can confirm)
            elif pos[lid1] == 'other' and p1 not in F_LIST and len(p1) >= 2:
                firsts.append((p1, None, lid1, False))   # adverb/pronoun first part: only Wiktionary can confirm (man-dag is not 'man')
        if len(p1) >= 3 and p1[-1] in 'se':
            r1, link = p1[:-1], p1[-1]
            for lid1 in sms_index.get(p1, ()):
                L1 = lem[lid1]
                if r1 == L1 and p1 != L1: firsts.append((r1, link, lid1, True))                       # tid-s, hund-e, sogn-e
                elif link == 's' and L1.endswith('e') and r1 == L1[:-1]: firsts.append((r1, link, lid1, True))  # arbejd-s (arbejde)
                elif not L1.startswith(r1) and r1 != L1: firsts.append((r1, link, lid1, True))      # børn-e (barn)
            noun_listed = any(pos[l] == 'sb' for l in sms_index.get(p1, ()))
            verb_common = any(pos[l] == 'vb' and own_use(l) >= 50 for l in stems.get(r1, ()) if stem(l) == r1)
            if noun_listed and verb_common and link == 'e': ambiguous.add(p1)   # bede-mand (beet?) or bed-e-mand (the verb bede)?
            if not noun_listed:   # skole-lærer, not skol-e-lærer (the rare verb at skole)
                for lid1 in stems.get(r1, ()):
                    if pos[lid1] == 'vb' and link == 'e' and r1 == stem(lid1) and len(r1) >= 3:
                        # albue-rum, not albu-e-rum: if p1 is also a noun that is used more than the verb, the e belongs to the noun
                        # fød-e-vare or føde-vare? var-e-tag-e or vare-tag-e? if p1 is also a noun, only the meaning decides: not split
                        if any(pos[l] in ('sb', 'adj') for l in by_lemma.get(p1, [])): ambiguous.add(p1); continue
                        firsts.append((r1, link, lid1, False))  # skriv-e-bord
        for root1, link, lid1, official in firsts:
            if lid1 == lid: continue
            for lid2 in sorted(heads, key=lambda h: pos[h] != pos[lid]):
                if lid2 == lid: continue
                possible = True
                a_forms = {lem[lid1], root1, p1}
                b_forms = {lem[lid2], p2}
                if (p2 in A_LIST or p2 in B_SET) and not ety_says(L, a_forms, b_forms): continue   # -lig, -ende … are endings here, not the nouns lig, ende
                short = len(root1) < 3 or len(p2) < 3
                # category: the word is a kind of the second part (postkasse is a kasse). The first part must then be
                # a verb stem (vask-e-rum, gå-tur) or be named in DanNet/COR.SEM too (man-dag is not 'mane + day')
                defs_all = tokens(L) | hyper_words(L) | SEM_HYP.get(L, set()) | SEM_REL.get(L, set())
                listed = p1 in sms.get(lid1, []) or (link and p1 in sms_index)             # COR lists p1 as this word's compound form (sogne-, tids-)
                common_verb = pos[lid1] == 'vb' and own_use(lid1) >= 50                    # gå-tur, vask-e-rum (not the rare verb mane in man-dag)
                category = pos[lid1] != 'other' and named(L, b_forms if len(p2) >= 3 else set(), hyper_words(L) | SEM_HYP.get(L, set())) and \
                           (listed or common_verb or named(L, a_forms, defs_all))
                if ety_says(L, a_forms, b_forms) or category or (official and not short and dannet_compound(L, a_forms, b_forms)):
                    r1 = sub(lid1); r2 = sub(lid2)
                    if r1 and r2:
                        segs = r1[0] + ([link] if link else []) + r2[0]
                        types = r1[1] + (['L'] if link else []) + r2[1]
                        if ''.join(r1[0]) != root1:
                            if not (link and len(r1[0]) == 1): continue
                            r1 = ([root1], ['R'], r1[2])   # arbejd-s (arbejde), børn-e (barn): the official compound form's root   # børn-e: the changed root is one piece
                            segs = r1[0] + [link] + r2[0]; types = r1[1] + ['L'] + r2[1]
                        confirmed.append((segs, types, [lem[lid1], lem[lid2]], 'com', lid1))
    confirmed = [c for c in confirmed if ''.join(c[0]) == s]
    if any(''.join(c[0]).startswith(a) for c in confirmed for a in ambiguous):
        memo[lid] = None; return None
    # safety net: a word that can be cut into two known words (or prefix + word form) is not proven to be one root
    if not confirmed and not possible:
        for f in F_LIST:
            if s.startswith(f) and len(s) - len(f) >= 3 and (s[len(f):] in stems or s[len(f):] in forms): possible = True
            for a in A_LIST:
                mid = s[len(f):-len(a)] if s.startswith(f) and s.endswith(a) else ''
                if len(mid) >= 3 and mid in stems: possible = True
        for i in range(2, len(s) - 2):
            p1, p2 = s[:i], s[i:]
            if (p1 in stems or p1 in by_lemma or p1 in sms_index or p1 in F_LIST) and (p2 in stems or p2 in forms) and len(p2) >= 3:
                if p2 in A_LIST or p2 in B_SET: continue
                possible = True; break
            # with a linking letter: kend-s-gerning, bemærkelse-s-værdig
            if len(p1) >= 4 and p1[-1] in 'se' and (p1[:-1] in stems or p1[:-1] in by_lemma) and (p2 in stems or p2 in forms) and len(p2) >= 4:
                possible = True; break
        # a stem that ends in a suffix (-lig, -hed, -ning …) is not proven to be one root (fjendtlig, kendsgerning)
        for a in ('lig', 'ig', 'hed', 'ning', 'ing', 'else', 'skab', 'dom', 'som', 'bar', 'løs'):
            if s.endswith(a) and len(s) >= len(a) + 3: possible = True
    if DEBUG: print('  confirmed:', [(c[0], c[3]) for c in confirmed], 'possible:', possible)
    if confirmed:
        # same cuts from several readings of the parts: keep the first (parts of the same word class come first)
        cuts = {tuple(c[0]) for c in confirmed}
        if len(cuts) > 1:
            # prefer the analysis that Wiktionary states outright; else ambiguous
            memo[lid] = None; return None
        c = confirmed[0]; memo[lid] = (c[0], c[1], c[2]); return memo[lid]
    if possible:
        memo[lid] = None; return None
    memo[lid] = ([s], ['R'], [L]); return memo[lid]

# ---------- inflection ----------
def infl(w, lid, tag):
    """-> (base, [endings]) using COR's grammatical tag, or None if irregular / not in the app's ending inventory"""
    p = pos[lid]; s = stem(lid)
    bases = [s]
    if s and s[-1] not in VOW: bases.append(s + s[-1])  # doubled consonant: kop -> kopp-er, smuk -> smukk-e
    if len(s) > 3 and s[-1] == s[-2] and s[-1] not in VOW: bases.append(s[:-1])  # glemme -> glem-te, kendt
    ub = umlaut_base(w, lid, tag)
    if ub: bases.append(ub)
    for b in bases:
        if not w.startswith(b): continue
        x = w[len(b):]
        r = endings(x, p, tag, lid, b)
        if r is not None: return b, r
    return None

def umlaut_base(w, lid, tag):
    """plural root with a changed vowel, taken from COR's own plural form: bog/bøger -> bøg, barn/børn -> børn"""
    if pos[lid] != 'sb' or '.pl.' not in tag + '.': return None
    L = lem[lid]
    for tg, ff in para[lid].items():
        if '.pl.ubest' not in tg or tg.endswith('.gen'): continue
        for P in ff:
            for e in ('er', 'e', ''):
                X = P[:len(P) - len(e)] if e else P
                if e and not P.endswith(e): continue
                if len(X) == len(L) and X != L and sum(a != b for a, b in zip(X, L)) == 1 and \
                   all((a in VOW and b in VOW) for a, b in zip(X, L) if a != b) and w.startswith(X):
                    return X
    return None

def endings(x, p, tag, lid, b):
    t = tag.split('.')
    if p == 'sb':
        gen = t[-1] == 'gen'
        if gen:
            if not x.endswith('s'): return None
            x = x[:-1]
        tail = ['s'] if gen else []
        num = 'sg' if 'sg' in t else 'pl' if 'pl' in t else None
        best = 'best' if 'best' in t else 'ubest' if 'ubest' in t else None
        if num == 'sg' and best == 'ubest': return tail if x == '' else None
        if num == 'sg' and best == 'best': return [x] + tail if x in ('en', 'n', 'et', 't') else None
        if num == 'pl' and best == 'ubest':
            if x == '': return tail
            return [x] + tail if x in ('er', 'r', 'e') else None
        if num == 'pl' and best == 'best':
            # the plural ending comes from COR's own plural form: fisk -> fisk (no ending) -> fisk-ene; bil -> bil-er -> bil-er-ne
            pls = [f for tg, ff in para[lid].items() if '.pl.ubest' in tg and not tg.endswith('.gen') for f in ff]
            for P in pls:
                if not P.startswith(b): continue
                pl = P[len(b):]
                if pl not in ('er', 'r', 'e', ''): continue
                if x == pl + ('ne' if pl else 'ene'):
                    return ([pl] if pl else []) + ['ne' if pl else 'ene'] + tail
            # lærer -> lærere -> lærerne: nouns in -er/-el/-en drop the plural e before -ne
            if x == 'ne' and lem[lid][-2:] in ('er', 'el', 'en') and any(P == b + 'e' for P in pls):
                return ['ne'] + tail
            return None
        return None
    if p == 'adj':
        k = '.'.join(t[1:])
        if k in ('sg.ubest.fk',): return [] if x == '' else None
        if k in ('sg.ubest.itk', 'adv'): return [] if x == '' else (['t'] if x == 't' else None)
        if k in ('sg.best', 'pl'): return [] if x == '' else (['e'] if x == 'e' else None)
        if k in ('kompar', 'adv.kompar'): return ['ere'] if x == 'ere' else None
        if k in ('superl.sg.ubest', 'adv.superl'): return [x] if x in ('est', 'st') else None
        if k in ('superl.sg.best', 'superl.pl'): return [x[:-1], 'e'] if x in ('este', 'ste') else None
        return None
    if p == 'vb':
        k = '.'.join(t[1:])
        if k == 'imp': return [] if x == '' else None
        if k == 'inf.akt': return [] if x == '' else (['e'] if x == 'e' else None)
        if k == 'præs.akt': return [x] if x in ('er', 'r') else None
        if k == 'præt.akt': return [x] if x in ('ede', 'te', 'de') else None
        if k in ('perf.part', 'perf.part.sg.fk', 'perf.part.sg.itk'): return [x] if x in ('et', 't') else None
        if k in ('perf.part.sg.best', 'perf.part.pl'): return [x] if x in ('ede', 'te') else None
        if k == 'præs.part': return [x] if x == 'ende' else None
        return None
    return None

# ---------- lemma frequency (for choosing between readings) ----------
def own_use(lid):
    """how much a word is used, counted only on forms that belong to no other word (bedt for 'bede', not 'beder' = beets)"""
    return sum(FREQ.get(f, 0) for fs in para[lid].values() for f in fs if all(l == lid for l, _ in forms.get(f, [])))

def lid_score(lid, others):
    mine = {f for fs in para[lid].values() for f in fs}
    theirs = {f for o in others for fs in para[o].values() for f in fs}
    uniq = mine - theirs
    return sum(FREQ.get(f, 0) for f in (uniq or mine))

# ---------- word analysis ----------
# words that do not belong in a school exercise (swearing, violence, sex, slurs, drugs)
BLOCK = set('''pis pisse lort røv røvhul fisse kusse pik pikke fuck fucke kneppe knep luder hore horeunge bøsse lesbisk neger perker
svans skid skide skiderik satan fanden fandens helvede helvedes kraftedeme idiot spasser mongol bitch nazist sex sexet sexuel seksuel
voldtage voldtægt voldtægtsforbryder selvmord mord morder myrde dræbe drab narko kokain heroin hash amfetamin
bordel prostitueret prostitution porno pornografi nøgen tissemand patter bryst bryster orgasme sæd kondom
terror terrorist bombe massakre tortur torturere henrette henrettelse kidnappe bortføre gidsel skyde skud pistol gevær riffel våben
sprut fuld druk drukke ludder kælling møgso so svin svinehund narre dumme dum dumrian
åndssvag tøsedreng snigskytte dødsstraf sprængstof sindssyg psykopat
lig onanere mødom jomfru jomfrudom kastrere'''.split())
def blocked(r):
    roots = [sg for sg, t in zip(r['segs'], r['types']) if t == 'R']
    return r['word'] in BLOCK or r['lemma'] in BLOCK or any(p in BLOCK for p in r['parts']) or any(sg in BLOCK for sg in roots)

def analyze_word(w):
    if w in FUNCTION_FORMS: return None, 'også et småord (fx hans, mens, under)'
    rd = [(lid, tag) for lid, tag in forms.get(w, [])]
    if not rd: return None, 'ikke i COR'
    # danskere: a generated comparative of 'dansk' must not beat the real word (plural of 'dansker');
    # but højest: COR's own entry 'højest' cannot be split, so the regular superlative of 'høj' is used
    real = [(l, t) for l, t in rd if (w, l, t) not in GENERATED]
    if real and len(real) < len(rd):
        r = _analyze_readings(w, real)
        if r[0] or r[1] not in ('uregelmæssig bøjning', 'en læsning følger ikke reglerne'): return r
    return _analyze_readings(w, rd)

def _analyze_readings(w, rd):
    lids = list(dict.fromkeys(l for l, _ in rd))
    results = {}
    for lid in lids:
        splits = set()
        for l2, tag in rd:
            if l2 != lid: continue
            r = infl(w, lid, tag)
            if r: splits.add((r[0], tuple(r[1])))
        results[lid] = splits
    scores = {l: lid_score(l, [o for o in lids if o != l]) for l in lids}
    own = {l: own_use(l) for l in lids}
    best = max(lids, key=lambda l: scores[l])
    if not results[best]: return None, 'uregelmæssig bøjning'
    # every reading of the chosen word must fit the rules (essays: genitive fits, but the English plural does not)
    if any(infl(w, best, tag) is None for l2, tag in rd if l2 == best): return None, 'en læsning følger ikke reglerne'
    if len(results[best]) > 1: return None, 'flere mulige delinger'
    base, ends = next(iter(results[best]))
    a = analyze(best)
    if a is None: return None, 'usikker deling af stammen'
    segs, types, parts = a
    if ''.join(segs) != base:
        joined = ''.join(segs)
        last = segs[-1]
        if types[-1] != 'R': return None, 'stamme passer ikke'
        if base == joined + base[-1]: segs = segs[:-1] + [last + base[-1]]                  # kopp-er
        elif base == joined[:-1] and last[-1] == last[-2]: segs = segs[:-1] + [last[:-1]]   # glem-te (glemme)
        elif len(base) == len(joined) and base[:len(joined) - len(last)] == joined[:len(joined) - len(last)] and \
             sum(a != b for a, b in zip(base, joined)) == 1:
            segs = segs[:-1] + [base[len(joined) - len(last):]]                               # bøg-er (bog), børn-ene (barn)
        else: return None, 'stamme passer ikke'
    segs = segs + list(ends); types = types + ['B'] * len(ends)
    # another common reading that splits the word differently -> ambiguous
    cuts = tuple(len(''.join(segs[:i + 1])) for i in range(len(segs) - 1))
    for l in lids:
        if l == best or not results[l]: continue
        # the word is the base form of another word (slags = 'kind', not slag + s): any different split there -> drop
        # only a practically unused reading may split differently (arbejderne: 'the workers' is not rare)
        if own[l] * 50 < max(own[best], 1) and scores[l] * 50 < scores[best] and w != lem[l]: continue
        a2 = analyze(l)
        for b2, e2 in results[l]:
            # the other word's own split is unknown (arbejder: arbejd-er?) -> at least its stem/ending boundary differs
            s2 = (a2[0] if a2 and ''.join(a2[0]) == b2 else [b2]) + list(e2)
            c2 = tuple(len(''.join(s2[:i + 1])) for i in range(len(s2) - 1))
            if c2 != cuts: return None, 'to læsninger med forskellig deling'
    r = {'word': w, 'segs': segs, 'types': types, 'lemma': lem[best], 'pos': pos[best], 'parts': parts}
    if blocked(r): return None, 'ikke egnet til skolebrug'
    return r, None

if __name__ == '__main__':
    for w in sys.argv[1:]:
        print(w, analyze_word(w))
