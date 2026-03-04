from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient
from flask_jwt_extended import *
import os
from dotenv import load_dotenv
from werkzeug.security import check_password_hash


load_dotenv()



# client = MongoClient('mongodb://admin:admin@10.0.134.192', 27017)
client = MongoClient(os.environ.get("MONGO_URI"), 27017)
db = client['junglegym']
user_collection = db['user']




app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")


@app.route('/')
def home():
    return render_template('index.html')

@app.route("/login", methods=["POST"])
def login():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']
    access_token = create_access_token(identity=id_receive)

    # 로그인 정보 맞으면  return {"access_token": access_token}

    # 로그인

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



if __name__ == '__main__':
    app.run('0.0.0.0', port=os.environ.get("PORT"), debug=True)
