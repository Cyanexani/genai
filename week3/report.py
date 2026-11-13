import os

import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi

load_dotenv(override=True)

MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise ValueError("MONGODB_URI is missing. Check your .env file.")

client = MongoClient(
    MONGODB_URI,
    server_api=ServerApi("1"),
    serverSelectionTimeoutMS=5000
)

collection = client["GenAI_Monitoring"]["api_usage_logs"]


records = list(
    collection.find({}, {"_id": 0}).sort("timestamp", 1)
)

df = pd.DataFrame(records)

if df.empty:
    print("No records found. Run main.py first.")
    raise SystemExit

print("Total API attempts:", len(df))

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", None)

print(df[[
    "model", "attempt", "input_tokens", "output_tokens",
    "total_tokens", "latency_seconds", "estimated_cost_usd", "status"
]].to_string(index=False))


pipeline = [
    {
        "$group": {
            "_id": None,
            "total_api_attempts": {"$sum": 1},
            "total_input_tokens": {"$sum": "$input_tokens"},
            "total_output_tokens": {"$sum": "$output_tokens"},
            "total_tokens": {"$sum": "$total_tokens"},
            "average_latency": {"$avg": "$latency_seconds"},
            "total_estimated_cost": {"$sum": "$estimated_cost_usd"}
        }
    }
]

summary = list(collection.aggregate(pipeline))[0]

print("\n========== TOTAL USAGE ==========")
print("Total API Attempts:", summary["total_api_attempts"])
print("Total Input Tokens:", summary["total_input_tokens"])
print("Total Output Tokens:", summary["total_output_tokens"])
print("Total Tokens:", summary["total_tokens"])
print("Average Latency:", round(summary["average_latency"], 3))
print("Total Estimated Cost: $", summary["total_estimated_cost"])


x = range(1, len(df) + 1)

plt.figure(figsize=(10, 5))
plt.plot(x, df["latency_seconds"], marker="o")
plt.xlabel("API Attempt Number")
plt.ylabel("Latency (Seconds)")
plt.title("Ollama API Response Latency")
plt.grid(True)
plt.savefig("latency.png")

plt.figure(figsize=(10, 5))
plt.bar(x, df["total_tokens"])
plt.xlabel("API Attempt Number")
plt.ylabel("Total Tokens")
plt.title("Ollama API Token Consumption")
plt.savefig("tokens.png")

plt.figure(figsize=(10, 5))
plt.bar(x, df["estimated_cost_usd"])
plt.xlabel("API Attempt Number")
plt.ylabel("Estimated Cost (USD)")
plt.title("Ollama API Cost Per Attempt")
plt.savefig("cost.png")

print("\nSaved latency.png, tokens.png, cost.png")
plt.show()
