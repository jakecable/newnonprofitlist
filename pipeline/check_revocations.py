"""One-off: size up the IRS auto-revocation list (how many new revocations per month, by state and type)."""
import collections, io, re, sys, urllib.request, zipfile
from datetime import datetime
URLS = ["https://apps.irs.gov/pub/epostcard/data-download-revocation.zip",
        "https://www.irs.gov/pub/epostcard/data-download-revocation.zip"]
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
data = None
for u in URLS:
    try:
        data = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=600).read(); print("ok", u, len(data)); break
    except Exception as e:
        print(u, e)
if not data:
    print("::error::download failed"); sys.exit(1)
z = zipfile.ZipFile(io.BytesIO(data)); name = max(z.namelist(), key=lambda n: z.getinfo(n).file_size)
lines = io.TextIOWrapper(z.open(name), encoding="latin-1").read().splitlines()
print("rows", len(lines)); [print("SAMPLE", l[:300]) for l in lines[:3]]
def pdate(s):
    s = s.strip()
    for f in ("%d-%b-%Y", "%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y"):
        try: return datetime.strptime(s, f)
        except ValueError: pass
    return None
rows = [l.split("|") for l in lines if l.count("|") >= 8]
ncol = collections.Counter(len(r) for r in rows).most_common(1)[0][0]
datecols = [i for i in range(ncol) if sum(1 for r in rows[:2000] if len(r) > i and pdate(r[i])) > 200]
print("ncol", ncol, "date columns", datecols)
# guess: exemption type column = short numeric like '03'
typecol = max(range(ncol), key=lambda i: sum(1 for r in rows[:2000] if len(r) > i and re.fullmatch(r"\d{1,2}", r[i].strip() or "x")))
statecol = max(range(ncol), key=lambda i: sum(1 for r in rows[:2000] if len(r) > i and re.fullmatch(r"[A-Z]{2}", r[i].strip())))
rev, post = datecols[0], datecols[1] if len(datecols) > 1 else datecols[0]
reinst = datecols[2] if len(datecols) > 2 else None
by_post = collections.Counter(); by_post_c3 = collections.Counter(); st = collections.Counter(); reinstated = 0; recent = 0
for r in rows:
    if len(r) < ncol: continue
    d = pdate(r[post])
    if not d: continue
    ym = d.strftime("%Y-%m"); by_post[ym] += 1
    if r[typecol].strip().zfill(2) == "03":
        by_post_c3[ym] += 1
        if ym >= "2025-10":
            recent += 1; st[r[statecol].strip()] += 1
            if reinst is not None and pdate(r[reinst]): reinstated += 1
months = sorted(by_post)[-15:]
out = [f"type col {typecol}, state col {statecol}, posting col {post}, reinstatement col {reinst}"]
out += [f"{m}: all {by_post[m]:,} / 501c3 {by_post_c3[m]:,}" for m in months]
out.append(f"501c3 posted since 2025-10: {recent:,}; already reinstated: {reinstated:,}")
out.append("top states: " + ", ".join(f"{k} {v}" for k, v in st.most_common(12)))
for l in out: print(l)
print("::notice title=Revocations::" + " %0A".join(out))
