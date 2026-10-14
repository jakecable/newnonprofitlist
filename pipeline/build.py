"""Turn raw IRS EO BMF files into (1) site data and (2) paid CSV deliverables.

Usage: python pipeline/build.py --release 2026-10 [--prev 2026-09]

Outputs
  data/processed/<release>/summary.json   numbers + previews used by the site generator
  data/processed/<release>/recent_eins.txt EINs approved in the last 24 months (for next diff)
  data/deliverables/<release>/<ST>.csv     full list of new 501(c)(3)s per state (paid)
  data/deliverables/<release>/ALL.csv      national file (paid)
  data/deliverables/<release>/SAMPLE.csv   20-row public sample
"""
import argparse, collections, csv, glob, json, os, re
from config import (STATES, NTEE, FOUNDATION, FILING, RECENT_MONTHS, TREND_MONTHS,
                    PREVIEW_ROWS, CITY_MIN, slug)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SMALL = {"of", "the", "and", "for", "in", "on", "at", "to", "a", "an", "by"}
KEEP_UPPER = {"USA", "US", "LLC", "PTA", "PTO", "YMCA", "NAACP", "VFW", "II", "III", "IV", "4H",
              "AME", "CME", "COGIC", "HOA", "STEM", "STEAM", "LGBTQ", "DC", "NFP"}


def nice(name: str) -> str:
    words = []
    for i, w in enumerate(name.split()):
        if w.strip(".,") in KEEP_UPPER or any(ch.isdigit() for ch in w):
            words.append(w)
        elif i and w.lower() in SMALL:
            words.append(w.lower())
        else:
            words.append("-".join(p.capitalize() for p in w.split("-")))
    return " ".join(words).strip()


try:
    from english_words import get_english_words_set
    WORDS = get_english_words_set(["web2", "gcide"], lower=True)
except Exception:  # word list not installed: fall back to frequency rules only
    WORDS = set()


def fix_breaks(name: str, freq) -> str:
    """The IRS stores names in 35-character pieces and inserts a space at each break
    ("FOUND ATION", "SIMSBOR O", "REHABILITAT ION"). Rejoin a break when:
      - the joined word is an English word or appears elsewhere in the data, or
      - either piece is a single stray letter, or
      - both pieces are rare, non-dictionary fragments."""
    for pos in (71, 35):
        if len(name) > pos + 1 and name[pos] == " " and name[pos - 1].isalpha() and name[pos + 1].isalpha():
            left = name[:pos].split(" ")[-1]
            right = name[pos + 1:].split(" ")[0]
            joined = left + right
            if (joined.lower() in WORDS or freq.get(joined, 0) > 0
                    or (len(right) == 1 and right not in ("A", "I"))
                    or (len(left) == 1 and left not in ("A", "I") and right.lower() not in WORDS)
                    or (left.lower() not in WORDS and right.lower() not in WORDS
                        and freq.get(left, 0) <= 1 and freq.get(right, 0) <= 1 and len(right) <= 4)):
                name = name[:pos] + name[pos + 1:]
    return name


def ym_add(ym: str, n: int) -> str:
    y, m = int(ym[:4]), int(ym[4:])
    t = y * 12 + (m - 1) + n
    return f"{t // 12:04d}{t % 12 + 1:02d}"


def label(ym: str) -> str:
    import calendar
    return f"{calendar.month_name[int(ym[4:])]} {ym[:4]}"


