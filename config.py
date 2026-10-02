import os

HASHTAGS = ["techreviewer", "gadgetreview", "techtok", "smartphonereview", "techcreator", "tech"]
MIN_FOLLOWERS = 5000
MAX_FOLLOWERS = 100000
MIN_ENGAGEMENT_RATE = 2.0

BRAND_NAME = "Heins"
BRAND_DESC = "Heins is an education consulting and institutional growth partner dedicated to helping schools and educational organizations improve academic outcomes, strengthen leadership effectiveness, and achieve sustainable growth"
SENDER_NAME = "Alina"
OFFER = "We offer a paid sponsorship for one short UGC video demonstrating our APIs, plus access to our platform and technical support while you create it."
COLLAB_ANGLE = "UGC content demonstrating a real-world multi-agent workflow using our APIs."

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

RAW_PROFILES = os.path.join(DATA_DIR, "raw_profiles.json")
ENRICHED_DATA = os.path.join(DATA_DIR, "enriched.csv")
FILTERED_DATA = os.path.join(DATA_DIR, "filtered.csv")
MESSAGES_DATA = os.path.join(DATA_DIR, "messages.csv")
OUTREACH_LOG = os.path.join(DATA_DIR, "outreach_log.csv")