
# Step 1: Import required libraries
import os
from dotenv import load_dotenv
from google import genai

# Step 2: Load environment variables
load_dotenv()

# Step 3: Retrieve Gemini API key
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("Gemini API key not found!")

print("Gemini API key loaded successfully.")

# Step 4: Initialize Gemini client
client = genai.Client(api_key=api_key)

print("Gemini client initialized successfully.")

# Step 5: Select Gemini model
MODEL = "gemini-3.5-flash-lite"

# Step 6: Get user input
print("\n===== GEMINI AI CHAT =====")

user_prompt = input("\nEnter your prompt: ")

# Step 7: Send prompt to Gemini
print("\nGenerating response...")

try:
    response = client.models.generate_content(
        model=MODEL,
        contents=user_prompt
    )

    # Step 8: Display AI response
    print("\n===== AI RESPONSE =====")
    print(response.text)

except Exception as e:
    print("\nError generating response:", e)