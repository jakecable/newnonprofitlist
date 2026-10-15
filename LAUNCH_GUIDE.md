# New Nonprofit List — Launch Guide

*Written October 14, 2026. Prices and availability were checked that day.*

This guide takes you from nothing to a live website, working checkout, automatic monthly delivery, and a plan for your first paying customer. Do the steps in order.

---

## 0. What you're launching

**The product.** Every month the IRS approves thousands of new 501(c)(3) nonprofits and lists them in a free public file (the *Exempt Organizations Business Master File*). New nonprofits need an accountant, insurance, a bank, donor software and a website, and haven't chosen any yet. You sell companies a clean monthly spreadsheet of these new organizations, by state.

**The customers:**
- Nonprofit CPAs and bookkeepers
- Insurance agents (directors & officers, general liability)
- Donor-software and fundraising companies
- Banks and credit unions
- Web designers and grant writers

**How customers find you:** about 70+ free pages (one per state, big city and cause) that rank in Google for searches like "new nonprofits in Texas". Each page shows real counts and a 12-row preview, with a button to buy the full list.

**Plans:** $29/month for one state, $99/month for all states.

**What runs on its own:** on the 16th of every month, GitHub downloads the new IRS files, rebuilds every page, publishes the site and emails each subscriber their spreadsheet.

**Your ongoing work:**
- About 5 minutes per new customer.
- About 5 minutes a month to check the run.
- Marketing (Section 10).

### Costs

| Item | Cost |
|---|---|
| Domain (Cloudflare Registrar, .com) | $10.46/year, same price at renewal |
| Website hosting (Cloudflare Pages, free plan) | $0 |
| Code + monthly automation (GitHub Free, private repo, 2,000 Actions minutes/month) | $0 (each run takes ~5 min) |
| Email delivery (Resend free: 3,000 emails/month, 100/day) | $0 until ~100 subscribers, then $20/month |
| Early-access form (Tally free: unlimited forms and submissions) | $0 |
| Payments (Stripe) | Stripe's standard card fee per payment; no monthly fee |
| **Total to launch** | **≈ $10.46** |

### Time

| Phase | Time |
|---|---|
| Accounts, domain, GitHub, first run (Steps 1–6) | ~2 hours, one evening |
| Stripe + email delivery (Steps 7–8) | ~1 hour |
| Google indexing | Days to weeks (automatic) |

---

## 1. Accounts to create first

Use one email address for all of them, ideally a Gmail you check daily.

| Service | Sign-up link | Used for |
|---|---|---|
| Cloudflare | https://dash.cloudflare.com/sign-up | Domain, website hosting, email forwarding |
| GitHub | https://github.com/signup | Stores the code; runs the monthly job |
| Tally | https://tally.so | Early-access form |
| Stripe | https://dashboard.stripe.com/register | Subscriptions (Step 7) |
| Resend | https://resend.com | Sends the monthly spreadsheets (Step 8) |
| Google Search Console | https://search.google.com/search-console | Gets the site into Google |

For Stripe you'll need your legal name, address, date of birth, the last 4 of your SSN (or EIN), and a bank account for payouts. You can sign up as an **individual / sole proprietor**; you don't need an LLC to start.

---

## 2. Buy the domain (15 minutes)

### Pick the name

The working name **fresh501.com is taken** (registered July 2026). As of October 14, 2026, the .com registry returned no record for these three, which normally means they're available. Confirm at checkout.

| Domain | Why |
|---|---|
| **newnonprofitlist.com** ← recommended | Says exactly what it is and matches what buyers type into Google |
| new501list.com | Short; reads well to accountants and insurance agents |
| freshnonprofits.com | More brand-like |

These were checked and are **taken**: fresh501.com, newnonprofits.com. The code is already set up for **newnonprofitlist.com**. If you pick another, see Step 4.

### Buy it at Cloudflare

1. Log in to https://dash.cloudflare.com.
2. In the left sidebar, open **Domain Registration → Register Domains**.
3. Search for `newnonprofitlist.com` and add it to the cart.
4. Fill in your contact details. Cloudflare hides them from public WHOIS for free.
5. Pay $10.46 and make sure **Auto-renew** is on.

Because Cloudflare is now both your registrar and your DNS, Steps 5, 6 and 8 mostly configure themselves.

### Set up your business email (free)

This gives you `hello@newnonprofitlist.com` and forwards it to your Gmail.

