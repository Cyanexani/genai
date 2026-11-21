import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# STEP 1: Load environment variables
load_dotenv()

# STEP 2: Retrieve API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("Gemini API key is missing!")

# STEP 3: Initialize Gemini client
client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(
        timeout= 120000
    )
)

# STEP 4: Select Gemini model
MODEL_NAME = "gemini-3.5-flash-lite"

print("Gemini client initialized successfully!")


# STEP 5: Test Gemini API connection
try:

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents="What is Artificial Intelligence?"
    )

    print("\n========== GEMINI RESPONSE ==========")
    print(response.text)

except Exception as e:

    print("\n========== GEMINI API ERROR ==========")
    print("Error Type:", type(e).__name__)
    print("Error Message:", e)