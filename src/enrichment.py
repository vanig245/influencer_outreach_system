import os
import re
import sys
import json
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def extract_email(item):
    """Only real public sources: business email field, then bio. Never guessed."""
    for value in (item.get("businessEmail"), item.get("biography")):
        if value:
            match = EMAIL_RE.search(str(value))
            if match:
                return match.group(0)
    return "Not Found"


def compute_engagement(item, followers):
    """Average (likes + comments) of recent posts / followers * 100. None if not computable."""
    if not followers:
        return None
    posts = item.get("latestPosts") or []
    rates = []
    for post in posts:
        likes = post.get("likesCount")
        comments = post.get("commentsCount") or 0
        if likes is None or likes < 0:
            continue
        rates.append((likes + comments) / followers * 100)
    return round(sum(rates) / len(rates), 2) if rates else None


def extract_themes(item):
    """Hashtags from recent captions, otherwise the bio, otherwise Not Available."""
    tags = []
    for post in item.get("latestPosts") or []:
        tags += post.get("hashtags") or []
    if tags:
        top = pd.Series(tags).str.lower().value_counts().head(5).index.tolist()
        return ", ".join(top)
    bio = (item.get("biography") or "").replace("\n", " ").strip()
    return bio if bio else "Not Available"


def enrich_data():
    print("Starting data enrichment...")

    if not os.path.exists(config.RAW_PROFILES):
        print("Error: raw_profiles.json not found.")
        return

    with open(config.RAW_PROFILES, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    for item in data:
        username = item.get("username")
        if not username:
            continue
        followers = item.get("followersCount")

        rows.append({
            "Influencer Name": item.get("fullName") or username,
            "Username": username,
            "Platform": "Instagram",
            "Profile URL": f"https://www.instagram.com/{username}/",
            "Follower Count": followers,
            "Engagement Rate (%)": compute_engagement(item, followers),
            "Category / HASHTAGS": item.get("businessCategoryName") or "Not Available",
            "Content Themes": extract_themes(item),
            "Contact Email": extract_email(item),
            "Website": item.get("externalUrl") or "Not Found",
            "Bio": (item.get("biography") or "").replace("\n", " "),
        })

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(config.ENRICHED_DATA), exist_ok=True)
    df.to_csv(config.ENRICHED_DATA, index=False)

    found = (df["Contact Email"] != "Not Found").sum()
    print(f"Enrichment complete! Saved {len(df)} profiles ({found} with a real public email).")


if __name__ == "__main__":
    enrich_data()