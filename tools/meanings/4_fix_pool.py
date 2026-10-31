import json,re,sys
src=open('/Users/saschaawhaber/ord-et/index.html').read()
A=json.loads(re.search(r'const AUTO = (\{.*?\});\n',src,re.S).group(1))
formof={}; ety={}; pos={}
for l in open('w/dl/kaikki.org-dictionary-Danish.jsonl'):
    e=json.loads(l); w=e['word']
    for s in e.get('senses',[]):
        for fo in s.get('form_of',[]) or []:
            formof.setdefault(w,[]).append((fo['word'],e.get('pos'),' '.join(s.get('glosses',[''])[:1])))
    if any(not s.get('form_of') for s in e.get('senses',[])):
        ety.setdefault(w,[]).extend(t['name'] for t in e.get('etymology_templates',[]))
        pos.setdefault(w,set()).add(e.get('pos'))
def ending(last):
    if 'noun' in pos.get(last,set()): return None
    for lem,p,g in formof.get(last,[]):
        if p!='verb' and 'verb' not in pos.get(lem,set()): continue
        stem=lem[:-1] if p=='verb' and lem.endswith('e') else lem
        if last.startswith(stem) and len(last)>len(stem) and len(stem)>=2:
            e=last[len(stem):]
            if e in ('et','t','ede','te','ende'): return stem,e
    return None
infl=[];loan=[]
for k in A:
    for l in A[k].split('\n'):
        p=l.split(' ')
        if len(p)<2: continue
        segs=p[0].split('-'); ty=p[1]
        if len(segs)>=2 and ty[-1] in 'R':
            r=ending(segs[-1])
            if r: infl.append((k,p[0],ty,'-'.join(segs[:-1]+list(r)),ty+'B'))
        w=''.join(segs)
        if ty.count('R')>=2:
            et=ety.get(w,[])
            if et and not any(n in('compound','af','com','suffix','prefix','affix','blend','surf') for n in et) and any(n in('bor','der','lbor','bor+','inh','ubor','slbor','calque','clipping') for n in et):
                loan.append((k,p[0],ty,et[:4]))
print('inflection fixes',len(infl));[print(x) for x in infl[:40]]
print('loan',len(loan));[print(x) for x in loan[:80]]
json.dump({'infl':infl,'loan':loan},open('w/fix.json','w'),ensure_ascii=False)
