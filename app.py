from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient
from flask_jwt_extended import *
import os
from dotenv import load_dotenv
from werkzeug.security import check_password_hash
from datetime import timedelta

load_dotenv()



# client = MongoClient('mongodb://admin:admin@10.0.134.192', 27017)
client = MongoClient(os.environ.get("MONGO_URI"), 27017)
db = client['junglegym']
user_collection = db['user']




app = Flask(__name__)
# 우선 access token만 사용, 유효기간 2시간 설정 -> 추후 가능하면 refresh token 구현
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=2)
jwt = JWTManager(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    id_receive = request.form.get('id_give')
    password_receive = request.form.get('password_give')
    access_token = create_access_token(identity=id_receive)

    user = user_collection.find_one({"id": id_receive})

    if not user:
        return jsonify(success=False, message="존재하지 않는 사용자입니다.")
    elif not check_password_hash(user["password"], password_receive):
        return jsonify(success=False, message="비밀번호가 올바르지 않습니다.")
    
    access_token = create_access_token(identity=id_receive)
    
    # 로그인 성공 시
    # 1. 로그인 ui 사라지고 텍스트 나타남 (이름)
    # 2. 출근 버튼 나타남
    # 3. 로그아웃 버튼 나타남
    return jsonify(
        success = True,
        access_token=access_token,
        name=user["name"]
    )

@app.route("/join", methods=["POST"])
def join():
    id_receive = request.form["id_give"]
    pw_receive = request.form["pw_give"]
    name_receive = request.form["name_give"]
    gen_receive = request.form["gen_give"]
    number_receive = request.form["number_give"]

    # 중복 아이디 검사 조작 검사용
    if db.USER.count_documents({"id": id_receive}) > 0:
        return jsonify({'result': '중복된 아이디입니다.'})
    
    user = {'id': id_receive, 'pw': pw_receive, 'name': name_receive, 'gen': gen_receive, 'number_receive': number_receive}
    db.USER.insert_one(user)
    return jsonify({'result':'회원가입 성공'})


@app.route("/delete", methods=["POST"])
@jwt_required()
def delete():
    current_user = get_jwt_identity()
    db.USER.delete_one({"id": current_user})
    return jsonify({'result':'회원 탈퇴 성공'})

# 회원 가입 수정 페이지 진입 시 필요한 데이터 전달
@app.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    current_user_id = get_jwt_identity()
    current_user = user_collection.find_one({"id":current_user_id})

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
        edit_data["pw"] = pw_receive

    if gen_receive:
        edit_data["gen"] = gen_receive

    if number_receive:
        edit_data["number"] = number_receive

    if edit_data:
        result = user_collection.update_one(
            {"id": current_user_id},
            {"$set": edit_data}
        )

        # 실제로 변경된 문서 순
        if result.modified_count > 0:
            return jsonify(success=True)
        else:
            # case를 나누는게 조금 애매해서 우선은 False 반환
            return jsonify(success=False)

if __name__ == '__main__':
    app.run('0.0.0.0', port=os.environ.get("PORT"), debug=True)
