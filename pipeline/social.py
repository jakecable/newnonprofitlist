"""Make this month's social media kit: two chart images and ready-to-paste captions.

Usage: python pipeline/social.py --release 2026-10
Output: data/social/<release>/  (top_states.png, trend.png, louisiana.png, captions.md)
"""
import argparse, json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from config import SITE_URL, SITE_NAME

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INK, MUTED, SEAL, BAR, PAPER = "#0f2a2a", "#56706d", "#1f6f4a", "#a9c9bb", "#f4f7f6"


def style(ax, title, subtitle):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#d3dfdc")
    ax.tick_params(colors=MUTED, labelsize=11, length=0)
    ax.set_title(title, loc="left", fontsize=17, fontweight="bold", color=INK, pad=28)
    ax.text(0, 1.03, subtitle, transform=ax.transAxes, fontsize=11, color=MUTED)


def footer(fig):
    fig.text(0.02, 0.02, f"{SITE_URL.replace('https://', '')}  ·  Source: IRS Exempt Organizations Business Master File",
             fontsize=9, color=MUTED)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--release", required=True); a = ap.parse_args()
    S = json.load(open(os.path.join(ROOT, "data", "processed", a.release, "summary.json")))
    out = os.path.join(ROOT, "data", "social", a.release); os.makedirs(out, exist_ok=True)
    per = f"{S['recent_labels'][0]} – {S['recent_labels'][-1]}"
    N = S["national"]

    # 1) Top 10 states, horizontal bars
    top = sorted(S["states"].items(), key=lambda kv: -kv[1]["count"])[:10][::-1]
    fig, ax = plt.subplots(figsize=(10, 6.2), dpi=150); fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
    names = [v["name"] for _, v in top]; vals = [v["count"] for _, v in top]
    bars = ax.barh(names, vals, color=[BAR] * 9 + [SEAL])
    for b, v in zip(bars, vals):
        ax.text(b.get_width() + max(vals) * 0.01, b.get_y() + b.get_height() / 2, f"{v:,}", va="center", fontsize=11, color=INK)
    ax.set_xticks([]); style(ax, "Where new nonprofits are forming", f"New 501(c)(3) approvals by state, {per}")
    fig.subplots_adjust(left=0.2, right=0.95, top=0.85, bottom=0.08); footer(fig)
    fig.savefig(os.path.join(out, "top_states.png"), facecolor=PAPER); plt.close(fig)

    # 2) National 12-month trend
    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=150); fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
    labels = [l.split()[0][:3] for l in S["trend_labels"]]; t = N["trend"]
    bars = ax.bar(labels, t, color=[BAR] * (len(t) - 1) + [SEAL])
    for b, v in zip(bars, t):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + max(t) * 0.01, f"{v:,}", ha="center", fontsize=9, color=INK)
    ax.set_yticks([]); style(ax, "New 501(c)(3) nonprofits approved each month (U.S.)",
                             "The latest month is still filling in as the IRS adds organizations")
    fig.subplots_adjust(left=0.04, right=0.98, top=0.82, bottom=0.12); footer(fig)
    fig.savefig(os.path.join(out, "trend.png"), facecolor=PAPER); plt.close(fig)

    # 3) Louisiana spotlight (home state) by cause
    la = S["states"].get("LA", {})
    if la.get("categories"):
        cats = la["categories"][:8][::-1]
        fig, ax = plt.subplots(figsize=(10, 6), dpi=150); fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
        bars = ax.barh([c for c, _ in cats], [n for _, n in cats], color=BAR)
        for b, (_, n) in zip(bars, cats):
            ax.text(b.get_width() + 0.3, b.get_y() + b.get_height() / 2, str(n), va="center", fontsize=11, color=INK)
        ax.set_xticks([]); style(ax, f"{la['count']:,} new nonprofits in Louisiana", f"By cause, {per}")
        fig.subplots_adjust(left=0.33, right=0.95, top=0.85, bottom=0.08); footer(fig)
        fig.savefig(os.path.join(out, "louisiana.png"), facecolor=PAPER); plt.close(fig)

    # Captions
    t3 = sorted(S["states"].values(), key=lambda v: -v["count"])[:3]
    top_cat = N["categories"][0][0] if N["categories"] else "—"
    la_line = f"Louisiana added {la.get('count', 0):,}." if la else ""
    cap = f"""# Social kit – IRS release {a.release}

Images: top_states.png, trend.png{', louisiana.png' if la.get('categories') else ''}

## Reddit (r/dataisbeautiful requires [OC] in the title and a source comment)
Title: [OC] New 501(c)(3) nonprofits approved by the IRS, by state ({per})
First comment: Source: IRS Exempt Organizations Business Master File (release {a.release}), approval month = IRS ruling date. Tool: Python + matplotlib. I build these monthly at {SITE_URL} (my project).

## Facebook group / Facebook page
The IRS approved {N['count']:,} new 501(c)(3) nonprofits between {per}. {t3[0]['name']} led with {t3[0]['count']:,}, then {t3[1]['name']} ({t3[1]['count']:,}) and {t3[2]['name']} ({t3[2]['count']:,}). The most common cause was {top_cat}. {la_line}
Every one of these groups now has to file a Form 990 and pick an accountant, insurance and a bank. State-by-state numbers: {SITE_URL}

## X / Bluesky / Threads
{N['count']:,} new nonprofits got IRS approval {per}. Top states: {t3[0]['name']} {t3[0]['count']:,} · {t3[1]['name']} {t3[1]['count']:,} · {t3[2]['name']} {t3[2]['count']:,}. Most common cause: {top_cat}. Your state → {SITE_URL}
"""
    open(os.path.join(out, "captions.md"), "w").write(cap)
    print(f"social kit written to data/social/{a.release}/")


if __name__ == "__main__":
    main()
