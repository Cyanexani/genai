# Week 3: Logging tokens, latency and cost for every Gemini API call (MongoDB)
# Written for Google Colab: each "# %%" block is one notebook cell.
# Colab Secrets needed: GEMINI_API_KEY, MONGODB_URI

# %% Cell 1: install libraries
# !pip install -q -U google-genai pymongo pandas matplotlib

# %% Cell 2: load Gemini key from Colab Secrets
from google.colab import userdata

GEMINI_API_KEY = userdata.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("Gemini API key is missing!")

print("Gemini API key configured successfully!")

# %% Cell 3: Gemini client
from google import genai
from google.genai import types

client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(
        timeout=30000
    )
)

MODEL_NAME = "gemini-2.5-flash"

print("Gemini client initialized successfully!")

# %% Cell 4: first test request
response = client.models.generate_content(
    model=MODEL_NAME,
    contents="What is Artificial Intelligence?"
)

print(response.text)

# %% Cell 5: load MongoDB URI
MONGODB_URI = userdata.get("MONGODB_URI")

if not MONGODB_URI:
    raise ValueError("MongoDB connection string is missing!")

print("MongoDB credentials loaded successfully!")

# %% Cell 6: connect to MongoDB
from pymongo import MongoClient
from pymongo.server_api import ServerApi

mongo_client = MongoClient(
    MONGODB_URI,
    server_api=ServerApi("1"),
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=10000,
    timeoutMS=10000,
    retryWrites=True
)

# Test the database connection
mongo_client.admin.command("ping")

# Create database
db = mongo_client["GenAI_Monitoring"]

# Create collection
collection = db["api_usage_logs"]

print("MongoDB connected successfully!")
print("Database:", db.name)
print("Collection:", collection.name)

# %% Cell 7: imports
import time
import uuid
import random
import pymongo

from datetime import datetime, timezone
from pymongo.errors import PyMongoError

# %% Cell 8: pricing
# Gemini 2.5 Flash standard paid-tier pricing
# USD per 1 million tokens

INPUT_PRICE = 0.30
OUTPUT_PRICE = 2.50

def calculate_cost(input_tokens, output_tokens):

    input_cost = (
        input_tokens * INPUT_PRICE / 1_000_000
    )

    output_cost = (
        output_tokens * OUTPUT_PRICE / 1_000_000
    )

    total_cost = input_cost + output_cost

    return total_cost

input_tokens = 1000
output_tokens = 2000

cost = calculate_cost(
    input_tokens,
    output_tokens
)

print("Estimated cost: $", cost)

# %% Cell 9: retry helpers (exponential backoff)
def retry_delay(attempt):

    delay = min(2 ** (attempt - 1), 16)

    return delay + random.uniform(0, 1)


def is_temporary_error(error):

    status_code = getattr(
        error, "status_code",
        getattr(error, "code", None)
    )

    if status_code in [408, 429, 500, 502, 503, 504]:
        return True

    error_name = type(error).__name__.lower()

    temporary_errors = [
        "timeout",
        "connection",
        "temporarily"
    ]

    return any(
        word in error_name
        for word in temporary_errors
    )

# %% Cell 10: MongoDB logging (idempotent upsert, retried)
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

            print(
                f"MongoDB error: {error}"
            )

            if attempt == 3:
                print("Unable to save the log.")
                return False

            time.sleep(retry_delay(attempt))

    return False

