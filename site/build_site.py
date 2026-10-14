"""Generate the static website from data/processed/<release>/summary.json into ./public.

Usage: python site/build_site.py --release 2026-10
"""
import argparse, html, json, os, shutil, sys, datetime
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
from config import (SITE_NAME, SITE_URL, CONTACT_EMAIL, CHECKOUT, WAITLIST_FORM, STATES, NTEE,
                    RECENT_MONTHS, slug)

e = html.escape
OUT = os.path.join(ROOT, "public")


def fmt(n):
    return f"{n:,}"


def short(ym):
    import calendar
    return f"{calendar.month_abbr[int(ym[4:])]} {ym[:4]}"


def period(S):
    return f"{short(S['recent'][0])} – {short(S['recent'][-1])}"


# ---------------------------------------------------------------- building blocks
def page(path, title, desc, body, S, schema=None):
    canonical = SITE_URL.rstrip("/") + path
    ld = f'<script type="application/ld+json">{json.dumps(schema)}</script>' if schema else ""
    doc = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website"><meta property="og:url" content="{canonical}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,800&family=Source+Sans+3:wght@400;600&family=IBM+Plex+Mono:wght@500&display=swap">
<link rel="stylesheet" href="/style.css">
{ld}
</head><body>
<header class="top"><div class="bar">
  <a class="brand" href="/"><span class="seal" aria-hidden="true">501</span>{e(SITE_NAME)}</a>
  <nav><a href="/#states">States</a><a href="/#categories">Categories</a><a href="/pricing/">Pricing</a></nav>
</div></header>
<main>{body}</main>
<footer class="foot"><div class="bar">
  <p>Data: IRS Exempt Organizations Business Master File, release {e(S['release'])}. Approval month = the IRS ruling date on each organization's determination letter. {e(SITE_NAME)} is independent and not affiliated with the IRS.</p>
  <p><a href="/about/">About the data</a> · <a href="/terms/">Terms</a> · <a href="/privacy/">Privacy</a> · <span class="mono">{e(CONTACT_EMAIL)}</span></p>
