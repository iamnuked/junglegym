from flask import Flask, render_template, jsonify, request, redirect
from pymongo import MongoClient
from flask_jwt_extended import *
import os
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import timedelta, datetime
import threading
import time

from flask.json.provider import JSONProvider
from bson import ObjectId
import json
import sys
from collections import defaultdict
import math

load_dotenv()

app = Flask(__name__)


#####################################################################################
# 이 부분은 코드를 건드리지 말고 그냥 두세요. 코드를 이해하지 못해도 상관없는 부분입니다.
#
# ObjectId 타입으로 되어있는 _id 필드는 Flask 의 jsonify 호출시 문제가 된다.
# 이를 처리하기 위해서 기본 JsonEncoder 가 아닌 custom encoder 를 사용한다.
# Custom encoder 는 다른 부분은 모두 기본 encoder 에 동작을 위임하고 ObjectId 타입만 직접 처리한다.
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)


class CustomJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, **kwargs, cls=CustomJSONEncoder)

    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)


# 위에 정의되 custom encoder 를 사용하게끔 설정한다.
app.json = CustomJSONProvider(app)

# 여기까지 이해 못해도 그냥 넘어갈 코드입니다.
# #####################################################################################


client = MongoClient('mongodb://admin:admin@10.0.134.192', 27017)
#client = MongoClient(os.environ.get("MONGO_URI"), 27017)
db = client["junglegym"]
user_collection = db["USER"]
use_history_collection = db["USE_HISTORY"]
# 최신순을 기준으로 주로 사용할 것이기 때문
use_history_collection.create_index([("id", 1), ("start_datetime", -1)])
gym_data_collection = db["GYM_DATA"]
rank_data_collection = db["RANK_DATA"]

# 우선 access token만 사용, 유효기간 2시간 설정 -> 추후 가능하면 refresh token 구현
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=2)
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]  # 쿠키에서 JWT를 가져와서 읽을 것임
app.config["JWT_COOKIE_HTTPONLY"] = True  # JS에서는 쿠키 접근을 막음
app.config["JWT_COOKIE_SAMESITE"] = (
    "Lax"  # CSRF 공격(다른 사이트에서 자동으로 쿠키를 보내는 상황) 제한
)
app.config["JWT_COOKIE_CSRF_PROTECT"] = False  # 운영 배포 시 True로 변경
jwt = JWTManager(app)


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return (
        jsonify(
            success=False, message="로그인이 만료되었습니다. 재로그인이 필요합니다."
        ),
        401,
    )


@jwt.unauthorized_loader
def missing_token_callback(callback):
    return jsonify(success=False, message="로그인이 필요합니다."), 401


@jwt.invalid_token_loader
def invalid_token_callback(callback):
    return jsonify(success=False, message="유효하지 않은 토큰입니다."), 422


@app.route("/")
def home():
    user = None
    # 페이지네이션 필요한 데이터
    # 현재 페이지, 전체 데이터 개수, 전체 페이지 수
    history = []

    page = int(request.args.get("page", 1))
    per_page = 5
    total_pages = 0
    has_next = False

    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()

        user_data = user_collection.find_one({"id": user_id})

        if user_data:
            user = {"id": user_data["id"], "name": user_data["name"]}

            # 운동 기록 처음에 띄울 5개 데이터
            total_count = use_history_collection.count_documents({"id": user_id})

            total_pages = math.ceil(total_count / per_page)

            has_next = page < total_pages

            skip_count = (page - 1) * per_page

            history = list(
                use_history_collection.find({"id": user_id})
                .sort("start_datetime", -1)
                .skip(skip_count)
                .limit(per_page)
            )
    except:
        user = None
        history = []
    print(history)
    return render_template(
        "home.html",
        user=user,
        history=history,
        page=page,
        total_pages=total_pages,
        has_next=has_next,
    )


@app.route("/join_home")
def joinhome():
    return render_template("join.html")


@app.route("/dev/home")
def go_dev_home():
    return render_template("home3.html")


