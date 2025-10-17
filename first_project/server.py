from flask import Flask, jsonify

data = {"message": "Hello, world!"}

app = Flask(__name__)

@app.route('/hello', methods=['GET'])
def hello():
    return jsonify(data)

if __name__ == '__main__':
    app.run(port=8080)