# %% Cell 11: main Gemini function
def ask_gemini(prompt):

    request_id = str(uuid.uuid4())

    MAX_RETRIES = 4

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

            # Step 1: Send request to Gemini

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            # Step 2: Extract AI response

            response_text = response.text or ""

            # Step 3: Extract token information

            usage = response.usage_metadata

            if usage:

                input_tokens = (
                    usage.prompt_token_count or 0
                )

                output_tokens = (
                    usage.candidates_token_count or 0
                )

                total_tokens = (
                    usage.total_token_count or 0
                )

            # Step 4: Mark request as successful

            status = "success"

        except Exception as error:

            # Python deletes `error` when the except block ends,
            # so keep a copy for the retry check below.
            last_error = error
            error_message = str(error)

            print(
                f"API attempt {attempt} failed: "
                f"{error_message}"
            )

        # Step 5: Measure latency

        latency = time.perf_counter() - start_time

        # Step 6: Calculate estimated cost

        estimated_cost = calculate_cost(
            input_tokens,
            output_tokens
        )

        # Step 7: Prepare MongoDB record

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

            "estimated_cost_usd": round(
                estimated_cost, 10
            ),

            "status": status,

            "error": error_message
        }

        # Step 8: Store the record in MongoDB

        save_log(log_record)

        # Step 9: Display the monitoring information

        print("\n========== API MONITORING ==========")

        print("Request ID:", request_id)

        print("Attempt:", attempt)

        print("Status:", status)

        print("Input Tokens:", input_tokens)

        print("Output Tokens:", output_tokens)

        print("Total Tokens:", total_tokens)

        print("Latency:", round(latency, 3), "seconds")

        print("Estimated Cost: $", estimated_cost)

        # Step 10: Return successful response

        if status == "success":

            print("\n========== GEMINI RESPONSE ==========")

            print(response_text)

            return response_text

        # Step 11: Retry only temporary failures

        if (
            attempt == MAX_RETRIES
            or not is_temporary_error(last_error)
        ):

            print("\nRequest failed permanently.")
            break

        wait_time = retry_delay(attempt)

        print(
            f"Retrying after {wait_time:.2f} seconds..."
        )

        time.sleep(wait_time)

    return None

# %% Cell 12: ask questions dynamically
while True:

    prompt = input("\nEnter your question (or type exit): ")

    if prompt.lower() == "exit":
        print("Application stopped.")
        break

    if not prompt.strip():
        print("Please enter a valid question.")
        continue

    ask_gemini(prompt)

# %% Cell 13: retrieve stored records
records = list(
    collection.find(
        {},
        {"_id": 0}
    ).sort("timestamp", -1)
)

print("Total API attempts:", len(records))

for record in records:

    print("\n--------------------------")

    print("Model:", record["model"])

    print("Input Tokens:", record["input_tokens"])

    print("Output Tokens:", record["output_tokens"])

    print("Total Tokens:", record["total_tokens"])

    print("Latency:", record["latency_seconds"])

    print("Cost:", record["estimated_cost_usd"])

    print("Status:", record["status"])

# %% Cell 14: records as a table
import pandas as pd

records = list(
    collection.find({}, {"_id": 0})
)

df = pd.DataFrame(records)

if not df.empty:

    display(df)

else:

    print("No records found.")

# %% Cell 15: aggregate totals
pipeline = [

    {
        "$group": {

            "_id": None,

            "total_api_attempts": {
                "$sum": 1
            },

            "total_input_tokens": {
                "$sum": "$input_tokens"
            },

            "total_output_tokens": {
                "$sum": "$output_tokens"
            },

            "total_tokens": {
                "$sum": "$total_tokens"
            },

            "average_latency": {
                "$avg": "$latency_seconds"
            },

            "total_estimated_cost": {
                "$sum": "$estimated_cost_usd"
            }
        }
    }
]

result = list(
    collection.aggregate(pipeline)
)

if result:

    summary = result[0]

    print("Total API Attempts:",
          summary["total_api_attempts"])

    print("Total Input Tokens:",
          summary["total_input_tokens"])

    print("Total Output Tokens:",
          summary["total_output_tokens"])

    print("Total Tokens:",
          summary["total_tokens"])

    print("Average Latency:",
          round(summary["average_latency"], 3))

    print("Total Estimated Cost: $",
          summary["total_estimated_cost"])

else:

    print("No API usage data available.")

# %% Cell 16: latency graph
import matplotlib.pyplot as plt

if not df.empty:

    plt.figure(figsize=(10, 5))

    plt.plot(
        range(1, len(df) + 1),
        df["latency_seconds"],
        marker="o"
    )

    plt.xlabel("API Attempt Number")

    plt.ylabel("Latency (Seconds)")

    plt.title("Gemini API Response Latency")

    plt.grid(True)

    plt.show()

# %% Cell 17: token consumption graph
if not df.empty:

    plt.figure(figsize=(10, 5))

    plt.bar(
        range(1, len(df) + 1),
        df["total_tokens"]
    )

    plt.xlabel("API Attempt Number")

    plt.ylabel("Total Tokens")

    plt.title("Gemini API Token Consumption")

    plt.show()

# %% Cell 18: cost graph
if not df.empty:

    plt.figure(figsize=(10, 5))

    plt.bar(
        range(1, len(df) + 1),
        df["estimated_cost_usd"]
    )

    plt.xlabel("API Attempt Number")

    plt.ylabel("Estimated Cost (USD)")

    plt.title("Gemini API Cost Per Attempt")

    plt.show()
