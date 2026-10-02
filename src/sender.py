import os
import re
import sys
import pandas as pd
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def load_or_create_log():
    if os.path.exists(config.OUTREACH_LOG):
        return pd.read_csv(config.OUTREACH_LOG)
    return pd.DataFrame(columns=["Influencer", "Email", "Platform", "Message Generated", "Sent Status", "Date"])


def save_dm_queue(df):
    """Instagram DMs are never auto-sent. Queue them for manual sending, keeping earlier statuses."""
    queue_path = os.path.join(config.DATA_DIR, "dm_queue.csv")
    dm_queue = df[["Influencer Name", "Profile URL", "Instagram DM"]].copy()
    dm_queue["Status"] = "Pending - send manually"
    if os.path.exists(queue_path):
        old = pd.read_csv(queue_path)
        dm_queue = dm_queue[~dm_queue["Profile URL"].isin(old["Profile URL"])]
        dm_queue = pd.concat([old, dm_queue], ignore_index=True)
    os.makedirs(config.DATA_DIR, exist_ok=True)
    dm_queue.to_csv(queue_path, index=False)
    print(f"DM queue saved to {queue_path} ({len(dm_queue)} entries)")


def execute_sending_layer():
    print("Starting Sending Layer Simulation...")

    if not os.path.exists(config.MESSAGES_DATA):
        print("Error: Messages data not found. Run personalization.py first.")
        return

    df = pd.read_csv(config.MESSAGES_DATA)
    log_df = load_or_create_log()
    sent_emails = set(log_df["Email"].dropna().astype(str))
    logged = set(log_df["Influencer"].dropna().astype(str))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_logs = []

    for _, row in df.iterrows():
        influencer = str(row["Influencer Name"])
        email = row["Contact Email"]
        pitch = row.get("Email Pitch")

        if pd.isna(email) or email == "Not Found" or not EMAIL_RE.fullmatch(str(email).strip()):
            print(f"[{influencer}] Skipped: no public email (DM queue only).")
            if influencer not in logged:
                new_logs.append({"Influencer": influencer, "Email": email, "Platform": "Instagram",
                                 "Message Generated": "Yes", "Sent Status": "Skipped - No Email", "Date": now})
            continue

        if pd.isna(pitch) or str(pitch).startswith("Error"):
            print(f"[{influencer}] Skipped: email message was not generated.")
            continue

        if str(email) in sent_emails:
            print(f"[{influencer}] Skipped: already contacted (duplicate prevention).")
            continue

        print(f"\nTo: {email}\nSubject: Collaboration with {config.BRAND_NAME}\nBody:\n{pitch}\n")
        new_logs.append({"Influencer": influencer, "Email": email, "Platform": "Instagram",
                         "Message Generated": "Yes", "Sent Status": "Simulated Send Success", "Date": now})
        sent_emails.add(str(email))

    save_dm_queue(df)

    if new_logs:
        updated_log = pd.concat([log_df, pd.DataFrame(new_logs)], ignore_index=True)
        os.makedirs(os.path.dirname(config.OUTREACH_LOG), exist_ok=True)
        updated_log.to_csv(config.OUTREACH_LOG, index=False)
        print(f"Outreach log updated: {config.OUTREACH_LOG}")
    else:
        print("No new messages to send.")


if __name__ == "__main__":
    execute_sending_layer()