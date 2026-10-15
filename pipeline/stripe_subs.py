"""Read paying subscribers straight from Stripe, so nobody has to maintain a list by hand.

Needs a Stripe *restricted* key in the STRIPE_API_KEY environment variable with:
  Subscriptions: Write   (to mark who has received their first list)
  Customers: Read        (email address)
  Checkout Sessions: Read (the "Which state?" answer typed at checkout)
  Products: Read         (tell One State from All States)

A subscriber is anyone whose subscription status is "active" or "trialing".
Their plan is ALL when the product name contains "all states"; otherwise it is the state
they typed into the checkout's state field (2-letter code or full state name).
"""
import json, os, re, urllib.error, urllib.parse, urllib.request
from config import STATES

API = "https://api.stripe.com/v1"
UA = "newnonprofitlist-delivery/1.0 (+https://newnonprofitlist.com)"
WELCOME_KEY = "first_list_sent"
FLAG_KEY = "needs_attention"
NAME_TO_CODE = {v.lower(): k for k, v in STATES.items()}


def _req(method, path, params=None):
    key = os.environ["STRIPE_API_KEY"]
    data = None
    url = f"{API}{path}"
    if params and method == "GET":
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    elif params:
        data = urllib.parse.urlencode(params, doseq=True).encode()
    r = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {key}", "User-Agent": UA,
        "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(r, timeout=60) as resp:
        return json.loads(resp.read())


def _list(path, params):
    params = dict(params, limit=100)
    while True:
        page = _req("GET", path, params)
        yield from page["data"]
        if not page.get("has_more"):
            return
        params["starting_after"] = page["data"][-1]["id"]


def normalize_state(text):
    t = (text or "").strip()
    if not t:
        return None
    up = t.upper().replace(".", "")
    if up in STATES:
        return up
    return NAME_TO_CODE.get(re.sub(r"\s+", " ", t.lower()))


def enabled():
    return bool(os.environ.get("STRIPE_API_KEY"))


def get_subscribers():
    """Return (subscribers, problems).
    subscribers: list of dicts {email, plan, sub_id, welcomed}
    problems: list of dicts {msg, sub_id, flagged} for subscriptions that could not be resolved.
    flagged=True means Jake was already told about it."""
    products, subs, problems = {}, [], []
    for s in _list("/subscriptions", {"status": "all", "expand[]": "data.customer"}):
        if s["status"] not in ("active", "trialing"):
            continue
        cust = s.get("customer") or {}
        email = (cust.get("email") if isinstance(cust, dict) else None) or ""
        item = s["items"]["data"][0]
        pid = item["price"]["product"]
        if pid not in products:
            products[pid] = _req("GET", f"/products/{pid}").get("name", "")
        pname = products[pid].lower()
        if "all states" in pname or "all-states" in pname:
            plan = "ALL"
        else:
            typed = ""
            sessions = _req("GET", "/checkout/sessions", {"subscription": s["id"], "limit": 1})["data"]
            if sessions:
                for f in sessions[0].get("custom_fields") or []:
                    label = ((f.get("label") or {}).get("custom") or f.get("key") or "").lower()
                    if "state" in label:
                        typed = (f.get("text") or {}).get("value") or (f.get("dropdown") or {}).get("value") or ""
            plan = normalize_state(typed)
            if not plan:
                problems.append({"sub_id": s["id"], "flagged": bool((s.get("metadata") or {}).get(FLAG_KEY)),
                                 "msg": f"{email or s['id']} typed the state '{typed}', which isn't a US state. "
                                        f"Fix: add the line '{email},XX' (XX = their state code) to the SUBSCRIBERS secret, "
                                        f"then run the Monthly update workflow with send_to = one and only_email = {email}."})
                continue
        if not email:
            problems.append({"sub_id": s["id"], "flagged": bool((s.get("metadata") or {}).get(FLAG_KEY)),
                             "msg": f"Subscription {s['id']} has no customer email."})
            continue
        subs.append({"email": email, "plan": plan, "sub_id": s["id"],
                     "welcomed": bool((s.get("metadata") or {}).get(WELCOME_KEY))})
    return subs, problems


def mark_flagged(sub_id):
    _req("POST", f"/subscriptions/{sub_id}", {f"metadata[{FLAG_KEY}]": "reported"})


def mark_welcomed(sub_id, release):
    _req("POST", f"/subscriptions/{sub_id}", {f"metadata[{WELCOME_KEY}]": release})
