import os
import sys
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
import concurrent.futures

# Add root directory to path
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
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        result = response.choices[0].message.content
        
        # Safely split the response based on our prompt formatting
        try:
            email_part = result.split("DM:")[0].replace("EMAIL:", "").strip()
            dm_part = result.split("DM:")[1].strip()
        except IndexError:
            email_part, dm_part = result, "Formatting error from LLM"
            
        return influencer.name, email_part, dm_part
        
    except Exception as e:
        return influencer.name, "Error", f"Error: {e}"

def personalize_messages():
    print("Starting High-Speed AI Personalization...")
    
    if not os.path.exists(config.FILTERED_DATA):
        print("Error: Filtered data not found. Run filtering.py first.")
        return
        
    df = pd.read_csv(config.FILTERED_DATA)
    # Only generate messages for influencers who passed the criteria
    passed_df = df[df['Status'] == 'Passed'].copy()
    
    if passed_df.empty:
        print("No passed influencers found. Check your filtering thresholds.")
        return

    total = len(passed_df)
    print(f"Generating custom messages for {total} qualified influencers using multithreading...\n")
    
    passed_df['Email Pitch'] = ""
    passed_df['Instagram DM'] = ""
    
    completed = 0
    
    # Process 5 API calls concurrently to speed up the loop without triggering Groq rate limits
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