import os
import sys
import pandas as pd
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def load_or_create_log():
    """Loads the outreach log or creates an empty one to track status and prevent duplicates."""
    if os.path.exists(config.OUTREACH_LOG):
        return pd.read_csv(config.OUTREACH_LOG)
    return pd.DataFrame(columns=["Influencer", "Email", "Platform", "Message Generated", "Sent Status", "Date"])

def execute_sending_layer():
    print("Starting Sending Layer Simulation...")
    
    if not os.path.exists(config.MESSAGES_DATA):
        print("Error: Messages data not found. Run personalization.py first.")
        return

    df = pd.read_csv(config.MESSAGES_DATA)
    log_df = load_or_create_log()

    sent_emails = set(log_df['Email'].dropna().tolist())
    
    new_logs = []
    
    for index, row in df.iterrows():
        influencer = row['Influencer Name']
        email = row['Contact Email']
        if email == "Not Found" or pd.isna(email):
            print(f"[{influencer}] Skipped: No valid email address.")
            new_logs.append({
                "Influencer": influencer, "Email": email, "Platform": "Instagram",
                "Message Generated": "Yes", "Sent Status": "Skipped - No Email", 
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            continue
            
        if email in sent_emails:
            print(f"[{influencer}] Skipped: Already contacted (Duplicate prevention).")
            continue
            
        print(f"To: {email}")
        print(f"Subject: Collaboration with {config.BRAND_NAME}")
        print(f"Body:\n{row['Email Pitch']}")
        
        new_logs.append({
            "Influencer": influencer, "Email": email, "Platform": "Instagram",
            "Message Generated": "Yes", "Sent Status": "Simulated Send Success", 
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        sent_emails.add(email)

    if new_logs:
        updated_log = pd.concat([log_df, pd.DataFrame(new_logs)], ignore_index=True)
        os.makedirs(os.path.dirname(config.OUTREACH_LOG), exist_ok=True)
        updated_log.to_csv(config.OUTREACH_LOG, index=False)
        print(f"\nOutreach Log updated! Saved to {config.OUTREACH_LOG}")
    else:
        print("\nNo new messages to send.")

if __name__ == "__main__":
    execute_sending_layer()