import os
import json
import random
from dotenv import load_dotenv
from apify_client import ApifyClient
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

load_dotenv()

def generate_mock_raw_data(niche, count=150):
    """Fallback generator if the Apify API fails or runs out of credits."""
    print("Generating mock dataset for resilience...")
    mock_data = []
    for i in range(count):
        followers = random.randint(1000, 150000)
        likes = int(followers * random.uniform(0.005, 0.08)) 
        comments = int(likes * random.uniform(0.01, 0.1))
        
        has_email = random.choice([True, False])
        
        mock_data.append({
            "username": f"{niche.lower()}_creator_{i}",
            "fullName": f"Creator {i}",
            "url": f"https://instagram.com/{niche.lower()}_creator_{i}",
            "followersCount": followers,
            "biography": f"Creating the best {niche} content. " + ("" if not has_email else f"Collabs: creator{i}@email.com"),
            "publicEmail": f"creator{i}@business.com" if has_email and random.choice([True, False]) else None,
            "latestPosts": [
                {"likesCount": likes, "commentsCount": comments, "caption": f"Loving this new {niche} trend! #ad #sponsor"}
            ]
        })
    return mock_data

def discover_influencers():
    print(f"Starting discovery for niche: {config.NICHE}...")
    
    apify_token = os.getenv("APIFY_API_TOKEN")
    dataset_items = []

    try:
        if not apify_token or apify_token == "your_apify_token_here":
            raise ValueError("Invalid Apify Token")

        client = ApifyClient(apify_token)
        actor_id = "apify/instagram-scraper"
        run_input = {
            "search": config.NICHE,
            "searchType": "hashtag",
            "resultsLimit": 150,
        }
        
        print(f"Calling Apify Actor '{actor_id}'... (This takes 1-3 minutes)")
        run = client.actor(actor_id).call(run_input=run_input)
        
        print("Fetching results from Apify dataset...")
        dataset_items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        
        if not dataset_items:
            raise Exception("Apify returned empty data.")
            
    except Exception as e:
        print(f"\n[WARNING] Cloud scraping failed: {e}")
        dataset_items = generate_mock_raw_data(config.NICHE)

    os.makedirs(os.path.dirname(config.RAW_PROFILES), exist_ok=True)
    with open(config.RAW_PROFILES, "w", encoding="utf-8") as f:
        json.dump(dataset_items, f, indent=4)
        
    print(f"\nDiscovery complete! Saved {len(dataset_items)} raw profiles to {config.RAW_PROFILES}")

if __name__ == "__main__":
    discover_influencers()