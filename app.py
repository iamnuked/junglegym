from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient
from flask_jwt_extended import *
import os
from dotenv import load_dotenv


load_dotenv()



# client = MongoClient('mongodb://admin:admin@10.0.134.192', 27017)
client = MongoClient(os.environ.get("MONGO_URI"), 27017)
db = client.junglegym




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


@app.route("/join", methods=["POST"])
def join():
    id_receive = request.form["id_give"]
    pw_receive = request.form["pw_give"]
    name_receive = request.form["pw_give"]
    gen_receive = request.form["pw_give"]
    number_receive = request.form["pw_give"]

    # 중복 아이디 검사 조작 검사용
    if db.USER.count_documents({"id": id_receive}) > 0:
        return jsonify({'result': '중복된 아이디입니다.'})
    
    user = {'id': id_receive, 'pw': pw_receive, 'name': name_receive, 'gen': gen_receive, 'number_receive': number_receive}
    db.USER.insert_one(user)
    return jsonify({'result':'회원가입 성공'})



if __name__ == __name__:
    app.run('0.0.0.0', port=5001, debug=True)