</div></footer>
</body></html>"""
    dest = os.path.join(OUT, path.strip("/"), "index.html") if path != "/" else os.path.join(OUT, "index.html")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w") as f:
        f.write(doc)
    return path


def bars(counts, labels, note_last=True):
    """Inline SVG bar chart, one bar per month, drawn to a single scale."""
    w, h, pad_b, pad_t = 640, 180, 34, 18
    n = len(counts); mx = max(counts) or 1
    bw = (w - 20) / n
    out = []
    for i, (c, lab) in enumerate(zip(counts, labels)):
        bh = (h - pad_b - pad_t) * c / mx
        x = 10 + i * bw + bw * 0.15
        y = h - pad_b - bh
        last = i == n - 1
        cls = "col-last" if last else "col"
        out.append(f'<rect class="{cls}" x="{x:.1f}" y="{y:.1f}" width="{bw*0.7:.1f}" height="{bh:.1f}" rx="2"><title>{e(lab)}: {fmt(c)}</title></rect>')
        if c and (bh > 16 or last):
            out.append(f'<text class="v" x="{x + bw*0.35:.1f}" y="{y - 5:.1f}" text-anchor="middle">{fmt(c)}</text>')
        out.append(f'<text class="m" x="{x + bw*0.35:.1f}" y="{h - 14}" text-anchor="middle">{e(lab.split()[0][:3])}</text>')
    note = '<p class="fine">The latest month fills in further over the next IRS releases.</p>' if note_last else ""
    return (f'<figure class="chart"><svg viewBox="0 0 {w} {h}" role="img" aria-label="New 501(c)(3) approvals by month">'
            + "".join(out) + f"</svg>{note}</figure>")


def table(rows, show_state=False):
    head = "<th>Organization</th><th>City</th>" + ("<th>State</th>" if show_state else "") + "<th>Category</th><th>Approved</th>"
    body = "".join(
        f"<tr><td>{e(r['name'])}</td><td>{e(r['city'])}</td>" + (f"<td>{e(r['state'])}</td>" if show_state else "")
        + f"<td>{e(r['category'])}</td><td class='mono'>{short(r['ruling'])}</td></tr>" for r in rows)
    return f'<div class="tbl"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def counts_list(items, link=None):
    li = []
    for name, n in items:
        label = f'<a href="{link(name)}">{e(name)}</a>' if link and link(name) else e(name)
        li.append(f"<li><span>{label}</span><span class='mono'>{fmt(n)}</span></li>")
    return f'<ul class="counts">{"".join(li)}</ul>'


def cta(scope, total, S):
    if CHECKOUT.get("state") or CHECKOUT.get("national"):
        btns = ""
        if CHECKOUT.get("state"):
            btns += f'<a class="btn" href="{e(CHECKOUT["state"])}">Get {e(scope)} – $29/mo</a>'
        if CHECKOUT.get("national"):
            btns += f'<a class="btn ghost" href="{e(CHECKOUT["national"])}">All states – $99/mo</a>'
    elif WAITLIST_FORM:
        btns = f'<a class="btn" href="{e(WAITLIST_FORM)}">Get early access</a>'
    else:
        btns = f'<a class="btn" href="mailto:{e(CONTACT_EMAIL)}?subject=Early%20access%20{e(scope)}">Get early access</a><span class="mono addr">{e(CONTACT_EMAIL)}</span>'
    return f"""<section class="cta">
  <div><h2>Get the full list of {fmt(total)}</h2>
  <p>Every organization with its mailing address, EIN, category, approval month and annual filing type, as a spreadsheet. A new list arrives each month when the IRS publishes its update.</p>
  <p class="fine">Preview shows {min(12,total)} of {fmt(total)}. <a href="/sample.csv">Download a free 20-row sample</a>.</p></div>
  <div class="cta-btns">{btns}</div>
</section>"""


def buyers():
    return """<section class="who"><h2>Who uses this list</h2><div class="grid3">
<div><h3>Nonprofit CPAs and bookkeepers</h3><p>Every new 501(c)(3) has to file a Form 990, 990-EZ or 990-N within its first year. Reach them before they pick a preparer.</p></div>
<div><h3>Insurance agents</h3><p>New boards look for directors &amp; officers, general liability and event coverage in their first months.</p></div>
<div><h3>Software, banks and agencies</h3><p>Donor CRMs, fundraising platforms, nonprofit banking, web and grant-writing services all sell to organizations at this stage.</p></div>
</div></section>"""


def dataset_ld(name, desc, url):
    return {"@context": "https://schema.org", "@type": "Dataset", "name": name, "description": desc,
            "url": url, "creator": {"@type": "Organization", "name": SITE_NAME},
            "isBasedOn": "https://www.irs.gov/charities-non-profits/exempt-organizations-business-master-file-extract-eo-bmf",
            "license": "https://www.usa.gov/government-works"}


# ---------------------------------------------------------------- pages
def build(S):
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copy(os.path.join(HERE, "style.css"), os.path.join(OUT, "style.css"))
    paths = []
    N = S["national"]; per = period(S)
    st_link = lambda code: f"/new-nonprofits/{S['states'][code]['slug']}/"
    cat_by_name = {v["name"]: v for v in S["categories"].values()}
    cat_link = lambda name: f"/category/{cat_by_name[name]['slug']}/" if name in cat_by_name else None

    # --- home
    states_sorted = sorted(S["states"].items(), key=lambda kv: kv[1]["name"])
    tiles = "".join(f'<a class="tile" href="{st_link(c)}"><span>{e(v["name"])}</span><b class="mono">{fmt(v["count"])}</b></a>'
                    for c, v in states_sorted)
    body = f"""
