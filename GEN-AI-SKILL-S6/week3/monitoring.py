import time
from datetime import datetime, timezone

from database import collection


# Function to calculate latency
def calculate_latency(start_time, end_time):
    return round((end_time - start_time) * 1000, 2)


# Function to estimate token count
def calculate_tokens(text):
    return len(text.split())


# Function to store API usage logs
def log_api_usage(
    model,
    prompt,
    response,
    input_tokens,
    output_tokens,
    latency,
    status
):

    total_tokens = input_tokens + output_tokens

    log = {
        "model": model,
        "prompt": prompt,
        "response": response,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "latency_ms": latency,
        "status": status,
        "timestamp": datetime.now(timezone.utc)
    }

    result = collection.insert_one(log)

    print("API usage logged successfully!")
    print("Document ID:", result.inserted_id)


    # Testing monitoring functions

prompt = "What is Artificial Intelligence?"
response = "AI is the simulation of human intelligence by machines."

start_time = time.time()

# Simulate processing
time.sleep(2)

end_time = time.time()

# Calculate metrics
input_tokens = calculate_tokens(prompt)
output_tokens = calculate_tokens(response)

latency = calculate_latency(start_time, end_time)

# Store monitoring data
log_api_usage(
    model="gemini",
    prompt=prompt,
    response=response,
    input_tokens=input_tokens,
    output_tokens=output_tokens,
    latency=latency,
    status="success"
)

print("Latency:", latency, "ms")
print("Input Tokens:", input_tokens)
print("Output Tokens:", output_tokens)



# Function to calculate API cost

def calculate_cost(
    input_tokens,
    output_tokens,
    input_price_per_million,
    output_price_per_million
):

    input_cost = (
        input_tokens / 1_000_000
    ) * input_price_per_million

    output_cost = (
        output_tokens / 1_000_000
    ) * output_price_per_million

    total_cost = input_cost + output_cost

    return round(total_cost, 8)


# Test cost calculation

cost = calculate_cost(
    input_tokens=1000,
    output_tokens=2000,
    input_price_per_million=0.10,
    output_price_per_million=0.40
)

print("\n========== API COST ==========")
print("Estimated API Cost: $", cost)