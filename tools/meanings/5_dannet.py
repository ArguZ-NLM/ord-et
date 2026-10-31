import csv,json,collections,re
d='w/dl/dannet/'
syn={r[0]:r[1] for r in csv.reader(open(d+'synsets.csv')) if len(r)>1}
words={r[0]:(r[1],r[2]) for r in csv.reader(open(d+'words.csv'))}
by=collections.defaultdict(list)
for r in csv.reader(open(d+'senses.csv')):
    s,sy,wd=r[0],r[1],r[2]
    if wd in words and syn.get(sy):
        m=re.match(r'sense-(\d+)(?:-i(\d+))?$',s)
        if m: by[words[wd][0]].append((int(m.group(1)),int(m.group(2) or 0),words[wd][1],syn[sy]))
en=json.load(open('w/en.json')); VERB=set(en['verb']); LP=en['lempos']
PMAP={'noun':'noun','name':'noun','verb':'verb','adj':'adjective','adv':'adverb'}
D=json.load(open('w/meaning.json'))
def tidy(t):
    t=t.replace('e.l.','eller lignende'); t=re.sub(r'\bel\.','eller',t); t=re.sub(r'\bbl\.a\.','blandt andet',t); t=re.sub(r'\bevt\.','eventuelt',t); t=re.sub(r'\bpers\.','person',t)
    if t.endswith('…'):
        t=t[:-1]; t=t[:t.rfind(' ')] if ' ' in t else t
        t=re.sub(r'[\s,;(]+\w{0,2}$','',t).rstrip(' ,;(') + ' …'
    return t[0].upper()+t[1:] if t else t
stats=collections.Counter(); out={}
for l,(da,enl) in D['l'].items():
    ss=sorted(by.get(l,[]))
    if not ss: out[l]=[da[0] if da else '',enl[0] if enl else '']; stats['no dannet']+=1; continue
    # the word class with most senses in DanNet is the main one (slå: verb, not the bolt); ties go to Wiktionary's first entry
    cnt=collections.Counter(s[2] for s in ss); first=PMAP.get(LP.get(l))
    want=max(cnt,key=lambda p:(cnt[p],p==first))
    ss=[s for s in ss if s[2]==want]
    inv={v:k for k,v in PMAP.items() if k!='name'}
    eg=en['enpos'].get(l,{}).get(inv.get(want))
    if eg: enl=[eg]
    full=[s for s in ss if not s[3].endswith('…')]
    main=ss[0]
    if not main[3].endswith('…'): t=tidy(main[3]); stats['dannet full']+=1
    elif da: t=da[0]; stats['wiktionary']+=1
    else: t=tidy(main[3]); stats['dannet cut']+=1
    out[l]=[t,enl[0] if enl else '']
print(stats)
json.dump({'w':D['w'],'l':out},open('/Users/saschaawhaber/ord-et/meanings.json','w'),ensure_ascii=False,separators=(',',':'))
for w in ['vej','sive','øge','hus','bil','hund','læse','glad','fodbold','venstreorienteret','orientere','tyv','skrive','kende']: print(w,'|',out.get(w))
