"""Shared constants: states, IRS code labels, site settings."""

SITE_NAME = "New Nonprofit List"
SITE_URL = "https://newnonprofitlist.com"     # your domain, no trailing slash
CONTACT_EMAIL = "hello@newnonprofitlist.com"  # an inbox you read (Cloudflare Email Routing can forward it)

# Stripe Payment Links (Stripe Dashboard -> Payment Links). Empty = buttons go to the early-access form.
CHECKOUT = {
    "state": "https://buy.stripe.com/aFafZj9iR2Yo17z0dMgrS00",      # $29/month, one state (custom text field "Which state?")
    "national": "https://buy.stripe.com/7sY6oJeDb56w03vaSqgrS01",   # $99/month, all states
}
WAITLIST_FORM = "https://tally.so/r/WJ92MP"    # Tally form URL for early access (used while CHECKOUT is empty)
CUSTOMER_PORTAL = "https://billing.stripe.com/p/login/aFafZj9iR2Yo17z0dMgrS00"  # Stripe customer portal login link, for customers to cancel or update cards

IRS_BASE = "https://www.irs.gov/pub/irs-soi/eo_{code}.csv"

STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "DC": "District of Columbia",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
    "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
    "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon",
    "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
    "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia",
    "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
    "PR": "Puerto Rico",
}

NTEE = {
    "A": "Arts, Culture & Humanities", "B": "Education", "C": "Environment",
    "D": "Animal-Related", "E": "Health Care", "F": "Mental Health & Crisis Intervention",
    "G": "Diseases, Disorders & Medical Disciplines", "H": "Medical Research",
    "I": "Crime & Legal-Related", "J": "Employment", "K": "Food, Agriculture & Nutrition",
    "L": "Housing & Shelter", "M": "Public Safety & Disaster Relief", "N": "Recreation & Sports",
    "O": "Youth Development", "P": "Human Services",
    "Q": "International & Foreign Affairs", "R": "Civil Rights & Advocacy",
    "S": "Community Improvement", "T": "Philanthropy & Grantmaking",
    "U": "Science & Technology", "V": "Social Science", "W": "Public & Societal Benefit",
    "X": "Religion-Related", "Y": "Mutual & Membership Benefit", "Z": "Unclassified",
}

FOUNDATION = {
    "02": "Private operating foundation", "03": "Private operating foundation",
    "04": "Private foundation", "10": "Church", "11": "School", "12": "Hospital",
    "13": "Supports gov't college", "14": "Governmental unit",
    "15": "Public charity (public support)", "16": "Public charity (509(a)(2))",
    "17": "Supporting organization", "18": "Public safety testing",
    "21": "Supporting org (Type I)", "22": "Supporting org (Type II)",
    "23": "Supporting org (Type III-FI)", "24": "Supporting org (Type III-NFI)",
}

FILING = {
    "01": "Form 990 / 990-EZ", "02": "Form 990-N (under $50k)", "03": "Group return",
    "06": "Not required (church)", "13": "Not required (religious)", "00": "Not required",
}

# How many recent approval months to treat as "new" and publish
RECENT_MONTHS = 3
# Months of history used for the trend table on each page
TREND_MONTHS = 12
# Free preview rows per page
PREVIEW_ROWS = 12
# Minimum new orgs (in RECENT_MONTHS) for a city to get its own page
CITY_MIN = 4


def slug(s: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
