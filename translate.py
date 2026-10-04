import json, re, time, random, sys, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlencode
import requests

SRC = "en.json"
DST = "cs.json"
REPORT = "translation-report.txt"

PLACEHOLDER_RE = re.compile(r'\\$\\{[^{}]+\\}|\\{[^{}]+\\}|%[sdif]|\\\\n')
TECH_KEEP = {
    "OK","ID","MDT","DOJ","EMS","SIM","IMEI","Wi-Fi","AM","PM","URL","GIF","LIVE","MAX",
    "SD Phone","Weazel News","Cherry","Photogram","Squawk","Clout","Ryde","Penta","VHS",
    "Blackjack","Baccarat","Texas Hold'em"
}

_tls = threading.local()

def sess():
    if not hasattr(_tls, "s"):
        _tls.s = requests.Session()
        _tls.s.headers.update({"User-Agent":"Mozilla/5.0"})
    return _tls.s

def protect(text):
    vals=[]
    def repl(m):
        vals.append(m.group(0))
        return f"ZXQPH{len(vals)-1}QXZ"
    return PLACEHOLDER_RE.sub(repl,text), vals

def restore(text, vals):
    for i,val in enumerate(vals):
        pats=[
            rf"ZXQPH{i}QXZ",
            rf"ZXQ\\s*PH\\s*{i}\\s*QXZ",
            rf"ZXQPH\\s*{i}\\s*QXZ",
        ]
        for p in pats:
            text=re.sub(p, lambda _m,v=val:v, text, flags=re.I)
    return text

def should_keep(s):
    if s in TECH_KEEP: return True
    if not re.search(r"[A-Za-z]", s): return True
    stripped=PLACEHOLDER_RE.sub("",s).strip()
    if not stripped: return True
    if re.fullmatch(r"[A-Z0-9._/+×:% -]{1,7}", stripped): return True
    return False

def tr_one(s):
    if should_keep(s): return s
    safe, vals = protect(s)
    params={"client":"gtx","sl":"en","tl":"cs","dt":"t","q":safe}
    last=None
    for attempt in range(9):
        try:
            r=sess().get("https://translate.googleapis.com/translate_a/single",params=params,timeout=30)
            if r.status_code==429:
                raise RuntimeError("rate limited")
            r.raise_for_status()
            data=r.json()
            out="".join(p[0] for p in data[0] if p and p[0] is not None)
            out=restore(out,vals)
            if sorted(PLACEHOLDER_RE.findall(out)) != sorted(PLACEHOLDER_RE.findall(s)):
                raise RuntimeError("placeholder mismatch")
            return out
        except Exception as e:
            last=e
            time.sleep(min(30, 1.7**attempt)+random.random())
    print(f"FAILED: {s!r}: {last}",file=sys.stderr)
    return s

def collect(x,out):
    if isinstance(x,dict):
        for v in x.values(): collect(v,out)
    elif isinstance(x,list):
        for v in x: collect(v,out)
    elif isinstance(x,str):
        out.append(x)

def replace(x,m):
    if isinstance(x,dict): return {k:replace(v,m) for k,v in x.items()}
    if isinstance(x,list): return [replace(v,m) for v in x]
    if isinstance(x,str): return m[x]
    return x

def flat(x,path=()):
    if isinstance(x,dict):
        for k,v in x.items(): yield from flat(v,path+(k,))
    elif isinstance(x,list):
        for i,v in enumerate(x): yield from flat(v,path+(i,))
    else:
        yield path,x

with open(SRC,"r",encoding="utf-8") as f:
    data=json.load(f)

vals=[]
collect(data,vals)
uniq=list(dict.fromkeys(vals))
mapping={s:s for s in uniq if should_keep(s)}
todo=[s for s in uniq if not should_keep(s)]
print(f"Unique translatable strings: {len(todo)}")

# Low parallelism is deliberate; it is more reliable with the public translate endpoint.
with ThreadPoolExecutor(max_workers=4) as ex:
    futures={ex.submit(tr_one,s):s for s in todo}
    done=0
    for fut in as_completed(futures):
        s=futures[fut]
        try: mapping[s]=fut.result()
        except Exception: mapping[s]=s
        done+=1
        if done%100==0: print(f"{done}/{len(todo)}")

result=replace(data,mapping)

srcf=dict(flat(data))
dstf=dict(flat(result))
assert srcf.keys()==dstf.keys(),"JSON structure changed"

bad=[]
unchanged=[]
for p,s in srcf.items():
    if not isinstance(s,str): continue
    t=dstf[p]
    if sorted(PLACEHOLDER_RE.findall(s)) != sorted(PLACEHOLDER_RE.findall(t)):
        bad.append((p,s,t))
    if s==t and not should_keep(s):
        unchanged.append((p,s))

if bad:
    raise RuntimeError(f"Placeholder validation failed for {len(bad)} strings")

with open(DST,"w",encoding="utf-8") as f:
    json.dump(result,f,ensure_ascii=False,indent=2)
    f.write("\n")

with open(REPORT,"w",encoding="utf-8") as f:
    f.write(f"Total unique strings: {len(uniq)}\n")
    f.write(f"Translated candidates: {len(todo)}\n")
    f.write(f"Unchanged non-technical after retries: {len(unchanged)}\n\n")
    for p,s in unchanged:
        f.write(".".join(map(str,p))+" = "+s.replace("\n","\\n")+"\n")

print(f"Done. Unchanged non-technical strings: {len(unchanged)}")
