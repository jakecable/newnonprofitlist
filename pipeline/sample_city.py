"""One-off: print the newest rows for one city from a built state file, as an annotation."""
import csv, json, os, sys
rel, st, city, n = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = [r for r in csv.DictReader(open(os.path.join(ROOT, "data", "deliverables", rel, f"{st}.csv"))) if r["City"].lower() == city.lower()]
rows.sort(key=lambda r: r["Approval month"], reverse=True)
keep = [{k: r[k] for k in ("Organization", "Street", "City", "ZIP", "Approval month", "Category", "Stage")} for r in rows[:n]]
print(f"{len(rows)} rows for {city}")
print("::notice title=Sample::" + json.dumps({"total": len(rows), "rows": keep}).replace("%", "%25"))