<section class="hero"><div class="stamp" aria-hidden="true"><span>Approved</span><b>{e(short(S['latest_month']))}</b></div>
<p class="eyebrow">New 501(c)(3) organizations · updated monthly from IRS records</p>
<h1>{fmt(N['count'])} nonprofits got IRS approval in the last {RECENT_MONTHS} months</h1>
<p class="lede">Each one is a brand-new organization choosing its accountant, insurance, bank and software for the first time. See them by state, city and cause, then get the full list with mailing addresses.</p>
</section>
{bars(N['trend'], S['trend_labels'])}
<section id="states"><h2>New nonprofits by state, {e(per)}</h2><div class="tiles">{tiles}</div></section>
<section id="categories" class="two">
  <div><h2>By cause</h2>{counts_list(N['categories'], cat_link)}</div>
  <div><h2>By annual filing</h2>{counts_list(N['filing'])}
  <p class="fine">Form 990-N is for groups expecting under $50,000 a year. Groups filing a 990 or 990-EZ are larger and usually need a paid preparer.</p></div>
</section>
{buyers()}
{cta('your state', N['count'], S)}"""
    desc = f"{fmt(N['count'])} new 501(c)(3) nonprofits approved by the IRS {per}, by state, city and cause. Monthly lists with mailing addresses."
    paths.append(page("/", f"New 501(c)(3) Nonprofits by State – {fmt(N['count'])} approved {per} | {SITE_NAME}", desc, body, S,
                      dataset_ld("New 501(c)(3) nonprofits, United States", desc, SITE_URL)))

    # --- state pages
    for code, v in states_sorted:
        path = st_link(code)
        cities = v["cities"]
        city_link = lambda c, v=v, cities=cities: (f"/new-nonprofits/{v['slug']}/{cities[c]['slug']}/" if c in cities else None)
        top_cat = v["categories"][0][0] if v["categories"] else "—"
        top_city = v["top_cities"][0][0] if v["top_cities"] else "—"
        months_txt = ", ".join(f"{fmt(n)} in {short(m)}" for m, n in v["by_month"].items())
        rel_txt = (f" {fmt(v['new_in_release'])} appeared for the first time in this month's IRS release." if S["has_diff"] else "")
        body = f"""
<nav class="crumbs"><a href="/">All states</a> / {e(v['name'])}</nav>
<section class="hero"><p class="eyebrow">{e(v['name'])} · IRS release {e(S['release'])}</p>
<h1>New nonprofits in {e(v['name'])}</h1>
<p class="lede">{fmt(v['count'])} organizations in {e(v['name'])} received 501(c)(3) approval from the IRS between {e(per)} ({e(months_txt)}).{e(rel_txt)} The most common cause was {e(top_cat)}, and {e(top_city)} had the most new groups.</p></section>
{bars(v['trend'], S['trend_labels'])}
<section><h2>Latest approvals in {e(v['name'])}</h2>{table(v['preview']) if v['preview'] else '<p>No approvals in this period.</p>'}</section>
{cta(v['name'], v['count'], S)}
<section class="two">
  <div><h2>Cities with the most new nonprofits</h2>{counts_list(v['top_cities'], city_link) if v['top_cities'] else '<p>—</p>'}</div>
  <div><h2>By cause</h2>{counts_list(v['categories'], cat_link) if v['categories'] else '<p>—</p>'}</div>
</section>
<section><h2>Annual filing requirement</h2>{counts_list(v['filing']) if v['filing'] else '<p>—</p>'}</section>
{buyers()}"""
        desc = f"{fmt(v['count'])} new 501(c)(3) nonprofits approved in {v['name']} {per}. Latest approvals, top cities and causes. Full list with addresses."
        paths.append(page(path, f"New Nonprofits in {v['name']} – {fmt(v['count'])} approved {per} | {SITE_NAME}", desc, body, S,
                          dataset_ld(f"New 501(c)(3) nonprofits in {v['name']}", desc, SITE_URL.rstrip('/') + path)))

        # --- city pages
        for cname, cv in cities.items():
            cpath = f"/new-nonprofits/{v['slug']}/{cv['slug']}/"
            body = f"""
