import json, re, sys
from transformers import MarianMTModel, MarianTokenizer

SRC = "en.json"
DST = "cs.json"
REPORT = "translation-report.txt"
MODEL = "Helsinki-NLP/opus-mt-en-cs"

PLACEHOLDER_RE = re.compile(r'\$\{[^{}]+\}|\{[^{}]+\}|%[sdif]|\\n')
TECH_KEEP = {
    "OK","ID","MDT","DOJ","EMS","SIM","IMEI","Wi-Fi","AM","PM","URL","GIF","LIVE","MAX",
    "SD Phone","Weazel News","Cherry","Photogram","Squawk","Clout","Ryde","Penta","VHS",
    "Blackjack","Baccarat","Texas Hold'em"
}

def should_keep(s):
    if s in TECH_KEEP:
        return True
    if not re.search(r"[A-Za-z]", s):
        return True
    stripped = PLACEHOLDER_RE.sub("", s).strip()
    if not stripped:
        return True
    if re.fullmatch(r"[A-Z0-9._/+×:% -]{1,7}", stripped):
        return True
    return False

def protect(text):
    vals = []
    def repl(m):
        token = f"PHX{len(vals)}XHP"
        vals.append((token, m.group(0)))
        return token
    return PLACEHOLDER_RE.sub(repl, text), vals

def restore(text, vals):
    for token, val in vals:
        text = text.replace(token, val)
        text = text.replace(token.lower(), val)
    return text

def collect(x, out):
    if isinstance(x, dict):
        for v in x.values():
            collect(v, out)
    elif isinstance(x, list):
        for v in x:
            collect(v, out)
    elif isinstance(x, str):
        out.append(x)

def replace(x, mapping):
    if isinstance(x, dict):
        return {k: replace(v, mapping) for k, v in x.items()}
    if isinstance(x, list):
        return [replace(v, mapping) for v in x]
    if isinstance(x, str):
        return mapping[x]
    return x

def flat(x, path=()):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from flat(v, path + (k,))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from flat(v, path + (i,))
    else:
        yield path, x

print("Loading Czech translation model...", flush=True)
tokenizer = MarianTokenizer.from_pretrained(MODEL)
model = MarianMTModel.from_pretrained(MODEL)

with open(SRC, "r", encoding="utf-8") as f:
    data = json.load(f)

vals = []
collect(data, vals)
uniq = list(dict.fromkeys(vals))
mapping = {}
todo = []

for s in uniq:
    if should_keep(s):
        mapping[s] = s
    else:
        safe, ph = protect(s)
        todo.append((s, safe, ph))

BATCH = 32
for start in range(0, len(todo), BATCH):
    chunk = todo[start:start+BATCH]
    texts = [x[1] for x in chunk]
    enc = tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=512)
    gen = model.generate(**enc, max_length=512, num_beams=4)
    outs = tokenizer.batch_decode(gen, skip_special_tokens=True)

    for (original, _safe, ph), out in zip(chunk, outs):
        out = restore(out, ph)
        if sorted(PLACEHOLDER_RE.findall(original)) != sorted(PLACEHOLDER_RE.findall(out)):
            mapping[original] = original
        else:
            mapping[original] = out

    print(f"Translated {min(start+BATCH, len(todo))}/{len(todo)}", flush=True)

result = replace(data, mapping)

srcf = dict(flat(data))
dstf = dict(flat(result))
assert srcf.keys() == dstf.keys(), "JSON structure changed"

bad = []
unchanged = []
for p, s in srcf.items():
    if not isinstance(s, str):
        continue
    t = dstf[p]
    if sorted(PLACEHOLDER_RE.findall(s)) != sorted(PLACEHOLDER_RE.findall(t)):
        bad.append((p, s, t))
    if s == t and not should_keep(s):
        unchanged.append((p, s))

if bad:
    raise RuntimeError(f"Placeholder validation failed for {len(bad)} strings")

with open(DST, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
    f.write("\n")

with open(REPORT, "w", encoding="utf-8") as f:
    f.write(f"Total unique strings: {len(uniq)}\n")
    f.write(f"Unchanged non-technical strings: {len(unchanged)}\n\n")
    for p, s in unchanged:
        f.write(".".join(map(str, p)) + " = " + s.replace("\n", "\\n") + "\n")

print(f"Done. Unchanged non-technical strings: {len(unchanged)}")
