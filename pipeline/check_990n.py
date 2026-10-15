"""One-off measurement: how many organizations on the current list can be matched to IRS
Form 990-N (e-Postcard) filings, which add a principal officer's name and sometimes a website.

Usage: python pipeline/check_990n.py --release 2026-10
Needs data/deliverables/<release>/ALL.csv (run build.py first).
Prints the results as a GitHub annotation; writes no customer data anywhere.
"""
import argparse, collections, csv, io, os, sys, urllib.request, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URLS = ["https://apps.irs.gov/pub/epostcard/data-download-epostcard.zip",
        "https://www.irs.gov/pub/epostcard/data-download-epostcard.zip"]
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def download():
    for url in URLS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=600) as r:
                data = r.read()
            print(f"downloaded {url}: {len(data)/1e6:.1f} MB")
            return data
        except Exception as e:
            print(f"{url} failed: {e}", file=sys.stderr)
    print("::error title=990-N check::Could not download the e-Postcard file")
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--release", required=True)
    a = ap.parse_args()
    rows = list(csv.DictReader(open(os.path.join(ROOT, "data", "deliverables", a.release, "ALL.csv"), newline="")))
    want = {r["EIN"]: r for r in rows}

    z = zipfile.ZipFile(io.BytesIO(download()))
    name = max(z.namelist(), key=lambda n: z.getinfo(n).file_size)
    latest = {}  # EIN -> (tax_year, officer, website)
    total = 0
    with z.open(name) as f:
        for line in io.TextIOWrapper(f, encoding="latin-1"):
            p = line.rstrip("\r\n").split("|")
            if len(p) < 9:
                continue
            total += 1
            ein = p[0].strip().zfill(9)
            if ein in want:
                ty = p[1].strip()
                if ein not in latest or ty > latest[ein][0]:
                    latest[ein] = (ty, p[8].strip(), p[7].strip())
    print(f"e-Postcard rows: {total:,}; matched EINs: {len(latest):,} of {len(want):,}")

    by_stage = collections.Counter(r["Stage"] for r in rows)
    m_stage = collections.Counter(want[e]["Stage"] for e in latest)
    officer = sum(1 for v in latest.values() if v[1])
    site = sum(1 for v in latest.values() if v[2] and v[2].lower() not in ("n/a", "na", "none"))
    filing = collections.Counter(r["Annual filing"] for r in rows)
    lines = [f"Organizations on the {a.release} list: {len(rows):,}",
             f"Matched to a 990-N filing: {len(latest):,} ({len(latest)/len(rows):.1%})",
             f"  with a principal officer name: {officer:,} ({officer/len(rows):.1%} of list)",
             f"  with a website: {site:,} ({site/len(rows):.1%} of list)"]
    for st, n in by_stage.most_common():
        lines.append(f"Stage '{st}': {n:,} on list, {m_stage.get(st, 0):,} matched ({m_stage.get(st, 0)/n:.1%})")
    for fl, n in filing.most_common():
        lines.append(f"Annual filing '{fl}': {n:,}")
    for l in lines:
        print(l)
    print("::notice title=990-N coverage::" + " %0A".join(lines))


if __name__ == "__main__":
    main()
