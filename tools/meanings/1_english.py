import json,sys,re
BAD=re.compile(r'(Only used|see |Alternative|Obsolete|Archaic|Misspelling|Clipping|Abbreviation|initialism)',re.I)
W=set(open('w/words.txt').read().split())
lem={}; form={}
for l in open('w/dl/kaikki.org-dictionary-Danish.jsonl'):
    e=json.loads(l); w=e['word']
    for f in e.get('forms',[]):
        if f.get('form') in W: form.setdefault(f['form'],w)
    for s in e.get('senses',[]):
        fo=s.get('form_of') or s.get('alt_of')
        if fo:
            if w in W: form.setdefault(w,fo[0]['word'])
        elif s.get('glosses') and 'form-of' not in s.get('tags',[]) and not BAD.match(s['glosses'][-1]):
            lem.setdefault(w,[]).append(s['glosses'][-1])
d=sum(1 for w in W if w in lem); f=sum(1 for w in W if w not in lem and form.get(w) in lem)
print('en: direct',d,'via form',f,'of',len(W))
json.dump({'lem':lem,'form':form},open('w/en.json','w'))
