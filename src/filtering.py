import os
import sys
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def evaluate_influencer(row):
    """Evaluates an influencer based on config thresholds and returns Status and Reason."""
    reasons = []
    followers = row.get('Follower Count', 0)
    if pd.isna(followers) or not (config.MIN_FOLLOWERS <= followers <= config.MAX_FOLLOWERS):
        reasons.append(f"Followers ({followers}) out of range {config.MIN_FOLLOWERS}-{config.MAX_FOLLOWERS}")
        
    engagement = row.get('Engagement Rate (%)', 0)
    if pd.isna(engagement) or engagement < config.MIN_ENGAGEMENT_RATE:
        reasons.append(f"Engagement ({engagement}%) below minimum {config.MIN_ENGAGEMENT_RATE}%")
        
    if reasons:
        return "Failed", " | ".join(reasons)
    
    return "Passed", "Meets all criteria"

def filter_data():
    print("Starting filtering and classification...")
    
    if not os.path.exists(config.ENRICHED_DATA):
        print(f"Error: {config.ENRICHED_DATA} not found. Run enrichment.py first.")
        return

    df = pd.read_csv(config.ENRICHED_DATA)
    status_results = df.apply(evaluate_influencer, axis=1)
    
    df['Status'] = [res[0] for res in status_results]
    df['Reason'] = [res[1] for res in status_results]
    
    os.makedirs(os.path.dirname(config.FILTERED_DATA), exist_ok=True)
    df.to_csv(config.FILTERED_DATA, index=False)
    
    passed_count = len(df[df['Status'] == 'Passed'])
    
    print(f"Filtering complete! Saved to {config.FILTERED_DATA}")
    print(f"Total Profiles Evaluated: {len(df)}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {len(df) - passed_count}")

if __name__ == "__main__":
    filter_data()