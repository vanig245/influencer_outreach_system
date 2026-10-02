import os
import sys
import pandas as pd
from groq import Groq
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_outreach(influencer):
    """Calls Groq API to generate an Email and DM for an influencer."""
    prompt = f"""
    You are an outreach manager for {config.BRAND_NAME}. 
    Brand Context: {config.BRAND_DESC}
    Collaboration Angle: {config.COLLAB_ANGLE}

    Write two personalized outreach messages for an influencer named {influencer['Influencer Name']} in the {influencer['Category / Niche']} niche. 
    Their content themes are: {influencer['Content Themes']}.

    Message 1: Email Collaboration Pitch
    - Must be exactly 60-90 words.
    - Include the value proposition and proposed collaboration.

    Message 2: Instagram DM
    - Must be exactly 15-30 words.
    - Keep it short, natural, and reference their niche.
    - Do not invent facts not provided.

    Format your exact output as:
    EMAIL: [Your email here]
    DM: [Your DM here]
    """
    
    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        result = response.choices[0].message.content

        try:
            email_part = result.split("DM:")[0].replace("EMAIL:", "").strip()
            dm_part = result.split("DM:")[1].strip()
        except IndexError:
            email_part, dm_part = result, "Formatting error from LLM"
            
        return email_part, dm_part
        
    except Exception as e:
        print(f"Error generating message for {influencer['Influencer Name']}: {e}")
        return "Error", "Error"

def personalize_messages():
    print("Starting AI Personalization...")
    
    if not os.path.exists(config.FILTERED_DATA):
        print("Error: Filtered data not found. Run filtering.py first.")
        return
        
    df = pd.read_csv(config.FILTERED_DATA)
    passed_df = df[df['Status'] == 'Passed'].copy()
    
    if passed_df.empty:
        print("No passed influencers found. Check your filtering thresholds.")
        return

    print(f"Generating custom messages for {len(passed_df)} qualified influencers. This will take a moment...")
    
    emails = []
    dms = []
    
    for index, row in passed_df.iterrows():
        email_msg, dm_msg = generate_outreach(row)
        emails.append(email_msg)
        dms.append(dm_msg)
        
    passed_df['Email Pitch'] = emails
    passed_df['Instagram DM'] = dms
    
    os.makedirs(os.path.dirname(config.MESSAGES_DATA), exist_ok=True)
    passed_df.to_csv(config.MESSAGES_DATA, index=False)
    
    print(f"Personalization complete! Saved to {config.MESSAGES_DATA}")

if __name__ == "__main__":
    personalize_messages()