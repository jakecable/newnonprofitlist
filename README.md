# New Nonprofit List — monthly lists of newly approved nonprofits

**Start with `LAUNCH_GUIDE.md`.** It walks through the domain, GitHub, Cloudflare, Stripe, email delivery and getting your first customer.

A website that shows how many new 501(c)(3) nonprofits the IRS approved in every state, city and cause, and sells the full list (name, EIN, mailing address, category, approval month, filing type) as a monthly subscription.

Buyers find it through Google ("new nonprofits in Texas", "newly approved 501c3 list"). Nobody has to make sales calls.

**Plans:** $29/month for one state, $99/month for all states.
**Running cost:** about $10.46/year for the domain. Hosting (Cloudflare Pages), automation (GitHub Actions, private repo) and email (Resend, up to ~100 subscribers) are free.

## How it works

Once a month (the 16th), a GitHub Action runs five steps:

1. Downloads the IRS Exempt Organizations Business Master File for every state (`pipeline/fetch.py`).
2. Keeps the 501(c)(3)s approved in the last 3 months and flags the ones that are new since last month (`pipeline/build.py`).
3. Rebuilds the website and publishes it to Cloudflare Pages: state, city and category pages with real counts, a 12-month chart and a 12-row free preview (`site/build_site.py`).
4. Makes a social media kit with charts and captions (`pipeline/social.py`).
5. Emails each paying subscriber their spreadsheet (`pipeline/deliver.py`).

## Setup

See **LAUNCH_GUIDE.md** for the full step-by-step. In short:

1. Domain on Cloudflare.
2. Private GitHub repo with these files.
3. Two GitHub secrets for Cloudflare: `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`.
4. Run the *Monthly update* workflow.
5. Add Tally, Stripe and Resend.

The secrets for email delivery are `RESEND_API_KEY`, `FROM_EMAIL` and `STRIPE_API_KEY` (subscribers are read from Stripe; the welcome workflow emails new ones hourly). `SUBSCRIBERS` is optional, for free extras.

## Data notes

- **Source:** IRS EO BMF extract (public, updated monthly). The approval month is the IRS ruling date.
- **The newest month is always partial.** The IRS adds organizations a few weeks after their letters go out.
- **Organization data only.** The "in care of" person, phone numbers and emails are deliberately left out. That keeps this an organization list, not a list of personal data.
- **Terms of use** (`/terms/`) limit buyers to business-to-business outreach.

## Testing locally

```bash
python tests/make_fixture.py          # writes fake data to data/raw/TEST (never deploy this)
cd pipeline && python build.py --release TEST && cd ..
python site/build_site.py --release TEST
python -m http.server --directory public
```
