from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# client = MongoClient('mongodb://admin:admin@10.0.134.192', 27017)
client = MongoClient(os.environ.get("MONGO_URI"), 27017)
db = client["junglegym"]
gym_data_collection = db["GYM_DATA"]

def init_complex_count():
    if gym_data_collection.find_one({"now": "now"}):
        gym_data_collection.update_one({"now": "now"}, {"$set": 0})
    else:
        gym_data_collection.insert_one({"now": "now", "datetime": datetime.now(),"count": 0})

init_complex_count()


client.close()
