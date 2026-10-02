import os
import sys
import json
import re
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def extract_email(text):
    """Regex to find an email address inside plain text (like a bio)."""
    if not text:
        return "Not Found"
    match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
    return match.group(0) if match else "Not Found"

def calculate_engagement(followers, posts):
    """Calculate average engagement rate from recent posts."""
    if not followers or followers == 0 or not posts:
        return 0.0
    
    total_engagements = 0
    recent_posts = posts[:5]
    for post in recent_posts:
        total_engagements += post.get('likesCount', 0) + post.get('commentsCount', 0)
        
    avg_engagement = total_engagements / len(recent_posts)
    return (avg_engagement / followers) * 100

def enrich_data():
    if not os.path.exists(config.RAW_PROFILES):
        print(f"Error: {config.RAW_PROFILES} not found. Run discovery.py first.")
        return

    with open(config.RAW_PROFILES, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    enriched_records = []
    
    for item in raw_data:
        followers = item.get('followersCount', 0)
        posts = item.get('latestPosts', [])
        bio = item.get('biography', '')
        email = item.get('publicEmail')
        if not email:
            email = extract_email(bio)

        themes = config.NICHE
        if "ad" in bio.lower() or "sponsor" in bio.lower():
            themes += ", Brand Collaborations"

        record = {
            "Influencer Name": item.get('fullName') or item.get('username', 'Unknown'),
            "Platform": "Instagram",
            "Profile URL": item.get('url', f"https://instagram.com/{item.get('username', '')}"),
            "Follower Count": followers,
            "Engagement Rate (%)": round(calculate_engagement(followers, posts), 2),
            "Category / Niche": config.NICHE,
            "Content Themes": themes,
            "Contact Email": email if email else "Not Found",
            "Audience Age": "Not Available",
            "Audience Gender": "Not Available",
            "Audience Geography": "Not Available"
        }
        enriched_records.append(record)

    df = pd.DataFrame(enriched_records)
    
    os.makedirs(os.path.dirname(config.ENRICHED_DATA), exist_ok=True)
    df.to_csv(config.ENRICHED_DATA, index=False)
    
    print(f"Enrichment complete! Saved {len(df)} enriched profiles to {config.ENRICHED_DATA}")

if __name__ == "__main__":
    enrich_data()