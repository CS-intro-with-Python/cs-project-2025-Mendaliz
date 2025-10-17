import requests

def make_request_hello(port=8080):
    response = requests.get(f"http://127.0.0.1:{port}/hello")
    print(response)
    print(response.json())

def make_response_user(port=8080, name="Tehia"):
    response = requests.get(f"http://127.0.0.1:{port}/user/{name}")
    print(response)
    print(response.json())

def make_response_search(port=8080, query="Hoot"):
    response = requests.get(f"http://127.0.0.1:{port}/search?q={query}")
    print(response)
    print(response.json())

if __name__ == '__main__':
    port = 8080
    make_request_hello(port)
    make_response_user(port)
    make_response_search(port)
