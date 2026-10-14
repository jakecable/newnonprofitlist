"""Download the IRS EO BMF state files into data/raw/<release>/.

Usage: python pipeline/fetch.py [--states TX,LA] [--release 2026-09]
The release label defaults to the current year-month. Files that already exist are skipped.
"""
import argparse, datetime, os, sys, time, urllib.request
from config import STATES, IRS_BASE

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--states", default="", help="comma list of state codes (default: all)")
    ap.add_argument("--release", default=datetime.date.today().strftime("%Y-%m"))
    a = ap.parse_args()
    codes = [c.strip().upper() for c in a.states.split(",") if c.strip()] or list(STATES)
    out = os.path.join(ROOT, "data", "raw", a.release)
    os.makedirs(out, exist_ok=True)
    failed = []
    for code in codes:
        dest = os.path.join(out, f"eo_{code.lower()}.csv")
        if os.path.exists(dest) and os.path.getsize(dest) > 1000:
            continue
        url = IRS_BASE.format(code=code.lower())
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/126.0 Safari/537.36 (+newnonprofitlist data pipeline)",
                    "Accept": "text/csv,*/*"})
                with urllib.request.urlopen(req, timeout=120) as r, open(dest + ".part", "wb") as f:
                    f.write(r.read())
                os.replace(dest + ".part", dest)
                print(f"{code}: {os.path.getsize(dest)/1e6:.1f} MB")
                break
            except Exception as e:  # network hiccup: wait and retry
                print(f"{code}: attempt {attempt+1} failed: {e}", file=sys.stderr)
                time.sleep(5 * (attempt + 1))
        else:
            failed.append(code)
    if failed:
        print("FAILED:", ",".join(failed), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
