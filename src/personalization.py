import os
import sys
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
import concurrent.futures
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_outreach(influencer, attempts=3):
    name = str(influencer["Influencer Name"])
    prompt = f"""
You are an outreach manager at {config.BRAND_NAME}, writing on behalf of {config.SENDER_NAME}.
Brand context: {config.BRAND_DESC}
Collaboration angle: {config.COLLAB_ANGLE}
What we offer the creator (use only this, invent nothing else): {config.OFFER}

Creator: {name}
Their bio and content themes: {influencer['Content Themes']}

Write two messages.
EMAIL: 65 to 85 words including greeting and sign-off. Greet by first name only if "{name}" looks like a real person's name, otherwise write "Hi there". Describe what they post in plain words, explain the collaboration and the offer, and sign off with "{config.SENDER_NAME}, {config.BRAND_NAME}".
DM: 15 to 30 words, casual and personal, no sign-off.

Rules: no hashtags, no emojis, no invented facts, offers, prices or numbers, and do not claim to have watched specific videos.
Output exactly:
EMAIL: ...
DM: ...
"""
    for _ in range(attempts):
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            result = response.choices[0].message.content
            if "DM:" not in result:
                continue
            email_part = result.split("DM:")[0].replace("EMAIL:", "").strip()
            dm_part = result.split("DM:")[1].strip()
            if 60 <= len(email_part.split()) <= 90 and 15 <= len(dm_part.split()) <= 30:
                return influencer.name, email_part, dm_part
        except Exception as e:
            print(f"[warn] {name}: attempt failed: {e}")
    return influencer.name, "Error", "Error: could not generate valid messages"

def personalize_messages():
    print("Starting High-Speed AI Personalization...")
    
    if not os.path.exists(config.FILTERED_DATA):
        print("Error: Filtered data not found. Run filtering.py first.")
        return
        
    df = pd.read_csv(config.FILTERED_DATA)
    passed_df = df[df['Status'] == 'Passed'].copy()
    
    if passed_df.empty:
        print("No passed influencers found. Check your filtering thresholds.")
        return

    total = len(passed_df)
    print(f"Generating custom messages for {total} qualified influencers using multithreading...\n")
    
    passed_df['Email Pitch'] = ""
    passed_df['Instagram DM'] = ""
    
    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(generate_outreach, row): row for index, row in passed_df.iterrows()}
        
        for future in concurrent.futures.as_completed(futures):
            index, email_msg, dm_msg = future.result()
            passed_df.at[index, 'Email Pitch'] = email_msg
            passed_df.at[index, 'Instagram DM'] = dm_msg
            
            completed += 1
            print(f"[{completed}/{total}] Generated messages for: {passed_df.at[index, 'Influencer Name']}")
            
    os.makedirs(os.path.dirname(config.MESSAGES_DATA), exist_ok=True)
    passed_df.to_csv(config.MESSAGES_DATA, index=False)
    
    print(f"\nPersonalization complete! Saved to {config.MESSAGES_DATA}")

if __name__ == "__main__":
    personalize_messages()