<nav class="crumbs"><a href="/">All states</a> / <a href="{path}">{e(v['name'])}</a> / {e(cname)}</nav>
<section class="hero"><p class="eyebrow">{e(cname)}, {e(code)} · IRS release {e(S['release'])}</p>
<h1>New nonprofits in {e(cname)}, {e(v['name'])}</h1>
<p class="lede">{fmt(cv['count'])} organizations based in {e(cname)} received 501(c)(3) approval between {e(per)}. That is {cv['count']*100/max(v['count'],1):.0f}% of all new nonprofits in {e(v['name'])} in the same period.</p></section>
<section><h2>Latest approvals in {e(cname)}</h2>{table(cv['preview'])}</section>
<section><h2>By cause</h2>{counts_list(cv['categories'], cat_link)}</section>
{cta(cname, cv['count'], S)}"""
            desc = f"{fmt(cv['count'])} new 501(c)(3) nonprofits in {cname}, {code} approved {per}. See the latest approvals and get the full list."
            paths.append(page(cpath, f"New Nonprofits in {cname}, {code} – {fmt(cv['count'])} approved {per} | {SITE_NAME}", desc, body, S))

    # --- category pages
    for code, cv in S["categories"].items():
        if not cv["count"]:
            continue
        cpath = f"/category/{cv['slug']}/"
        top_st = [(S["states"][s]["name"], n) for s, n in cv["top_states"]]
        body = f"""
<nav class="crumbs"><a href="/">Home</a> / {e(cv['name'])}</nav>
<section class="hero"><p class="eyebrow">NTEE group {e(code)} · IRS release {e(S['release'])}</p>
<h1>New {e(cv['name'])} nonprofits</h1>
<p class="lede">{fmt(cv['count'])} {e(cv['name'].lower())} organizations received 501(c)(3) approval nationwide between {e(per)}.</p></section>
<section><h2>Latest approvals</h2>{table(cv['preview'], show_state=True)}</section>
<section><h2>States with the most</h2>{counts_list(top_st, lambda n: next((st_link(c) for c, s in S['states'].items() if s['name']==n), None))}</section>
{cta(cv['name'] + ' list', cv['count'], S)}"""
        desc = f"{fmt(cv['count'])} new {cv['name']} 501(c)(3) nonprofits approved {per}, by state. Monthly lists with addresses."
        paths.append(page(cpath, f"New {cv['name']} Nonprofits – {fmt(cv['count'])} approved {per} | {SITE_NAME}", desc, body, S))

    # --- pricing / about / legal
    body = f"""
<section class="hero"><p class="eyebrow">Pricing</p><h1>One list a month, cancel anytime</h1>
<p class="lede">You get a spreadsheet of every new 501(c)(3) approved in your area, delivered by email each month after the IRS posts its update (usually the second week of the month).</p></section>
<section class="plans">
  <div class="plan"><h2>One state</h2><p class="price">$29<span>/month</span></p><ul><li>Every new 501(c)(3) in one state</li><li>Name, EIN, mailing address, city, ZIP</li><li>Cause category, approval month, filing type</li><li>Flags organizations new since last month</li></ul></div>
  <div class="plan"><h2>All states</h2><p class="price">$99<span>/month</span></p><ul><li>The national file, about {fmt(round(N['count']/RECENT_MONTHS, -2))} new organizations a month</li><li>Per-state files included</li><li>Same fields as the state plan</li></ul></div>
</section>
{cta('your state', N['count'], S)}"""
    paths.append(page("/pricing/", f"Pricing | {SITE_NAME}", "Monthly lists of newly approved 501(c)(3) nonprofits. $29/month per state or $99/month for all states.", body, S))

    body = f"""<section class="hero"><h1>About the data</h1></section><section class="prose">
