import json,sys,re
BAD=re.compile(r'(Only used|see |Alternative|Obsolete|Archaic|Misspelling|Clipping|Abbreviation|initialism)',re.I)
W=set(open('w/words.txt').read().split())
lem={}; form={}; fs={}; verb=set()
for l in open('w/dl/kaikki.org-dictionary-Danish.jsonl'):
    e=json.loads(l); w=e['word']
    for f in e.get('forms',[]):
        if e.get('pos') in ('noun','adj') and f.get('form') and ' ' not in f['form'] and not set(f.get('tags',[]))&{'table-tags','inflection-template'} and f['form'] not in ('no-table-tags','da-decl','da-conj'): fs.setdefault(w,set()).add(f['form'])
        if f.get('form') in W: form.setdefault(f['form'],w)
    if e.get('pos')=='verb' and any(not s.get('form_of') for s in e.get('senses',[])): verb.add(w)
    for s in e.get('senses',[]):
        fo=s.get('form_of') or s.get('alt_of')
        if fo:
            if w in W: form.setdefault(w,fo[0]['word'])
            if e.get('pos') in ('noun','adj'): fs.setdefault(fo[0]['word'],set()).add(w)
        elif s.get('glosses') and 'form-of' not in s.get('tags',[]) and not BAD.match(s['glosses'][-1]):
            lem.setdefault(w,[]).append(s['glosses'][-1])
d=sum(1 for w in W if w in lem); f=sum(1 for w in W if w not in lem and form.get(w) in lem)
print('en: direct',d,'via form',f,'of',len(W))
json.dump({'lem':lem,'form':form,'fs':{k:sorted(v) for k,v in fs.items()},'verb':sorted(verb)},open('w/en.json','w'))
