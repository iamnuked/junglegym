from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return '정글짐 프로젝트 시작'

if __name__ == __name__:
    app.run('0.0.0.0', port=5001, debug=True)