import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from pymongo import MongoClient
import os

# USER 생성
user_list = []
used_number_receive = set()

client = MongoClient(os.environ.get("MONGO_URI"), 27017)
db = client["junglegym"]
user_collection = db["USER"]
use_history_collection = db["USE_HISTORY"]
gym_data_collection = db["GYM_DATA"]
rank_data_collection = db["RANK_DATA"]

db["USE_HISTORY"].delete_many({})
db["GYM_DATA"].delete_many({})
db["USER"].delete_many({})
setting_stack = 20
now_stack = 0
stack_data = {}
gym_using_record = {}

for i in range(1, 101):
    user_id = f"user{i:03d}"  # user001 ~ user100

    # 3글자 한글 이름 랜덤 생성 (간단히 예시)
    last_names = ["김", "이", "박", "최", "정", "강", "조"]
    first_names = ["철수", "영희", "민수", "지우", "수현", "예린", "현우"]
    name = random.choice(last_names) + random.choice(first_names)

    # gen 1~99, 중복 제거
    gen = random.choice([x for x in range(12, 14)])

    # number_receive 1~99, 중복 제거
    number_receive = random.choice(
        [x for x in range(1, 101) if x not in used_number_receive]
    )
    used_number_receive.add(number_receive)

    user = {
        "id": user_id,
        "pw": generate_password_hash(f"password{i}"),
        "name": name,
        "gen": gen,
        "number_receive": number_receive,
    }
    user_list.append(user)

# USE_HISTORY 생성
use_history_list = []

historyConfigure = [1, 2, 3]
gym_data_list = []
location_setting = set()
now = datetime.now()
# 거점 만들기
for i in range(100):
    day = random.randint(1, 28)
    hour = random.randint(6, 20)
    minute = random.randint(0, 59)
    month = historyConfigure[random.randint(0, len(historyConfigure) - 1)]
    start = datetime(
        2026,
        month,
        day,
        hour,
        minute,
    )
    if now < start:
        continue
    location_setting.add(start)
location_setting.add(now)
location_setting = sorted(list(location_setting))


# GYM_DATA 생성
now_count = 30
shuffled_user = user_list
for gym_datetime in location_setting:  # 6시~21시
    random.shuffle(shuffled_user)

    count = random.randint(6, 35)

    # start = now - timedelta(minutes=duration_minutes)
    if gym_datetime == now:
        gym_data_list.append({"datetime": gym_datetime, "count": count, "now": "now"})
        for i in range(count):
            duration_minutes = random.randint(20, 40)
            minus_duration = random.randint(0, duration_minutes - 1)
            use_history_list.append(
                {
                    "id": shuffled_user[i]["id"],
                    "start_datetime": gym_datetime - timedelta(minutes=minus_duration),
                    "end_datetime": "",
                }
            )

    else:
        gym_data_list.append({"datetime": gym_datetime, "count": count, "now": ""})
        for i in range(count):
            duration_minutes = random.randint(20, 40)
            minus_duration = random.randint(0, duration_minutes - 1)
            use_history_list.append(
                {
                    "id": shuffled_user[i]["id"],
                    "start_datetime": gym_datetime - timedelta(minutes=minus_duration),
                    "end_datetime": gym_datetime
                    + timedelta(minutes=duration_minutes)
                    - timedelta(minutes=minus_duration),
                }
            )


# 출력 확인
print("USER sample:", user_list[:3])
print("USE_HISTORY sample:", use_history_list[:3])
print("GYM_DATA sample:", gym_data_list[:3])

user_collection.insert_many(user_list)
use_history_collection.insert_many(use_history_list)
gym_data_collection.insert_many(gym_data_list)
