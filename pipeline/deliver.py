"""Email each subscriber their monthly CSV through Resend (https://resend.com, free up to 3,000 emails/month).

Environment variables (set as GitHub Actions secrets):
  RESEND_API_KEY   API key from resend.com
  FROM_EMAIL       e.g. "New Nonprofit List <lists@newnonprofitlist.com>" (domain verified in Resend)
  SUBSCRIBERS      one subscriber per line: email,PLAN   where PLAN is a state code (TX) or ALL
                   e.g.  jane@cpa-firm.com,TX
                         ops@donorapp.com,ALL

Usage: python pipeline/deliver.py --release 2026-10 [--only someone@firm.com] [--dry-run]
  --only sends to just that subscriber (use it the day a new customer pays).
"""
import argparse, base64, json, os, sys, urllib.request
from config import STATES, SITE_NAME, SITE_URL, CONTACT_EMAIL, CUSTOMER_PORTAL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--release", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", default="", help="send only to this email address")
    ap.add_argument("--preview", default="", help="write each email as a .eml file into this folder instead of sending")
    a = ap.parse_args()
    key, sender = os.environ.get("RESEND_API_KEY"), os.environ.get("FROM_EMAIL")
    subs = [l.strip() for l in os.environ.get("SUBSCRIBERS", "").splitlines() if l.strip() and not l.startswith("#")]
    if a.only:
        subs = [l for l in subs if l.split(",")[0].strip().lower() == a.only.strip().lower()]
        if not subs:
            sys.exit(f"{a.only} is not in SUBSCRIBERS. Add the line 'email,STATE' to the secret first.")
    if not subs:
        print("No subscribers configured; nothing to send."); return
    if not (key and sender) and not (a.dry_run or a.preview):
        sys.exit("RESEND_API_KEY and FROM_EMAIL are required to send.")
    summary = json.load(open(os.path.join(ROOT, "data", "processed", a.release, "summary.json")))
    ddir = os.path.join(ROOT, "data", "deliverables", a.release)
    failures = 0
    for line in subs:
        email, plan = [x.strip() for x in line.split(",", 1)]
        plan = plan.upper()
        fname = "ALL.csv" if plan == "ALL" else f"{plan}.csv"
        path = os.path.join(ddir, fname)
        if not os.path.exists(path):
            print(f"skip {email}: no file {fname}"); continue
        area = "all states" if plan == "ALL" else STATES.get(plan, plan)
        count = summary["national"]["count"] if plan == "ALL" else summary["states"].get(plan, {}).get("count", 0)
        months = f"{summary['recent_labels'][0]} – {summary['recent_labels'][-1]}"
        text = (f"Hi,\n\nAttached is this month's list of new 501(c)(3) nonprofits for {area}: "
                f"{count:,} organizations approved {months} (IRS release {a.release}).\n\n"
                "Quick guide to the columns:\n"
                "- Stage: 'New - no tax return filed yet' are brand-new groups; 'Likely reinstated' are older groups being re-approved.\n"
                "- Annual filing: groups filing a Form 990 or 990-EZ are larger; Form 990-N groups take in under $50,000 a year.\n"
                "- Category: the group's cause (education, youth sports, animal rescue and so on).\n"
                + ("- New this release: 'Yes' marks groups that appeared since last month's list.\n" if summary.get("has_diff") else "")
                + "\nThe newest month is still filling in; next month's list will include the groups the IRS adds late.\n\n"
                f"Browse the numbers: {SITE_URL}\n"
                + (f"Manage or cancel your subscription: {CUSTOMER_PORTAL}\n" if CUSTOMER_PORTAL else "")
                + f"Questions: reply to this email or write to {CONTACT_EMAIL}.\n\n- {SITE_NAME}")
        payload = {"from": sender, "to": [email], "reply_to": CONTACT_EMAIL,
                   "subject": f"New nonprofits in {area} – IRS release {a.release}",
                   "text": text,
                   "attachments": [{"filename": f"new-nonprofits-{plan.lower()}-{a.release}.csv",
                                    "content": base64.b64encode(open(path, "rb").read()).decode()}]}
        if a.dry_run:
            print(f"[dry run] {email}: {fname} ({count:,} rows)"); continue
        if a.preview:
            from email.message import EmailMessage
            m = EmailMessage()
            m["From"] = sender or f"{SITE_NAME} <lists@{SITE_URL.split('//')[-1]}>"
            m["To"] = email; m["Reply-To"] = CONTACT_EMAIL; m["Subject"] = payload["subject"]
            m.set_content(text)
            m.add_attachment(open(path, "rb").read(), maintype="text", subtype="csv",
                             filename=payload["attachments"][0]["filename"])
            os.makedirs(a.preview, exist_ok=True)
            out = os.path.join(a.preview, f"email-to-{email.split('@')[0]}-{plan.lower()}.eml")
            open(out, "wb").write(bytes(m))
            print(f"[preview] wrote {out}"); continue
        req = urllib.request.Request("https://api.resend.com/emails", data=json.dumps(payload).encode(),
                                     headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=60).read()
            print(f"sent {email}: {fname}")
        except Exception as ex:
            failures += 1
            print(f"FAILED {email}: {ex}", file=sys.stderr)
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
