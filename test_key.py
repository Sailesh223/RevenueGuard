import google.generativeai as genai

from google import genai

# 1. Initialize the new Client
# It automatically looks for an environment variable, 
# but we will pass it directly for the hackathon.
client = genai.Client(api_key="AIzaSyDB0Uv-plJsPywpg_z9pgMh2s8GngU5qHc")

try:
    # 2. Use the 2026 stable model name
    response = client.models.generate_content(
        model='gemini-2.5-flash', 
        contents="Is the Revenue Guard online?"
    )
    
    print("---")
    print("✅ SUCCESS: The Guard is officially online!")
    print(f"AI Response: {response.text}")
    print("---")

except Exception as e:
    print("---")
    print("❌ 404 Still occurring? Try 'gemini-2.0-flash' as a backup.")
    print(f"Error Details: {e}")
