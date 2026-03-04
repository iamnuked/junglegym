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


if __name__ == __name__:
    app.run('0.0.0.0', port=5001, debug=True)