exec(open('3_check.py').read().replace("if __name__ == '__main__':","if False:"))
import json as _j
P='/Users/saschaawhaber/ord-et/index.html'
src=open(P,encoding='utf-8').read()
m=re.search(r'const AUTO = (\{.*?\});\n',src,re.S); A=_j.loads(m.group(1))
old=set()
for k in A:
    for l in A[k].split('\n'):
        p=l.split(' ')
        if len(p)>=2: old.add(p[0].replace('-',''))
cands=[w for w,_ in sorted(FREQ.items(),key=lambda x:-x[1]) if re.fullmatch(r'[a-zæøå]{3,}',w)]
cands+= [w for w in old if w not in FREQ]
pools={'boej':[],'sammen':[],'afled':[]}; info={}; seen=set()
for w in cands:
    if w in seen: continue
    seen.add(w)
    r,e=analyze_word(w)
    if not r or len(r['segs'])<2: continue
    ty=''.join(r['types'])
    k='afled' if ('F' in ty or 'A' in ty) else ('sammen' if ty.count('R')>=2 or 'L' in ty else 'boej')
    pools[k].append('-'.join(r['segs'])+' '+ty)
    info[w]={'lemma':r['lemma'],'pos':r['pos'],'parts':r['parts']}
for k in pools: print(k,len(pools[k]))
NEW={k:'\n'.join(v) for k,v in pools.items()}
src=src[:m.start(1)]+_j.dumps(NEW,ensure_ascii=False,separators=(', ',': '))+src[m.end(1):]
# curated lists: keep a line only if the checker gives the same cuts
B0=src.index('const BUILTIN = ['); B1=src.index('const AUTO =')
B=src[B0:B1]; removed=[]
def keep(line):
    l=line.split(';')[0].strip()
    if not l or l.startswith('#'): return True
    alts=[]
    for part in l.split('/'):
        p=part.split()
        segs=[x for x in re.split(r'[-|+·]+',p[0].lower()) if x]; alts.append(segs)
    w=''.join(alts[0]); r,e=analyze_word(w)
    if r and any(r['segs']==a for a in alts):
        info.setdefault(w,{'lemma':r['lemma'],'pos':r['pos'],'parts':r['parts']}); return True
    removed.append((l, ('-'.join(r['segs'])+' '+''.join(r['types'])) if r else e)); return False
def fix(mt):
    body=mt.group(1)
    return 'text: `'+'\n'.join(x for x in body.split('\n') if keep(x))+'`'
B=re.sub(r'text: `(.*?)`',fix,B,flags=re.S)
src=src[:B0]+B+src[B1:]
open(P,'w',encoding='utf-8').write(src)
_j.dump(info,open('w/pool_info.json','w'),ensure_ascii=False)
print('curated removed',len(removed))
for l,why in removed: print('  ',l,'|',why)
