import json, re, sys
from argostranslate import package, translate

SRC = "en.json"
DST = "cs.json"
REPORT = "translation-report.txt"

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
        i = len(vals)
        vals.append(m.group(0))
        return chr(0xE000 + i)
    return PLACEHOLDER_RE.sub(repl, text), vals

def restore(text, vals):
    for i, val in enumerate(vals):
        text = text.replace(chr(0xE000 + i), val)
    return text

print("Downloading Argos Translate package index...")
package.update_package_index()
available = package.get_available_packages()
matches = [p for p in available if p.from_code == "en" and p.to_code == "cs"]
if not matches:
    raise RuntimeError("No Argos Translate en->cs package available")

pkg = matches[0]
print(f"Installing translation model: {pkg}")
path = pkg.download()
package.install_from_path(path)

langs = translate.get_installed_languages()
from_lang = next(x for x in langs if x.code == "en")
to_lang = next(x for x in langs if x.code == "cs")
translator = from_lang.get_translation(to_lang)

def tr_one(s):
    if should_keep(s):
        return s
    safe, vals = protect(s)
    out = translator.translate(safe)
    out = restore(out, vals)
    if sorted(PLACEHOLDER_RE.findall(out)) != sorted(PLACEHOLDER_RE.findall(s)):
        print(f"PLACEHOLDER FALLBACK: {s!r}", file=sys.stderr)
        return s
    return out

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

with open(SRC, "r", encoding="utf-8") as f:
    data = json.load(f)

vals = []
collect(data, vals)
uniq = list(dict.fromkeys(vals))
mapping = {}

for i, s in enumerate(uniq, 1):
    mapping[s] = tr_one(s)
    if i % 100 == 0:
        print(f"Translated {i}/{len(uniq)}", flush=True)

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
