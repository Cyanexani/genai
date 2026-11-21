import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

# Retrieve MongoDB connection string
MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise ValueError("MongoDB URI is missing!")

# Initialize MongoDB client
client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=10000
)

# Verify database connection
try:
    client.admin.command("ping")
    print("MongoDB connected successfully!")

except Exception as e:
    print("MongoDB connection failed!")
    print(type(e).__name__, e)

# Select database and collection
db = client["GenAI_Monitoring"]

collection = db["api_usage_logs"]


# Test MongoDB data insertion