<p>Every month the IRS publishes the Exempt Organizations Business Master File, a public list of every tax-exempt organization. Each record includes a ruling date: the month the IRS issued the organization's determination letter. {e(SITE_NAME)} downloads every state file, keeps the 501(c)(3) organizations with a ruling date in the last {RECENT_MONTHS} months, and sorts them by state, city and cause (NTEE code).</p>
<p>The newest month in each release is incomplete, because the IRS adds organizations to the file a few weeks after their letters go out. Counts for that month rise in later releases.</p>
<p>Records include the organization's name, EIN and mailing address as published by the IRS. We do not include the "in care of" person named in the IRS file, phone numbers or email addresses.</p>
<p>Source: <a href="https://www.irs.gov/charities-non-profits/exempt-organizations-business-master-file-extract-eo-bmf">IRS EO BMF extract</a>. {e(SITE_NAME)} is not affiliated with the IRS.</p></section>"""
    paths.append(page("/about/", f"About the data | {SITE_NAME}", "How the new nonprofit lists are built from IRS records.", body, S))
    body = f"""<section class="hero"><h1>Terms</h1></section><section class="prose">
<p>Lists are compiled from public IRS records and provided as is. Use them for business-to-business outreach to organizations. Do not use them to make decisions about any individual's credit, employment, housing or insurance eligibility. Follow the CAN-SPAM Act and telemarketing rules when you contact organizations.</p>
<p>Subscriptions renew monthly and can be cancelled at any time from the link in your receipt. Contact <span class="mono">{e(CONTACT_EMAIL)}</span> with questions.</p></section>"""
    paths.append(page("/terms/", f"Terms | {SITE_NAME}", "Terms of use.", body, S))
    body = f"""<section class="hero"><h1>Privacy</h1></section><section class="prose">
<p>We collect the email address and billing details you provide at checkout (payments are processed by Stripe) and use them only to deliver your lists and manage your subscription. We do not sell customer information. Email <span class="mono">{e(CONTACT_EMAIL)}</span> to have your information deleted.</p></section>"""
    paths.append(page("/privacy/", f"Privacy | {SITE_NAME}", "Privacy policy.", body, S))

    body = f"""<section class="hero"><p class="eyebrow">Payment received</p><h1>You're subscribed</h1>
<p class="lede">Your first list will arrive by email within one business day, then every month after the IRS publishes its update (usually mid-month). Check your spam folder for mail from {e(CONTACT_EMAIL)}.</p></section>
<section class="prose"><p>Questions about the data or your plan: <span class="mono">{e(CONTACT_EMAIL)}</span>.</p></section>"""
    page("/thanks/", f"Thank you | {SITE_NAME}", "Subscription confirmed.", body, S)
    with open(os.path.join(OUT, "_headers"), "w") as f:
        f.write("/thanks/*\n  X-Robots-Tag: noindex\n")

    # --- extras
    sample = os.path.join(ROOT, "data", "deliverables", S["release"], "SAMPLE.csv")
    if os.path.exists(sample):
        shutil.copy(sample, os.path.join(OUT, "sample.csv"))
    today = datetime.date.today().isoformat()
    with open(os.path.join(OUT, "sitemap.xml"), "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for p in paths:
            f.write(f"  <url><loc>{SITE_URL.rstrip('/')}{p}</loc><lastmod>{today}</lastmod></url>\n")
        f.write("</urlset>\n")
    with open(os.path.join(OUT, "robots.txt"), "w") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL.rstrip('/')}/sitemap.xml\n")
    page("/404/", f"Page not found | {SITE_NAME}", "Page not found.",
         '<section class="hero"><h1>Page not found</h1><p class="lede"><a href="/">See new nonprofits by state</a></p></section>', S)
    shutil.move(os.path.join(OUT, "404", "index.html"), os.path.join(OUT, "404.html")); os.rmdir(os.path.join(OUT, "404"))
    print(f"wrote {len(paths)} pages to public/")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--release", required=True); a = ap.parse_args()
    build(json.load(open(os.path.join(ROOT, "data", "processed", a.release, "summary.json"))))
