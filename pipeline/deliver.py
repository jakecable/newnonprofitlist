"""Email subscribers their CSV through Resend.

Who gets an email comes from two places, combined:
  1. Stripe (automatic): every active or trialing subscription, when STRIPE_API_KEY is set.
     The plan is read from the product (All States) or the state typed at checkout.
  2. The SUBSCRIBERS secret (manual extras): one line per person, "email,PLAN",
     PLAN = 2-letter state code or ALL. Use it for yourself, testers, or free accounts.

Environment variables (GitHub Actions secrets):
  RESEND_API_KEY, FROM_EMAIL, SUBSCRIBERS (optional), STRIPE_API_KEY (optional)

Modes:
  --mode all      everyone (the monthly send on the 16th)
  --mode new      only Stripe subscribers who have never received a list (checked hourly)
  --mode check    print whether any new Stripe subscriber is waiting (no email sent)
  --only EMAIL    restrict to one email address (manual sends)
  --dry-run / --preview DIR   don't send
"""
import argparse, base64, json, os, sys, urllib.error, urllib.request
from config import STATES, SITE_NAME, SITE_URL, CONTACT_EMAIL, CUSTOMER_PORTAL
import stripe_subs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "newnonprofitlist-delivery/1.0 (+https://newnonprofitlist.com)"


def fail(msg):
    """Exit with a message that also shows as an error annotation on the GitHub run page."""
    print(f"::error title=Email delivery::{msg}")
    sys.exit(msg)


def resend(key, payload):
    req = urllib.request.Request("https://api.resend.com/emails", data=json.dumps(payload).encode(),
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                                          "User-Agent": UA})
    urllib.request.urlopen(req, timeout=120).read()


def manual_subscribers():
    out = []
    for line in os.environ.get("SUBSCRIBERS", "").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "," not in line:
            continue
        email, plan = [x.strip() for x in line.split(",", 1)]
        out.append({"email": email, "plan": plan.upper(), "sub_id": None, "welcomed": True})
    return out


def output(name, value):
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"{name}={value}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--release", default="")
    ap.add_argument("--mode", choices=["all", "new", "check"], default="all")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", default="", help="send only to this email address")
    ap.add_argument("--preview", default="", help="write each email as a .eml file into this folder instead of sending")
    a = ap.parse_args()
    key, sender = os.environ.get("RESEND_API_KEY"), os.environ.get("FROM_EMAIL")

    # ---- who to send to
    stripe_list, problems = [], []
    if stripe_subs.enabled():
        try:
            stripe_list, problems = stripe_subs.get_subscribers()
        except urllib.error.HTTPError as ex:
            fail(f"Stripe refused the request: HTTP {ex.code} {ex.read().decode(errors='replace')[:300]}. "
                 "Check the STRIPE_API_KEY secret and its permissions.")
    new_problems = [p for p in problems if not p["flagged"]]
    for p in problems:
        print(f"::warning title=Subscriber needs attention::{p['msg']}")

    if a.mode == "check":
        waiting = [s for s in stripe_list if not s["welcomed"]]
        print(f"{len(waiting)} new subscriber(s) waiting; {len(new_problems)} new problem(s)")
        output("has_new", "true" if (waiting or new_problems) else "false")
        return

    recipients = [s for s in stripe_list if not s["welcomed"]] if a.mode == "new" else stripe_list + manual_subscribers()
    if a.only:
        recipients = [s for s in recipients if s["email"].lower() == a.only.strip().lower()]
        if not recipients:
            fail(f"{a.only} is not a current subscriber in Stripe or in the SUBSCRIBERS secret.")
    if not recipients and not new_problems:
        print("Nobody to send to."); return
    if not (key and sender) and not (a.dry_run or a.preview):
        fail("Missing secret(s): " + ", ".join(n for n, v in (("RESEND_API_KEY", key), ("FROM_EMAIL", sender)) if not v))

    # ---- tell Jake about subscriptions that need a manual fix (only when actually sending)
    if new_problems and key and sender and not (a.dry_run or a.preview):
        try:
            resend(key, {"from": sender, "to": [CONTACT_EMAIL], "subject": "Action needed: a subscriber's state couldn't be read",
                         "text": "These subscriptions couldn't be matched to a list automatically:\n\n- "
                                 + "\n- ".join(p["msg"] for p in new_problems)})
            for p in new_problems:
                stripe_subs.mark_flagged(p["sub_id"])
        except Exception as ex:
            print(f"::warning::Could not send the problem report: {ex}")

    summary = json.load(open(os.path.join(ROOT, "data", "processed", a.release, "summary.json")))
    ddir = os.path.join(ROOT, "data", "deliverables", a.release)
    failures = 0
    for s in recipients:
        email, plan = s["email"], s["plan"]
        fname = "ALL.csv" if plan == "ALL" else f"{plan}.csv"
        path = os.path.join(ddir, fname)
        if not os.path.exists(path):
            print(f"::warning title=Email delivery::Skipped {email}: no list for plan '{plan}' (use a 2-letter state code or ALL)"); continue
        area = "all states" if plan == "ALL" else STATES.get(plan, plan)
        count = summary["national"]["count"] if plan == "ALL" else summary["states"].get(plan, {}).get("count", 0)
        months = f"{summary['recent_labels'][0]} – {summary['recent_labels'][-1]}"
        intro = ("Welcome! Here is your first list. " if a.mode == "new" else "") + "Attached is this month's list"
        text = (f"Hi,\n\n{intro} of new 501(c)(3) nonprofits for {area}: "
                f"{count:,} organizations approved {months} (IRS release {a.release}).\n\n"
                "Quick guide to the columns:\n"
                "- Stage: 'New - no tax return filed yet' are brand-new groups; 'Likely reinstated' are older groups being re-approved.\n"
                "- Annual filing: groups filing a Form 990 or 990-EZ are larger; Form 990-N groups take in under $50,000 a year.\n"
                "- Category: the group's cause (education, youth sports, animal rescue and so on).\n"
                + ("- New this release: 'Yes' marks groups that appeared since last month's list.\n" if summary.get("has_diff") else "")
                + "\nThe newest month is still filling in; next month's list will include the groups the IRS adds late. "
                "A new list arrives around the 16th of each month.\n\n"
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
        try:
            resend(key, payload)
            print(f"sent {email}: {fname}")
            if s["sub_id"] and not s["welcomed"]:
                stripe_subs.mark_welcomed(s["sub_id"], a.release)
        except urllib.error.HTTPError as ex:
            failures += 1
            body = ex.read().decode(errors="replace")[:300]
            print(f"::error title=Email delivery::Refused for {email}: HTTP {ex.code} {body}")
        except Exception as ex:
            failures += 1
            print(f"::error title=Email delivery::Sending to {email} failed: {ex}")
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