def load(release):
    rows = []
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "raw", release, "eo_*.csv"))):
        with open(path, newline="", encoding="latin-1") as f:
            for r in csv.DictReader(f):
                if r.get("SUBSECTION", "").strip().zfill(2) != "03":
                    continue
                ruling = (r.get("RULING") or "").strip()
                if not re.fullmatch(r"\d{6}", ruling) or ruling.endswith("00"):
                    continue
                st = (r.get("STATE") or "").strip().upper()
                if st not in STATES:
                    continue
                rows.append(r)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--release", required=True)
    ap.add_argument("--prev", default="")
    a = ap.parse_args()

    rows = load(a.release)
    if not rows:
        raise SystemExit(f"No rows found in data/raw/{a.release}/")
    freq = collections.Counter(w for r in rows for w in r["NAME"].split())
    for r in rows:
        r["NAME"] = fix_breaks(r["NAME"].strip(), freq)
    # Latest month with a meaningful count; the newest month in a release is often partial,
    # so we report it but treat it as "so far".
    by_month = collections.Counter(r["RULING"] for r in rows)
    latest = max(m for m, n in by_month.items() if n >= 50)
    recent = [ym_add(latest, -i) for i in range(RECENT_MONTHS)][::-1]
    trend = [ym_add(latest, -i) for i in range(TREND_MONTHS)][::-1]
    keep_from = ym_add(latest, -23)

    prev_eins = set()
    if a.prev:
        p = os.path.join(ROOT, "data", "processed", a.prev, "recent_eins.txt")
        if os.path.exists(p):
            prev_eins = set(open(p).read().split())

    def rec(r):
        ntee = (r.get("NTEE_CD") or "").strip().upper()
        cat = NTEE.get(ntee[:1], "Unclassified")
        ein = r["EIN"].strip().zfill(9)
        tp = (r.get("TAX_PERIOD") or "").strip()
        if not tp:
            stage = "New - no tax return filed yet"
        elif tp >= ym_add(r["RULING"], -24):
            stage = "New - has filed a first return"
        else:
            stage = "Likely reinstated (older organization)"
        return {
            "stage": stage,
            "ein": ein,
            "name": nice(r["NAME"].strip()),
            "name_raw": r["NAME"].strip(),
            "street": r.get("STREET", "").strip(),
            "city": r.get("CITY", "").strip().title(),
            "state": r["STATE"].strip().upper(),
            "zip": (r.get("ZIP") or "").strip()[:5],
            "ruling": r["RULING"],
            "ntee": ntee,
            "category": cat,
            "cat_code": ntee[:1] if ntee[:1] in NTEE else "Z",
            "foundation": FOUNDATION.get((r.get("FOUNDATION") or "").strip().zfill(2), "Other"),
            "filing": FILING.get((r.get("FILING_REQ_CD") or "").strip().zfill(2), "Other"),
            "deductible": "Yes" if (r.get("DEDUCTIBILITY") or "").strip() == "1" else "No",
            "new_in_release": "Yes" if prev_eins and ein not in prev_eins else ("" if not prev_eins else "No"),
        }

    recent_set = set(recent)
    new = [rec(r) for r in rows if r["RULING"] in recent_set]
    new.sort(key=lambda x: (-int(x["ruling"]), x["name"]))

    out_p = os.path.join(ROOT, "data", "processed", a.release)
    out_d = os.path.join(ROOT, "data", "deliverables", a.release)
    os.makedirs(out_p, exist_ok=True); os.makedirs(out_d, exist_ok=True)
    with open(os.path.join(out_p, "recent_eins.txt"), "w") as f:
        f.write("\n".join(sorted(r["EIN"].strip().zfill(9) for r in rows if r["RULING"] >= keep_from)))

    # ---------- paid deliverables ----------
    cols = ["EIN", "Organization", "Street", "City", "State", "ZIP", "Approval month", "Stage", "NTEE code",
            "Category", "Type", "Annual filing", "Donations deductible", "New this release", "Profile"]
    def write(path, items):
        with open(path, "w", newline="") as f:
            w = csv.writer(f); w.writerow(cols)
            for x in items:
                w.writerow([x["ein"], x["name_raw"], x["street"], x["city"], x["state"], x["zip"],
                            f'{x["ruling"][:4]}-{x["ruling"][4:]}', x["stage"], x["ntee"], x["category"],
                            x["foundation"], x["filing"], x["deductible"], x["new_in_release"],
                            f'https://projects.propublica.org/nonprofits/organizations/{int(x["ein"])}'])
    by_state = collections.defaultdict(list)
    for x in new: by_state[x["state"]].append(x)
    for st, items in by_state.items(): write(os.path.join(out_d, f"{st}.csv"), items)
    write(os.path.join(out_d, "ALL.csv"), new)
    write(os.path.join(out_d, "SAMPLE.csv"), new[:: max(1, len(new) // 20)][:20])

    # ---------- site data ----------
    def preview(items):
        return [{k: x[k] for k in ("name", "city", "state", "ruling", "category")} for x in items[:PREVIEW_ROWS]]

    def breakdown(items, key, n=None):
        c = collections.Counter(x[key] for x in items)
        return c.most_common(n)

    trend_counts = lambda items_all: [sum(1 for r in items_all if r["RULING"] == m) for m in trend]
    rows_by_state = collections.defaultdict(list)
    for r in rows:
        if r["RULING"] in trend: rows_by_state[r["STATE"].strip().upper()].append(r)

    states = {}
    for st, name in STATES.items():
        items = by_state.get(st, [])
        cities = collections.defaultdict(list)
        for x in items: cities[x["city"]].append(x)
        city_pages = {c: {"slug": slug(c), "count": len(v), "preview": preview(v),
                          "categories": breakdown(v, "category", 6)}
                      for c, v in cities.items() if c and len(v) >= CITY_MIN}
        states[st] = {
            "name": name, "slug": slug(name), "count": len(items),
            "by_month": {m: sum(1 for x in items if x["ruling"] == m) for m in recent},
            "trend": trend_counts(rows_by_state.get(st, [])),
            "categories": breakdown(items, "category"),
            "top_cities": [(c, len(v)) for c, v in sorted(cities.items(), key=lambda kv: -len(kv[1]))[:10] if c],
            "filing": breakdown(items, "filing"),
            "preview": preview(items),
            "cities": city_pages,
            "new_in_release": sum(1 for x in items if x["new_in_release"] == "Yes"),
        }

    cats = {}
    for code, cname in NTEE.items():
        items = [x for x in new if x["cat_code"] == code]
        cats[code] = {"name": cname, "slug": slug(cname), "count": len(items),
                      "top_states": breakdown(items, "state", 10), "preview": preview(items)}

    summary = {
        "release": a.release, "latest_month": latest, "latest_label": label(latest),
        "recent": recent, "recent_labels": [label(m) for m in recent],
        "trend": trend, "trend_labels": [label(m) for m in trend],
        "national": {"count": len(new), "trend": [by_month.get(m, 0) for m in trend],
                     "by_month": {m: by_month.get(m, 0) for m in recent},
                     "categories": breakdown(new, "category"),
                     "filing": breakdown(new, "filing"),
                     "new_in_release": sum(1 for x in new if x["new_in_release"] == "Yes")},
        "states": states, "categories": cats,
        "has_diff": bool(prev_eins),
    }
    with open(os.path.join(out_p, "summary.json"), "w") as f:
        json.dump(summary, f)
    print(f"release {a.release}: latest approval month {label(latest)}; "
          f"{len(new):,} new 501(c)(3)s in {RECENT_MONTHS} months; "
          f"{sum(1 for s in states.values() for _ in s['cities'])} city pages")


if __name__ == "__main__":
    main()
