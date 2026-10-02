import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from src.discovery import discover_influencers
from src.enrichment import enrich_data
from src.filtering import filter_data
from src.personalization import personalize_messages
from src.sender import execute_sending_layer

def run_pipeline():
    
    print("\nSTEP 1: DISCOVERY")
    if not discover_influencers():
        print("❌ Discovery module failed. Exiting pipeline safely to prevent cascading errors.")
        sys.exit(1)
    
    print("\nSTEP 2: ENRICHMENT")
    enrich_data()
    
    print("\nSTEP 3: FILTERING & CLASSIFICATION")
    filter_data()
    
    print("\nSTEP 4: AI PERSONALIZATION")
    personalize_messages()
    
    print("\nSTEP 5: SENDING LAYER")
    execute_sending_layer()
    
    print("\nPipeline execution completed successfully!")


if __name__ == "__main__":
    try:
        run_pipeline()
    except KeyboardInterrupt:
        print("\nPipeline execution was stopped by the user.")
    except Exception as e:
        print(f"\nPipeline failed due to a critical error: {e}")