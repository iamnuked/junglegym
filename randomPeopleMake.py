import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from pymongo import MongoClient
import os

# 1️⃣ USER 컬렉션 생성
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

# 2️⃣ USE_HISTORY 컬렉션 생성
use_history_list = []

historyConfigure = [1, 2, 3]
gym_data_list = []


for user in user_list:
    for month in historyConfigure:
        num_sessions = random.randint(1, random.randint(4, 10))  # 1~5회 운동 기록
        for _ in range(num_sessions):
            day = random.randint(1, 28)
            hour = random.randint(6, 20)
            minute = random.randint(0, 59)
            month == datetime.now().month
            hour == datetime.now().hour

            start = datetime(
                2026,
                month,
                day,
                hour,
                minute,
            )
            duration_minutes = random.randint(30, 90)
            end = start + timedelta(minutes=duration_minutes)
            if datetime.now().month == month:
                if user["id"] not in stack_data:
                    stack_data[user["id"]] = 1
                else:
                    stack_data[user["id"]] += 1

            if end > datetime.now():
                continue
                # gym_data_list.append({"datetime": "now", "count": random.randint(1, 28)})
                # end == 1
                # use_history_list.append(
                #     {"id": user["id"], "start_datetime": start}
                # )
            else:

                datetime(year=start.year, month=start.month, day=start.day, hour=hour)
                (end - start)
                (
                    datetime(year=2026, month=3, day=2, hour=2)
                    - datetime(year=2026, month=3, day=2, hour=1)
                ).seconds // 3600
                use_history_list.append(
                    {"id": user["id"], "start_datetime": start, "end_datetime": end}
                )

# 3️⃣ GYM_DATA 컬렉션 생성

# shuffled_user = user_list
# random.shuffle(shuffled_user)

# for hour_offset in range(30):  # 6시~21시

#     count = random.randint(1, datetime.now().day)

#     now = datetime.now()

#     duration_minutes = random.randint(2, 60)
#     start = now - timedelta(minutes=duration_minutes)
#     use_history_list.append(
#         {
#             "id": shuffled_user[hour_offset]["id"],
#             "start_datetime": start,
#         }
#     )
#     dt = "now"
#     gym_data_list.append({"datetime": datetime(), "count": count, "now": ""})
gym_data_list.append(
    {"datetime": datetime(year=2026, month=3, day=4, hour=5), "count": 12, "now": ""}
)
gym_data_list.append(
    {"datetime": datetime.now() - timedelta(seconds=300), "count": 30, "now": "now"}
)

# 출력 확인
print("USER sample:", user_list[:3])
print("USE_HISTORY sample:", use_history_list[:3])
print("GYM_DATA sample:", gym_data_list[:3])

user_collection.insert_many(user_list)
use_history_collection.insert_many(use_history_list)
gym_data_collection.insert_many(gym_data_list)
