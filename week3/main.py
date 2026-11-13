import os
import time
import uuid
import random

import pymongo
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from pymongo.server_api import ServerApi

load_dotenv(override=True)


MONGODB_URI = os.getenv("MONGODB_URI")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3.2")


INPUT_PRICE = float(os.getenv("INPUT_PRICE", "0.30"))
OUTPUT_PRICE = float(os.getenv("OUTPUT_PRICE", "2.50"))

REQUEST_TIMEOUT = 120
MAX_RETRIES = 4

if not MONGODB_URI:
    raise ValueError("MONGODB_URI is missing. Check your .env file.")


mongo_client = MongoClient(
    MONGODB_URI,
    server_api=ServerApi("1"),
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=10000,
    retryWrites=True
)


mongo_client.admin.command("ping")

db = mongo_client["GenAI_Monitoring"]
collection = db["api_usage_logs"]

print("MongoDB connected successfully!")
print("Database:", db.name)
print("Collection:", collection.name)
print("Model:", MODEL_NAME)


def calculate_cost(input_tokens, output_tokens):

    input_cost = input_tokens * INPUT_PRICE / 1_000_000
    output_cost = output_tokens * OUTPUT_PRICE / 1_000_000

    return input_cost + output_cost


def retry_delay(attempt):

    delay = min(2 ** (attempt - 1), 16)

    return delay + random.uniform(0, 1)


def is_temporary_error(error):

    if isinstance(error, requests.exceptions.HTTPError):
        code = error.response.status_code if error.response is not None else None
        return code in [408, 429, 500, 502, 503, 504]

    return isinstance(
        error,
        (requests.exceptions.Timeout, requests.exceptions.ConnectionError)
    )


def save_log(record):

    for attempt in range(1, 4):

        try:

            with pymongo.timeout(10):

                collection.update_one(
                    {"_id": record["_id"]},
                    {"$setOnInsert": record},
                    upsert=True
                )

            print("Log saved in MongoDB!")
            return True

        except PyMongoError as error:

            print(f"MongoDB error: {error}")

            if attempt == 3:
                print("Unable to save the log.")
                return False

            time.sleep(retry_delay(attempt))

    return False


def ask_ollama(prompt):

    request_id = str(uuid.uuid4())

    for attempt in range(1, MAX_RETRIES + 1):

        start_time = time.perf_counter()

        input_tokens = 0
        output_tokens = 0
        total_tokens = 0

        response_text = ""
        error_message = None
        last_error = None
        status = "failed"

        try:

            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL_NAME,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()
            data = response.json()

            response_text = data.get("response", "")

            input_tokens = data.get("prompt_eval_count", 0) or 0
            output_tokens = data.get("eval_count", 0) or 0
            total_tokens = input_tokens + output_tokens

            status = "success"

        except Exception as error:

            last_error = error
            error_message = str(error)

            print(f"API attempt {attempt} failed: {error_message}")

        latency = time.perf_counter() - start_time

        estimated_cost = calculate_cost(input_tokens, output_tokens)

        log_record = {
            "_id": f"{request_id}_{attempt}",
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc),
            "model": MODEL_NAME,
            "prompt": prompt,
            "attempt": attempt,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "latency_seconds": round(latency, 3),
            "estimated_cost_usd": round(estimated_cost, 10),
            "status": status,
            "error": error_message
        }

        save_log(log_record)

        print("\n========== API MONITORING ==========")
        print("Request ID:", request_id)
        print("Attempt:", attempt)
        print("Status:", status)
        print("Input Tokens:", input_tokens)
        print("Output Tokens:", output_tokens)
        print("Total Tokens:", total_tokens)
        print("Latency:", round(latency, 3), "seconds")
        print("Estimated Cost: $", estimated_cost)

        if status == "success":

            print("\n========== OLLAMA RESPONSE ==========")
            print(response_text)

            return response_text

        if attempt == MAX_RETRIES or not is_temporary_error(last_error):

            print("\nRequest failed permanently.")
            break

        wait_time = retry_delay(attempt)

        print(f"Retrying after {wait_time:.2f} seconds...")

        time.sleep(wait_time)

    return None


if __name__ == "__main__":

    while True:

        prompt = input("\nEnter your question (or type exit): ")

        if prompt.lower() == "exit":
            print("Application stopped.")
            break

        if not prompt.strip():
            print("Please enter a valid question.")
            continue

        ask_ollama(prompt)
