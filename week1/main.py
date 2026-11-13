from dotenv import load_dotenv
from google import genai
import os


load_dotenv()


api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("Gemini API key not found!")


client = genai.Client(api_key=api_key)


response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents="What is Artificial Intelligence? Explain in simple words."
)


print("\nLLM Response:")
print(response.text)
