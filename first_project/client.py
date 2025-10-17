import requests
import json

def make_request(port=8080):
    response = requests.get(f"http://127.0.0.1:{port}/hello")
    print(response)
    print(response.json())

if __name__ == '__main__':
    make_request(port=8080)