import os
import sys
import json
from apify_client import ApifyClient
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

load_dotenv()


def discover_influencers():
    print(f"Starting automated discovery for hashtags: {', '.join(config.HASHTAGS)}")

    apify_token = os.getenv("APIFY_API_TOKEN")
    if not apify_token:
        print("Error: APIFY_API_TOKEN not found in .env. Please add it.")
        return False

    client = ApifyClient(apify_token)

    try:
        print("Phase 1: Searching recent hashtag posts to find active creators")
        search_input = {
            "hashtags": config.HASHTAGS,
            "resultsType": "posts",
            "resultsLimit": 50,
        }
        search_run = client.actor("apify/instagram-hashtag-scraper").call(run_input=search_input)
        search_items = client.dataset(search_run.default_dataset_id).list_items().items

        print(f"Posts returned: {len(search_items)}")
        if not search_items:
            print("Hashtag search returned no posts.")
            return False

        usernames = set()
        for item in search_items:
            username = item.get("ownerUsername")
            if not username and isinstance(item.get("owner"), dict):
                username = item["owner"].get("username")
            if username:
                usernames.add(username)

        if not usernames:
            print("Failed to find any creators from the hashtag search.")
            return False

        print(f"Found {len(usernames)} unique creators! Generating profile URLs...")
        target_usernames = sorted(usernames)[:60]
        profile_urls = [f"https://www.instagram.com/{user}/" for user in target_usernames]

        print(f"Phase 2: Scraping {len(profile_urls)} profiles (This will take a few minutes)")
        profile_input = {
            "directUrls": profile_urls,
            "resultsType": "details",
        }

        profile_run = client.actor("apify/instagram-scraper").call(run_input=profile_input)
        profile_items = client.dataset(profile_run.default_dataset_id).list_items().items

        if not profile_items:
            print("Profile scrape returned no data.")
            return False

        os.makedirs(os.path.dirname(config.RAW_PROFILES), exist_ok=True)
        with open(config.RAW_PROFILES, "w", encoding="utf-8") as f:
            json.dump(profile_items, f, indent=4, ensure_ascii=False)

        print(f"Automated Discovery complete! Saved {len(profile_items)} real profiles to {config.RAW_PROFILES}")
        return True

    except Exception as e:
        print(f"\n[ERROR] Cloud scraping failed: {e}")
        return False


if __name__ == "__main__":
    discover_influencers()