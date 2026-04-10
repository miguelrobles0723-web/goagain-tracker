import requests, smtplib, json, os, time
from email.mime.text import MIMEText

# ── CONFIG ──────────────────────────────────────────────
PRICE_LIMIT    = 300
GMAIL_FROM     = "miguelrobles0723@gmail.com"
GMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD", "vgmp dvsq jjrp lpxv")
NOTIFY_EMAIL   = "miguelrobles0723@gmail.com"
CHECK_INTERVAL = 300
SEEN_FILE      = "seen_ids.json"
# ────────────────────────────────────────────────────────

# Use the collection URL directly — more reliable than products.json filtering
URL = "https://goagain.com/collections/iphone/products.json?limit=250"

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"]    = GMAIL_FROM
    msg["To"]      = NOTIFY_EMAIL
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_FROM, GMAIL_PASSWORD)
        s.send_message(msg)
    print(f"  Email sent!")

def check():
    print(f"Checking... ({time.strftime('%H:%M:%S')})")
    try:
        r = requests.get(URL, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        data = r.json()
    except Exception as e:
        print(f"  Fetch error: {e}")
        return

    seen = load_seen()
    new_seen = set(seen)
    found = []

    for product in data.get("products", []):
        title = product.get("title", "")

        # Only look at iPhone 14 Plus, Unlocked
        if "14 plus" not in title.lower():
            continue
        if "unlocked" not in title.lower():
            continue

        for variant in product.get("variants", []):
            vid   = str(variant["id"])
            price = float(variant["price"])
            avail = variant.get("available", False)

            if avail and price <= PRICE_LIMIT and vid not in seen:
                new_seen.add(vid)
                url = f"https://goagain.com/products/{product['handle']}"
                found.append(f"{title} — {variant.get('title','')}\n${price:.2f}\n{url}")
                print(f"  MATCH: {title} ${price}")

    if found:
        send_email(
            subject=f"🔔 {len(found)} iPhone 14 Plus under ${PRICE_LIMIT} on GoAgain!",
            body="New listings found:\n\n" + "\n\n".join(found)
        )

    save_seen(new_seen)
    print(f"  {len(found)} new match(es).")

if __name__ == "__main__":
    print(f"Monitoring GoAgain every {CHECK_INTERVAL//60} min...")
    while True:
        check()
        time.sleep(CHECK_INTERVAL)
