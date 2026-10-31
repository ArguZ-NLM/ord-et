import re,json,html,sys
src=open('/Users/saschaawhaber/ord-et/index.html').read()
A=json.loads(re.search(r'const AUTO = (\{.*?\});\n',src,re.S).group(1))
B=src[src.index('const BUILTIN = ['):src.index('const AUTO =')]
lines=[l for k in A for l in A[k].split('\n')]+[l for t in re.findall(r'text: `(.*?)`',B,re.S) for l in t.split('\n')]
items={}
for l in lines:
    l=l.split(';')[0].strip()
    if not l or l.startswith('#'): continue
    toks=l.split('/')[0].split()
    segs=[s for s in re.split(r'[-|+·]+',toks[0].lower()) if s]; w=''.join(segs)
    ty=list(toks[1].upper()) if len(toks)>1 and len(toks[1])==len(segs) else None
    items.setdefault(w,(segs,ty))
en=json.load(open('w/en.json')); da=json.load(open('w/da.json'))
EN=en['lem']; FORM=en['form']; FS={k:set(v) for k,v in en['fs'].items()}; VERB=set(en['verb']); FORMOF=en['formof']
FRE=re.compile(r'^(?:(?:u?bestemt|imperativ|nutid|datid|præteritum|perfektum|participium|genitiv|flertal|ental|komparativ|superlativ|intetkøn|fælleskøn|nominativ|akkusativ|infinitiv|præsens|passiv)\b.*|.*\bform\b.*) af ([a-zæøåé]+)\W*$',re.I)
for k in list(da):
    keep=[]
    for d in da[k]:
        m=FRE.match(d)
        if m: FORM.setdefault(k,m.group(1).lower())
        else: keep.append(d)
    if keep: da[k]=keep
    else: del da[k]

def has(w): return w in EN or w in da
NOUNONLY={'en','ene','ne','erne','n','nes','ens','ets','enes','ernes'}
def fits(l,w,ctx):
    # a noun/adjective base is dropped only when the ending can be a verb ending,
    # a verb reading exists, and Wiktionary's table of the noun does not list this form
    nounonly,verbalt=ctx
    return l==w or l in VERB or nounonly or not verbalt or len(FS.get(l,()))<6 or w in FS[l]
FREQ={}
for l in open('w/dl/da_50k.txt'):
    p=l.split()
    if len(p)==2: FREQ[p[0]]=int(p[1])
def vforms(v):
    st=v[:-1] if v.endswith('e') else v
    return {v,v+'r',st+'er',st+'ede',st+'te',st+'et',st+'t',st,st+'ende',v+'s'}
def pick(found,w):
    # when Wiktionary has a page for the form itself (øget: "past participle of øge"), it decides
    own=[l for l in found if l in FORMOF.get(w,())]
    return own[0] if own else found[0]
def lemma(w,segs=None,ty=None):
    ctx=(False,False); found=[]
    def add(c):
        if c and c not in found: found.append(c)
    if segs and ty and ty[-1]=='B' and len(segs)>1 and not (segs[-1]=='e' and ty[-2]!='B' and has(w)):
        s,t=list(segs),list(ty); cand=[]; verbal=False; ends=[]
        while len(s)>1 and t[-1]=='B':
            e=s.pop();t.pop();stem=''.join(s); ends.append(e)
            if e in ('ede','te','ende','edes','tes','es','ed'): verbal=True
            dbl=stem[:-1] if len(stem)>2 and stem[-1]==stem[-2] else None
            cand.insert(0,[stem+'e',stem,dbl] if verbal else [stem,stem+'e',dbl])
        allc=[c for cs in cand for c in cs if c]
        verbalt=any(c in VERB or FORM.get(c) in VERB for c in allc)
        ctx=(any(e in NOUNONLY for e in ends) or (len(ends)>1 and ends[0]=='s'),verbalt)
        for cs in cand:
            for c in cs:
                if c and has(c) and fits(c,w,ctx): add(c)
            for c in cs:
                if c and FORM.get(c) and has(FORM[c]) and fits(FORM[c],w,ctx): add(FORM[c])
    if found and not ctx[0]: return pick(found,w)
    if found: return found[0]
    if has(w): return w
    f=FORM.get(w)
    if f and has(f) and fits(f,w,ctx): return f
    return None
def parts(segs,ty):
    comps=[];cur='';curty=''
    for s,t in zip(segs,ty):
        if t=='L':
            comps.append((cur,curty));cur='';curty='';continue
        if t in 'FR' and 'R' in curty: comps.append((cur,curty));cur='';curty=''
        cur+=s;curty+=t
    comps.append((cur,curty))
    out=[]
    for c,ct in comps:
        if not c: continue
        cs=[];i=0;ss=[]
        # rebuild segs for heuristics
        l=lemma(c,*_split(c,segs,ty)) or lemma(c)
        out.append((c,l))
    return out
def _split(c,segs,ty):
    w=''.join(segs);i=w.find(c);acc=0;s=[];t=[]
    for sg,tt in zip(segs,ty):
        if acc>=i and acc+len(sg)<=i+len(c): s.append(sg);t.append(tt)
        acc+=len(sg)
    return s,t
def dedef(lst,n=1,mx=160):
    out=[]
    for d in lst:
        d=d.strip()
        if len(d)>mx: d=re.split(r'(?<=[.;])\s',d)[0]
        if len(d)>mx: d=d[:mx].rsplit(' ',1)[0]+' …'
        if d and d not in out: out.append(d)
        if len(out)==n: break
    return out
W={};L={};stats={'direct':0,'lemma':0,'parts':0,'none':0}
for w,(segs,ty) in items.items():
    l=lemma(w,segs,ty)
    if l:
        W[w]=l if l!=w else 1; L[l]=1; stats['direct' if l==w else 'lemma']+=1; continue
    if ty and ty.count('R')>=2:
        ps=parts(segs,ty)
        if len(ps)>=2 and all(p[1] for p in ps):
            W[w]=[p[1] for p in ps]; [L.__setitem__(p[1],1) for p in ps]; stats['parts']+=1; continue
    stats['none']+=1
lex={}
for l in L:
    lex[l]=[dedef(da.get(l,[])),dedef(EN.get(l,[]))]
print(len(items),stats,len(lex))
json.dump({'w':W,'l':lex},open('w/meaning.json','w'),ensure_ascii=False,separators=(',',':'))
import os;print(os.path.getsize('w/meaning.json'))
for w in ['vejen','udløbsdatoen','hentede','computer','bilerne','glad','læse','kørte','højeste']:
    print(w,W.get(w),[lex.get(x) for x in ([W[w]] if isinstance(W.get(w),str) else W.get(w) if isinstance(W.get(w),list) else [w])])