1. In Cloudflare, click the domain → **Email → Email Routing → Get started**.
2. Create the address `hello` → destination: your Gmail. Click the confirmation link Cloudflare emails you.
3. Let Cloudflare add the MX/TXT records it suggests.
4. Optional: to *reply* as hello@, add it in Gmail under **Settings → Accounts → Send mail as**.

---

## 3. Put the code on GitHub (20 minutes)

1. Sign in to GitHub → **+** (top right) → **New repository**.
   - Name: `newnonprofitlist`
   - Visibility: **Private**, so nobody can copy your setup
   - Don't add a README; the project has one.
   - Click **Create repository**.
2. Choose one way to add the files:

   **Option A — let Claude do it (easiest).** Tell Claude the repo name (e.g. `jakecable/newnonprofitlist`) and Claude will push the code. If Claude says GitHub isn't connected for this chat, it will tell you what to click.

   **Option B — upload it yourself.**
   1. Unzip `newnonprofitlist.zip`.
   2. On the empty repo page, click **uploading an existing file**.
   3. Drag in **everything inside** the unzipped folder, including the hidden `.github` folder. On a Mac, press `Cmd + Shift + .` in Finder to show hidden folders.
   4. Click **Commit changes**.
   5. Check that the repo shows `.github/workflows/monthly.yml`. Without it, nothing runs.

---

## 4. Personalize the settings (10 minutes)

In GitHub, open `pipeline/config.py`, click the pencil icon, and check these lines:

```python
SITE_NAME = "New Nonprofit List"
SITE_URL = "https://newnonprofitlist.com"     # your domain, no trailing slash
CONTACT_EMAIL = "hello@newnonprofitlist.com"
WAITLIST_FORM = ""      # fill in after Step 6
CHECKOUT = {"state": "", "national": ""}   # fill in after Step 7
CUSTOMER_PORTAL = ""    # fill in after Step 7
```

If you bought a different domain, change `SITE_NAME`, `SITE_URL` and `CONTACT_EMAIL`. In `.github/workflows/monthly.yml`, you can also change `CF_PROJECT: newnonprofitlist` to any lowercase name. That only sets your free `*.pages.dev` address.

Click **Commit changes**.

---

## 5. Connect GitHub to Cloudflare hosting (15 minutes)

GitHub builds the site and needs permission to publish it to Cloudflare.

1. **Find your Cloudflare Account ID.** Cloudflare dashboard → **Workers & Pages**. The Account ID is in the right sidebar. Copy it.
2. **Create an API token.**
   1. Click your profile icon (top right) → **My Profile → API Tokens → Create Token → Create Custom Token**.
   2. Name: `github-pages-deploy`.
   3. Permissions: **Account → Cloudflare Pages → Edit**.
   4. Click **Continue to summary → Create Token** and copy it. Cloudflare shows it only once.
3. **Save both in GitHub.**
   1. Repo → **Settings → Secrets and variables → Actions → New repository secret**.
   2. Add `CLOUDFLARE_ACCOUNT_ID` = the Account ID.
   3. Add `CLOUDFLARE_API_TOKEN` = the token.

---

## 6. First run, go live, and check the data (30 minutes)

### Run it

1. Repo → **Actions** tab. If GitHub asks, click **I understand my workflows, go ahead and enable them**.
2. Click **Monthly update → Run workflow**. Leave *send_to* = `nobody` → **Run workflow**.
3. Wait about 5–10 minutes until it shows a green check. The first run downloads ~50 IRS files.
4. Your site is now live at `https://newnonprofitlist.pages.dev`.

### Attach your domain

1. Cloudflare → **Workers & Pages** → `newnonprofitlist` → **Custom domains → Set up a custom domain**.
2. Enter `newnonprofitlist.com`, then confirm. DNS is added automatically because the domain is on Cloudflare.
3. Repeat for `www.newnonprofitlist.com`.
4. HTTPS turns on by itself within a few minutes.

### Check the data before you tell anyone about the site

Open the site and check each of these:

- [ ] **The home page headline number is in the thousands** for 3 months nationally. Hundreds or zero means files were missing; see Troubleshooting.
- [ ] **Big states look right.** Texas, California, Florida and New York should be among the largest counts, and Louisiana should be well below them.
- [ ] **The last bar on each chart is the shortest or close to it.** That's expected: the newest month is partial because the IRS keeps adding organizations for several weeks.
- [ ] **Spot-check 5 organizations.**
  1. Pick 5 names from different state pages.
  2. Look each one up at the IRS **Tax Exempt Organization Search** (https://apps.irs.gov/app/eos/) or on ProPublica Nonprofit Explorer.
  3. Confirm the name, city and that it's a 501(c)(3).
  4. Confirm the approval month matches the ruling or determination date.
- [ ] **The free sample downloads.** Open `https://newnonprofitlist.com/sample.csv` in Excel or Google Sheets and confirm the columns are filled.
- [ ] **The paid files exist.** Actions → the latest run → scroll to **Artifacts** → download `lists-2026-10`. Open `LA.csv` and `ALL.csv`.

If all six pass, the build is accurate and ready.

### Known limits (be upfront with customers)

- Lists have **mailing addresses only**, no phone or email. Many buyers send mail or look up the organization's website themselves.
- A mailing address is sometimes a founder's home or a registered agent.
- Some new organizations have no cause code yet; they show as "Unclassified".
- "Approval month" is the IRS ruling date, not the date the group was founded.

### Troubleshooting

| Symptom | Fix |
|---|---|
| Red ✗ at "Download IRS files" | The IRS site had a hiccup. Wait an hour and run again; files already downloaded are skipped. If it fails twice, send Claude the error text from the log. |
| Red ✗ at "Save this month's summary" (push rejected) | Repo → Settings → Actions → General → Workflow permissions → **Read and write permissions** → Save. Run again. |
| Red ✗ at "Publish the website" | Re-check both Cloudflare secrets (Step 5). The token needs *Cloudflare Pages: Edit*. |
| Site shows the old version | Cloudflare → your Pages project → Deployments: confirm the newest one is "Production". |

---

## 7. Collect early-access sign-ups now, payments next (Tally + Stripe)

Collect interest first, then turn on payments. You can do both on day 1, or turn on Stripe once 3–5 people have signed up.

### 7a. Early-access form (10 minutes)

1. Go to Tally → **Create form**.
2. Title: *Get the new nonprofit list for your state*.
3. Add these questions:
   - Work email (required)
   - Company
   - What do you sell to nonprofits? (choices: Accounting / bookkeeping · Insurance · Software · Banking · Web or marketing · Grant writing · Other)
   - Which states? (text)
   - Would $29/month per state be worth it? (Yes / Maybe / No)
4. Turn on email notifications to yourself.
5. **Publish**, copy the form link and paste it into `WAITLIST_FORM` in `config.py`. Commit.
6. Actions → **Run workflow** (send_to = nobody) so every "Get early access" button points to the form.

### 7b. Stripe subscriptions (40 minutes)

1. **Activate your account.**
   1. Stripe Dashboard → **Activate payments**.
   2. Business type **Individual / Sole proprietorship**.
   3. Website: `https://newnonprofitlist.com`.
   4. Description: *Monthly data subscriptions listing newly IRS-approved nonprofits for B2B outreach.*
   5. Add your bank account.
2. **Set your public details.**
   1. Settings → **Public details**.
   2. Terms of service URL: `https://newnonprofitlist.com/terms/`.
   3. Privacy policy URL: `https://newnonprofitlist.com/privacy/`.
   4. Support email: `hello@newnonprofitlist.com`.
3. **Create the products** (Product catalog → Add product):
   - *New Nonprofit List — One State*, **Recurring**, $29.00 USD **monthly**.
   - *New Nonprofit List — All States*, **Recurring**, $99.00 USD **monthly**.
4. **Create a Payment Link for each product** (Payment Links → New):
   - **Add custom field**:
     - Type **Text**
     - Label: `Which state? (2-letter code, e.g. TX)`
     - Required
     - Use Text, not Dropdown: dropdowns made in the Dashboard allow only 10 options.
     - The All-States link doesn't need this field.
   - **Collect customer names**: business name.
   - **Require customers to accept your terms of service**: on.
   - Optional: **Include a free trial** of 14 days. This makes a "yes" much easier for a first customer.
   - **After payment**: *Don't show confirmation page* → redirect to `https://newnonprofitlist.com/thanks/`.
   - Create the link and copy it.
5. **Turn on the customer portal**, so customers can cancel or update their card without emailing you.
   1. Settings → Billing → **Customer portal** → **Activate link**.
   2. Allow canceling subscriptions.
   3. Copy the login link.
6. Paste everything into `config.py`:
   ```python
   CHECKOUT = {"state": "https://buy.stripe.com/…", "national": "https://buy.stripe.com/…"}
   CUSTOMER_PORTAL = "https://billing.stripe.com/p/login/…"
   ```
   Commit, then run the workflow (send_to = nobody). Buttons now say "Get [State] – $29/mo" and "All states – $99/mo".
7. **Test it end to end.** Stripe has a **Test mode** toggle; make a test-mode copy of one link to try the full flow. Or buy one real month yourself and refund it from the Payments page.

---

## 8. Automatic email delivery (Resend) (30 minutes)

1. **Add your domain.**
   1. Resend → **Domains → Add Domain** → `newnonprofitlist.com`.
   2. Resend shows several DNS records (SPF/DKIM). Add each one in Cloudflare → your domain → **DNS → Records → Add record**, copying type, name and value exactly.
   3. Click **Verify** in Resend. It usually verifies within minutes.
2. **Create an API key.** Resend → **API Keys → Create** with *Sending access*. Copy it.
3. **Add three GitHub secrets** (repo → Settings → Secrets and variables → Actions):
   - `RESEND_API_KEY` = the key
   - `FROM_EMAIL` = `New Nonprofit List <lists@newnonprofitlist.com>`
   - `SUBSCRIBERS` = for now, just yourself, e.g. `yourgmail@gmail.com,LA`
4. **Test it.**
   1. Actions → Run workflow → send_to = **one**, only_email = `yourgmail@gmail.com`.
   2. Within ~10 minutes you should get an email with `new-nonprofits-la-2026-10.csv` attached.
   3. If it lands in spam, mark it "Not spam".

**The SUBSCRIBERS secret format** is one customer per line: `email,STATE` or `email,ALL`.

```
jane@smithcpa.com,TX
ops@donorapp.io,ALL
yourgmail@gmail.com,LA
```

GitHub never shows a secret again after you save it. **Keep the master list in a private note or spreadsheet** and paste the whole thing every time you update the secret.

---

## 9. Your routines

### When someone pays: nothing to do

Customer lists come straight from Stripe (this needs the `STRIPE_API_KEY` secret; see below).
- **New subscriber:** within about an hour, the **Welcome new subscribers** workflow finds them, reads the state they typed at checkout, and emails them their first list. Free-trial customers count.
- **Cancellation:** they drop out automatically and stop getting emails.
- **Typo in the state** (for example "Texs"): you get one email at hello@ that says who it is and how to fix it.
- It's still worth replying to Stripe's "new payment" email with a short thank-you: *"Your Texas list is in your inbox. What will you use it for?"* Their answer tells you which buyer type to market to next.

**The SUBSCRIBERS secret** is now only for free extras: you, testers, or anyone you comp. Format: `email,STATE` or `email,ALL`, one per line.

**Stripe key setup (one time, 3 minutes):**
1. Stripe → **Developers** → **API keys** → **Create restricted key** → name it `github-delivery`.
2. Set these permissions; leave everything else as **None**:
   - **Subscriptions:** Write
   - **Customers:** Read
   - **Checkout Sessions:** Read
   - **Products:** Read
3. Click **Create key**, copy it (it starts with `rk_live_`), and add it as the GitHub secret `STRIPE_API_KEY`.

### On the 16th of each month (2 minutes)

The run starts on its own. Check Actions for a green check and glance at the home page number. Everyone on the list gets their file automatically.

---

## 10. Getting your first customer (no phone calls, no LinkedIn posts)

You'll use three channels, from fastest to slowest:

| Channel | What you do | Speed | Who it reaches |
|---|---|---|---|
| **LinkedIn messages** | Connect with and message specific buyers. No public posts. | Days to weeks | The buyers themselves: nonprofit CPAs, insurance agents, nonprofit software sales reps |
| **Email** (optional) | Short personal emails to firms that work with nonprofits | Days to weeks | Same buyers |
| **Social posts** (Reddit, Facebook, X/Bluesky) | One chart post a month from the ready-made kit | Weeks to months | Mostly site visitors and links back to your site, which help your Google ranking. Fewer direct buyers. |
| **Google** | Nothing after setup | Weeks to months | Buyers searching for lists |

Your first customers will most likely come from **LinkedIn messages and email**. Most of your buyers live there. The social posts mainly bring visitors, links and credibility.

### Week 1 — get found

1. **Google Search Console.**
   1. Add property → **Domain** → `newnonprofitlist.com`.
   2. Choose Cloudflare when it asks for your DNS provider, and it can add the verification record for you.
   3. Then **Sitemaps** → submit `https://newnonprofitlist.com/sitemap.xml`.
   4. Use **URL inspection → Request indexing** on the home page and the five biggest state pages.
2. **Bing Webmaster Tools** (https://www.bing.com/webmasters). Import your site from Search Console with one click. Bing also feeds DuckDuckGo and some AI search tools.
3. **Update your LinkedIn profile.** This isn't a post; it's what people see when your message arrives.
   - Headline: *"Founder, New Nonprofit List — monthly lists of newly approved 501(c)(3)s for nonprofit service providers."*
   - Add the website link to your profile.

### Weeks 1–8 — LinkedIn messages (no posting)

**How LinkedIn's limits work on a free account:**
- You can message anyone you're already connected with, for free.
- Free accounts can only add a personal note to roughly **5–10 connection requests a month**. Send the rest **without a note**, then message them once they accept.

**Who to look for.** Search LinkedIn people results for these titles:
- "nonprofit CPA" or "nonprofit audit"
- "nonprofit insurance" or "D&O insurance"
- "nonprofit banking"
- "account executive" at donor-software companies (Bloomerang, Donorbox, Givebutter, Neon One and similar)
- "grant writer" or "nonprofit consultant"

Start with Texas, California, Florida, New York and Louisiana.

**Pace.** 10–15 connection requests a day, 5 days a week. LinkedIn limits how many invitations you can send each week, so a steady pace keeps your account safe. Expect a share of people to accept, and message each one the day they do.

**Message 1 (after they accept):**

> Thanks for connecting, [First name]. I noticed you work with nonprofits, so this may be useful. I track every new 501(c)(3) the IRS approves. [Texas] had **[210]** in the last three months, and each one has to start filing a 990 and pick an accountant/insurer/bank. Want me to send you this month's [Texas] list (names, addresses, cause, filing type) free?

**Message 2 (only if they reply yes):**

> Here you go — attached is [Texas]. If it's useful, you can keep getting it monthly here: [Stripe link] ($29/mo, cancel anytime). What would make it more useful for you?

Download their state's file from the latest GitHub run (Actions → latest run → Artifacts → `lists-…`) and attach it, or add them to `SUBSCRIBERS` and use send_to = **one**.

**Don't** send a second follow-up to people who don't reply, and don't paste the same message into dozens of chats at once. LinkedIn flags that.

### Monthly — social posts (about 5 minutes, after the 16th)

Every monthly run now makes a **social kit**. Download it from GitHub → Actions → latest run → Artifacts → `social-YYYY-MM`. It contains:
- `top_states.png` — the top 10 states for new nonprofits
- `trend.png` — 12 months of new approvals nationwide
- `louisiana.png` — Louisiana by cause
- `captions.md` — ready-to-paste text for Reddit, Facebook and X/Bluesky/Threads, with this month's real numbers

Use a brand account named **New Nonprofit List** where the platform allows it, so it stays separate from your personal profile.

| Where | What to post | Rules to know |
|---|---|---|
| **Reddit r/dataisbeautiful** | `top_states.png` with the [OC] title from captions.md | Titles must include [OC]. Put your source and tool in the first comment, and say it's your project. |
| **Reddit state/city subreddits** (r/Louisiana, r/texas…) | The state chart or a local number ("92 new nonprofits in Louisiana this summer") | Check each subreddit's rules first. Many ban self-promotion. Reddit's guideline is about 90% normal participation, 10% your own stuff. |
| **Facebook groups** for grant writers, nonprofit consultants and accountants | The Facebook caption + one chart | Join and read the group rules. Many allow helpful data posts but not ads. |
| **Facebook page / X / Bluesky / Threads** | The short caption + `top_states.png` | No special rules. Low reach at first, but each post links back to your site. |

Never post the same thing in many subreddits at once. Reddit's spam filters catch that.

### Weeks 1–8 — email (optional, works alongside LinkedIn)

**Who to email:** nonprofit-focused CPA firms and insurance agencies in the 5 states with the most new nonprofits, plus Louisiana, where you can say you're local. Find them by searching Google for `nonprofit CPA firm [city]` or `nonprofit insurance agent [state]`. Their websites list emails.

**Pace:** 10–15 personal emails a day, each written to one person. Not bulk blasts.

**Rules** (US CAN-SPAM Act):
- An honest subject line.
- Say who you are.
- Include a physical mailing address. A PO box or virtual mailbox works if you'd rather not use your home address.
- Include a way to opt out, and honor it.

**Template:**

> **Subject:** 37 new nonprofits in Dallas since June
>
> Hi [First name],
>
> I noticed [Firm] works with nonprofits, so this might be useful. The IRS approved **[37]** new 501(c)(3)s in the Dallas area between [June] and [August]. Each one has to start filing a Form 990 and is choosing an accountant now.
>
> I compile these into a spreadsheet each month (name, mailing address, EIN, cause, filing type). Want me to send you this month's Texas list for free? If it's useful, it's $29/month after that.
>
> Jake Cable
> New Nonprofit List · newnonprofitlist.com
> [mailing address]
> *If you'd rather not hear from me, just reply "no thanks."*

**When they say yes:** add them to `SUBSCRIBERS` and send with send_to = **one**. Write back after a week: *"Was it useful? Here's the link to keep getting it: [Stripe link]."* With the 14-day trial on, you can send the Stripe link from the start.

**Founding-customer offer** for the first 10 customers: create a promotion code in Stripe (Product catalog → Coupons → e.g. 33% off forever, which brings $29 down to about $19/mo) and enable promotion codes on the Payment Link. *"Founding price, locked in for as long as you stay."*

### Score it at day 30 and day 60

| Number | Where to see it | Good sign by day 60 |
|---|---|---|
| Google impressions | Search Console → Performance | 1,000+ and rising |
| Early-access sign-ups | Tally | 10+ |
| LinkedIn + email messages → replies | LinkedIn inbox, Sent folder | 10%+ reply rate |
| Free trials → paid | Stripe | 1–3 paying customers |

- **Continue and double down** if you have any paying customer, or 10+ sign-ups.
- **Rethink** if you have under 1,000 impressions, no sign-ups and no replies by day 60. The likely fixes are the buyer type, adding emails/websites to the data, or the price. Bring the numbers to Claude.

### Realistic path to $1,000/month

$1,000/month is about 35 state subscriptions, or about 10 all-states customers, or a mix such as 20 state + 4 all-states. With 10–15 LinkedIn messages or emails a day plus monthly social posts, getting there in 4–6 months is a reasonable target. That's a target, not a guarantee.

---

## 11. Legal and tax basics (not legal or tax advice)

- **The data** is public IRS information about organizations. The lists leave out the "in care of" person, phone numbers and emails on purpose. Your Terms page limits use to B2B outreach and forbids using it for credit, employment, housing or insurance decisions about individuals.
- **Email outreach** must follow CAN-SPAM (Section 10).
- **Sales tax:** some states tax data or information subscriptions. Stripe Tax (paid) can calculate it. Before revenue gets meaningful, ask a tax preparer whether you need to collect it in Louisiana or in your customers' states.
- **Business structure:** you can start as a sole proprietor under your own name. Consider registering a trade name or forming an LLC with the Louisiana Secretary of State once you have paying customers.
- **Income:** keep Stripe payouts in a separate bank account if you can. Stripe gives you a 1099-K summary for taxes.

---

## 12. What Claude can do next

- Push the code to your GitHub repo and watch the first run with you.
- Review your first real data and the spot-checks in Step 6.
- Tweak the monthly social kit (more charts, other states, different captions).
- Help you find LinkedIn prospects and tailor messages for each buyer type.
- Automate the "someone paid" step with a Stripe webhook, so new subscribers are added and emailed without you.
- Add website/email lookups for each organization, which would justify a higher price.
- Add a $15 one-time "this month's list" option for buyers who won't subscribe.

---

## Quick reference

| Task | Where |
|---|---|
| Run the job now | GitHub → Actions → Monthly update → Run workflow |
| Send a new customer their list | Run workflow → send_to = one, only_email = their address |
| Download this month's paid files | Actions → latest run → Artifacts → `lists-YYYY-MM` |
| Download this month's social kit | Actions → latest run → Artifacts → `social-YYYY-MM` |
| Add or remove a customer | Automatic from Stripe; `SUBSCRIBERS` secret only for free extras |
| Change prices or links | `pipeline/config.py` → commit → Run workflow |
| See who paid / cancelled | Stripe Dashboard → Payments / Subscriptions |
| See Google traffic | Search Console → Performance |
