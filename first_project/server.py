from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/hello', methods=['GET'])
def hello():
    return jsonify({"message": "Hello, world!"})

@app.route('/user/<username>', methods=['GET'])
def greeting_user(username):
    return jsonify({"message": f"Hello, {username}!"})

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    return jsonify({"query": f"{query}", "length": f"{len(query)}"})

if __name__ == '__main__':
    app.run(port=8080)