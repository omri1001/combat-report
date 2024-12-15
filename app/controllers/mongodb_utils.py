# mongodb_utils.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")  # This reads the URI from .env
# Example: "mongodb+srv://username:password@cluster0.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)
db = client["combat_database"]  # Choose a database name

# `db` is now your database object. You can import this and use `db["collection_name"]`