@app.route("/edit")
@jwt_required()
def go_edit():
    user = None
    user_id = get_jwt_identity()

    user_data = user_collection.find_one({"id": user_id})

    if not user_data:
        # 에러 페이지 등으로 안내 필요함. 우선 /로 redirect
        return redirect("/")

    user = {
        "id": user_data["id"],
        "name": user_data["name"],
        "gen": user_data.get("gen"),
        "number": user_data.get("number"),
    }

    return render_template("edit.html", user=user)


@app.route("/login", methods=["POST"])
def login():
    id_receive = request.form.get("id_give")
    pw_receive = request.form.get("pw_give")

    user = user_collection.find_one({"id": id_receive})
    if not user:
        return jsonify({"result": "해당 아이디가 존재하지 않습니다"})
    elif not check_password_hash(user["pw"], pw_receive):
        return jsonify({"result": "비밀번호가 틀립니다."})

    access_token = create_access_token(identity=id_receive)

    # 로그인 성공 시
    # 1. 로그인 ui 사라지고 텍스트 나타남 (이름)
    # 2. 출근 버튼 나타남
    # 3. 로그아웃 버튼 나타남
    response = jsonify(success=True, name=user["name"])
    # jwt 쿠키에 저장
    set_access_cookies(response, access_token)
    return response


@app.route("/join", methods=["POST"])
def join():
    name_receive = request.form["name_give"].strip()
    id_receive = request.form["id_give"].strip()
    pw_receive = request.form["pw_give"].strip()
    gen_receive = request.form["gen_give"].strip()
    number_receive = request.form["number_give"].strip()

    user = {
        "name": name_receive,
        "id": id_receive,
        "pw": pw_receive,
        "gen": gen_receive,
        "number": number_receive,
    }

    # 빈 항목 검사
    if check_empty(user):
        return jsonify({"result": "빈 항목이 있습니다"})

    # 이름 길이 검사
    if check_name_len(name_receive):
        return jsonify({"result": "잘못된 이름입니다"})

    # 아이디 길이 검사
    if check_id_len(id_receive):
        return jsonify({"result": "잘못된 아이디입니다"})

    # 비밀번호 길이 검사
    if check_pw_len(pw_receive):
        return jsonify({"result": "잘못된 비밀번호입니다"})

    # 기수 검사
    if check_gen(gen_receive):
        return jsonify({"result": "잘못된 기수번호 입니다"})

    # 번호 검사
    if check_number(number_receive):
        return jsonify({"result": "잘못된 번호입니다."})

    # 중복 아이디 검사
    if user_collection.count_documents({"id": id_receive}) > 0:
        return jsonify({"result": "중복 아이디입니다."})

    user["pw"] = generate_password_hash(pw_receive)

    user_collection.insert_one(user)
    return jsonify({"result": "회원가입 성공"})


# 무결성 검사 함수들
def check_empty(user):
    for key, value in user.items():
        if not value:
            return True
    return False


def check_name_len(name_receive):
    return len(name_receive) > 10 or len(name_receive) < 2


def check_id_len(id_receive):
    return len(id_receive) > 20 or len(id_receive) < 4


def check_pw_len(pw_receive):
    return len(pw_receive) > 20 or len(pw_receive) < 4


def check_gen(gen_receive):
    return gen_receive != "12기" and gen_receive != "13기"


def check_number(number_receive):
    return int(number_receive) < 1 or int(number_receive) > 200


def init_complex_count():
    gym_data_collection.insert_one(
        {"now": "now", "datetime": datetime.now(), "count": 0}
    )


# 짐 출근
@app.route("/gym_start", methods=["POST"])
@jwt_required()
def gym_start():
    current_user = get_jwt_identity()
    history = {
        "id": current_user,
        "start_datetime": datetime.now(),
        "end_datetime": None,
    }

    use_history_collection.insert_one(history)
    gym_data_collection.update_one({"now": "now"}, {"$inc": {"count": 1}})
    return {"result": "success"}


# 짐 퇴근
@app.route("/gym_end", methods=["POST"])
@jwt_required()
def gym_end():
    current_user_id = get_jwt_identity()
    active_history = use_history_collection.find_one(
        {"id": current_user_id, "end_datetime": None}, sort=[("start_datetime", -1)]
    )
    if active_history:
        use_history_collection.update_one(
            {"_id": active_history["_id"]},
            {"$set": {"end_datetime": datetime.now()}},
        )
        gym_data_collection.update_one({"datetime": "now"}, {"$inc": {"count": -1}})
        return {"result": "success"}
    else:
        return {"result": "no_active_data"}


