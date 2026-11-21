import os
from dotenv import load_dotenv

from llm_client import (
    GeminiProvider,
    OllamaProvider,
    LLMClient
)

# Load environment variables
load_dotenv(override=True)

# Select LLM provider
provider_name = input(
    "Choose provider (gemini/ollama): "
).strip().lower()

# Initialize selected provider
if provider_name == "gemini":

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL")

    if not api_key:
        raise ValueError("Gemini API key not found in .env")

    if not model:
        raise ValueError("Gemini model not found in .env")

    provider = GeminiProvider(api_key, model)

elif provider_name == "ollama":

    model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

    provider = OllamaProvider(model)

else:
    raise ValueError("Invalid provider selected")

# Initialize common client
client = LLMClient(provider)

# Get user prompt
prompt = input("Enter your question: ")

# Generate response
answer = client.generate(prompt)

print("\nLLM Response:")
print(answer)