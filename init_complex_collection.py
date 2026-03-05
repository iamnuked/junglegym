from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# client = MongoClient('mongodb://admin:admin@10.0.134.192', 27017)
client = MongoClient(os.environ.get("MONGO_URI"), 27017)
db = client["junglegym"]
user_collection = db["USER"]
use_history_collection = db["USE_HISTORY"]
gym_data_collection = db["GYM_DATA"]
rank_data_collection = db["RANK_DATA"]

def init_complex_count():
    if gym_data_collection.find_one({"datetime": "now"}) > 0:
        gym_data_collection.update_one({"datetime": "now"}, {"$set": 0})
    else:
        gym_data_collection.insert_one({"datetime": "now", "count": 0})

init_complex_count()


client.close()