@app.route("/delete", methods=["POST"])
@jwt_required()
def delete():
    current_user = get_jwt_identity()
    user_collection.delete_one({"id": current_user})
    response = jsonify({"result": "회원 탈퇴 성공"})
    unset_jwt_cookies(response)   # JWT 쿠키 삭제
    return response


# 회원 가입 수정 페이지 진입 시 필요한 데이터 전달
@app.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    current_user_id = get_jwt_identity()
    current_user = user_collection.find_one({"id": current_user_id}, {"pw": 0})

    return jsonify(current_user)


@app.route("/profile-edit", methods=["POST"])
@jwt_required()
def edit():
    current_user_id = get_jwt_identity()

    # 수정 가능한 데이터 : 이름, 비밀번호, 기수, 번호
    name_receive = request.form.get("name_give")
    pw_receive = request.form.get("pw_give")
    gen_receive = request.form.get("gen_give")
    number_receive = request.form.get("number_give")

    user = user_collection.find_one({"id": current_user_id})

    if not user:
        return jsonify(success=False, message="사용자를 찾을 수 없음")

    edit_data = {}

    if name_receive != user["name"]:
        edit_data["name"] = name_receive

    if pw_receive:
        edit_data["pw"] = generate_password_hash(pw_receive)

    if gen_receive != user["gen"]:
        edit_data["gen"] = gen_receive

    if number_receive != user["number"]:
        edit_data["number"] = number_receive

    if edit_data:
        user_collection.update_one({"id": current_user_id}, {"$set": edit_data})
        return redirect("/")


@app.route("/logout", methods=["POST"])
def logout():
    # 쿠키에 저장된 jwt 삭제
    response = jsonify(success=True)
    unset_jwt_cookies(response)  # 브라우저에 저장된 jwt 쿠키 삭제
    return response


# 혼잡도 기록 저장 관련 루프문
def save_gymdata_by_1hour():
    last_hour = datetime.now().hour
    while True:
        now = datetime.now()
        if now.hour != last_hour:
            last_hour = now.hour
            now_gym_count = gym_data_collection.find_one({"now": "now"})
            gym_data_collection.update_one({"$set": ""}, {"now": "now"})
            gym_data_collection.insert_one(
                {
                    "now": "now",
                    "datetime": datetime.now(),
                    "count": now_gym_count["count"],
                }
            )
        time.sleep(60)  # 60초


threading.Thread(target=save_gymdata_by_1hour, daemon=True).start()


##############################################
# 기록 관련
#
# 시간 형식 %Y-%m-%d %H    예시 -> 2026-03-05 15 -> 롤백 그냥 datetime 사용
#
# 1. 전체 기록 클라이언트로 전송
# 2. 기간 선택해서 클라이언트로 전송


# 해당 유저 전체 기록 전송 - 페이지네이션
# id, start_datetime, end_datetime
@app.route("/get_history", methods=["GET"])
@jwt_required()
def get_history():
    current_user = get_jwt_identity()
    # user_history = use_history_collection.find({"id": current_user})
    # return jsonify(user_history)
    page = int(request.args.get("page", 1))
    per_page = 5

    total_count = use_history_collection.count_documents({"id": current_user})

    total_pages = max(1, math.ceil(total_count / per_page))

    skip_count = (page - 1) * per_page

    history = list(
        use_history_collection.find({"id": current_user})
        .sort([("start_datetime", -1), ("_id", -1)])
        .skip(skip_count)
        .limit(per_page)
    )

    return jsonify({"history": history, "page": page, "total_pages": total_pages})


