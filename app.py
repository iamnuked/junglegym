from flask import Flask, render_template, jsonify, request, redirect
from pymongo import MongoClient
from flask_jwt_extended import *
import os
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import timedelta, datetime
import threading
import time

load_dotenv()


# client = MongoClient('mongodb://admin:admin@10.0.134.192', 27017)
client = MongoClient(os.environ.get("MONGO_URI"), 27017)
db = client["junglegym"]
user_collection = db["USER"]
use_history_collection = db["USE_HISTORY"]
gym_data_collection = db["GYM_DATA"]


app = Flask(__name__)
# 우선 access token만 사용, 유효기간 2시간 설정 -> 추후 가능하면 refresh token 구현
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=2)
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]  # 쿠키에서 JWT를 가져와서 읽을 것임
app.config["JWT_COOKIE_HTTPONLY"] = True    # JS에서는 쿠키 접근을 막음
app.config["JWT_COOKIE_SAMESITE"] = "Lax"   # CSRF 공격(다른 사이트에서 자동으로 쿠키를 보내는 상황) 제한
jwt = JWTManager(app)

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify(success=False, message="로그인이 만료되었습니다. 재로그인이 필요합니다."), 401


@jwt.unauthorized_loader
def missing_token_callback(callback):
    return jsonify(success=False, message="로그인이 필요합니다."), 401


@jwt.invalid_token_loader
def invalid_token_callback(callback):
    return jsonify(success=False, message="유효하지 않은 토큰입니다."), 422


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/join_home")
def joinhome():
    return render_template("join.html")


@app.route("/login", methods=["POST"])
def login():
    id_receive = request.form.get("id_give")
    pw_receive = request.form.get("pw_give")

    user = user_collection.find_one({"id": id_receive})
    if not user:
        return jsonify(success=False, message="존재하지 않는 사용자입니다.")
    elif not check_password_hash(user["pw"], pw_receive):
        return jsonify(success=False, message="비밀번호가 올바르지 않습니다.")

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




# 짐 출근
@app.route("/gym_start", methods=["POST"])
@jwt_required()
def gym_start():
    current_user = get_jwt_identity()
    history = {
        "id": current_user,
        "start_datetime": datetime.now(),
        "end_datetime": "",
    }

    use_history_collection.insert_one(history)
    gym_data_collection.update_one({"datetime": "now"}, {"$inc": {"count": 1}})


# 짐 퇴근
@app.route("/gym_end", methods=["POST"])
@jwt_required()
def gym_end():
    current_user_id = get_jwt_identity()
    use_history_collection.update_one({
            "id": current_user_id, "end_datetime": ""},
            {"$set": {"end_datetime": datetime.now()}
         })
    gym_data_collection.update_one({"datetime": "now"}, {"$inc": {"count": -1}})


                 


@app.route("/delete", methods=["POST"])
@jwt_required()
def delete():
    current_user = get_jwt_identity()
    user_collection.delete_one({"id": current_user})
    return jsonify({"result": "회원 탈퇴 성공"})


# 회원 가입 수정 페이지 진입 시 필요한 데이터 전달
@app.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    current_user_id = get_jwt_identity()
    current_user = user_collection.find_one({"id": current_user_id},{"pw":0})

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

    if name_receive:
        edit_data["name"] = name_receive

    if pw_receive:
        edit_data["pw"] = generate_password_hash(pw_receive)

    if gen_receive:
        edit_data["gen"] = gen_receive

    if number_receive:
        edit_data["number_receive"] = number_receive

    if edit_data:
        result = user_collection.update_one(
            {"id": current_user_id}, {"$set": edit_data}
        )

        # 실제로 변경된 문서 순
        if result.modified_count > 0:
            return jsonify(success=True)
        else:
            # case를 나누는게 조금 애매해서 우선은 False 반환
            return jsonify(success=False)
        
@app.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    # 쿠키에 저장된 jwt 삭제
    response = redirect('/')
    unset_jwt_cookies(response)
    return response




# 혼잡도 기록 저장 관련 루프문
def save_gymdata_by_1hour():
    last_hour = datetime.now().hour
    while True:
        now = datetime.now()
        if now.hour != last_hour:
            last_hour = now.hour
            # 업데이트 코드 넣기
            now_gym_data = gym_data_collection.find_one({"datetime": "now"})
            now_gym_data[datetime] = datetime.now().strftime("%Y-%m-%d %H (%A)")
            gym_data_collection.insert_one(now_gym_data)
        time.sleep(60) #60초
threading.Thread(target=save_gymdata_by_1hour, daemon=True).start()


# 혼잡도 새로고침
def refresh_complex():
    return gym_data_collection.find_one({"datetime": "now"})



if __name__ == "__main__":
    app.run("0.0.0.0", port=os.environ.get("PORT", 5000), debug=True)