# 3월 2일 월요일
# 주간 기록 작성중
# day값에서  ( 0, 1, 2 ~ 6 ) 는 ( 월, 화, 수 ~ 일 ) 을 의미함
# new_data값은 주, 요일, 운동 시간이 들어감
@app.route("/get_week_history", methods=["GET"])
@jwt_required()
def get_week_history():
    current_user = get_jwt_identity()
    start_jungle_date = datetime(2026, 3, 2)
    # user_history_list = list(use_history_collection.find({"id": current_user}))
    user_history_list = list(
    use_history_collection.find({
        "id": current_user,
        "end_datetime": {"$ne": None}
    })
)
    new_data = []
    for target in user_history_list:
        diff = (target["end_datetime"] - start_jungle_date).days
        week = diff // 7 + 1
        day = diff % 7 # 요일

        use_time = (target["end_datetime"] - target["start_datetime"]).total_seconds() / 60

        new_data.append({
            "week": week,
            "day": day,
            "time": use_time
        })
    return jsonify(new_data)


@app.route("/get_month_history", methods=["GET"])
@jwt_required()
def get_month_history():  # 나의 기록
    current_user = get_jwt_identity()
    # user_history_list = list(use_history_collection.find({"id": current_user}))
    user_history_list = list(
    use_history_collection.find({
        "id": current_user,
        "end_datetime": {"$ne": None}
    })
)

    sum_time = defaultdict(int)

    for doc in user_history_list:
        month = doc["end_datetime"].month
        start = doc["start_datetime"]
        end = doc["end_datetime"]

        use_time = (end - start).total_seconds() / 60
        sum_time[month] += use_time

    new_data = []

    for month, time in sum_time.items():
        new_data.append({"month": month, "time": time})

    return jsonify(new_data)


# 혼잡도 데이터 전송 관련


@app.route("/get_now_complex", methods=["GET"])  # 현재 시간대 사람수
def get_now_complex():
    now_complex_data = gym_data_collection.find({"now": "now"})

    return jsonify(list(now_complex_data))


@app.route("/get_today_complex", methods=["GET"])  # 하루 전체 사람수
def get_today_complex():
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    today_complex_data = gym_data_collection.find(
        {"datetime": {"$gte": start, "$lt": end}}
    )
    return jsonify(list(today_complex_data))


######################
# 랭킹 관련

# def calc_by_month():
#     use_history_collection.aggregate({

#     })


# 전체 기록 하루 중복 제거
def total_use_days_data():
    total_use_days_data = list(
        db.USE_HISTORY.aggregate(
            [
                {
                    "$group": {
                        "_id": {
                            "id": "$id",
                            "date": {
                                "$dateToString": {
                                    "format": "%Y-%m-%d",
                                    "date": "$start_datetime",
                                }
                            },
                        },
                        "doc": {"$first": "$$ROOT"},
                    }
                },
                {"$replaceRoot": {"newRoot": "$doc"}},
            ]
        )
    )
    return total_use_days_data


# 달별 유저 헬스 이용 데이터 (같은날 중복 제거)
def month_use_days_data(month):
    data = total_use_days_data()
    result = []
    for doc in data:
        if doc["start_datetime"].month == month:
            result.append(doc)

    return result


# 이번 달 전체 랭킹 반환
@app.route("/rank_month/<int:month>", methods=["GET"])
def get_month_rank(month):
    data = month_use_days_data(month)
    user_count = defaultdict(int)

    # 유저별 출석일수 계산
    for doc in data:
        user_id = doc["id"]
        user_count[user_id] += 1

    # 출석일수 기준 정렬
    sorted_users = sorted(user_count.items(), key=lambda x: x[1], reverse=True)

    result = []

    # 랭킹 생성
    for rank, (user_id, count) in enumerate(sorted_users, start=1):
        target = user_collection.find_one({"id": user_id})
        result.append({"rank": rank, "name": target["name"], "days": count})

    return jsonify(result)

@app.route("/check_started", methods=["GET"])
@jwt_required()
def check_started():
    current_user = get_jwt_identity()
    if use_history_collection.find_one({"id": current_user, "end_datetime": None}):
        return "이미출근"
    else:
        return "미출근"



##############################################


# 혼잡도 새로고침
def refresh_complex():
    return gym_data_collection.find_one({"now": "now"})


if __name__ == "__main__":
    app.run("0.0.0.0", port=os.environ.get("PORT", 5000), debug=True)
