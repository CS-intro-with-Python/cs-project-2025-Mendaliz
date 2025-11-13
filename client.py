import requests
import sys

OK, ERR, RST = "\033[32m", "\033[31m", "\033[0m"

def test_server():
    port = 8080
    host = 'localhost'
    
    try:
        response = requests.get(f"http://{host}:{port}/", timeout=5)
        
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")
        
        if response.status_code == 200:
            print(f"{OK}✅ SUCCESS: Server returned 200 OK (port {port}){RST}")
            sys.exit(0)
        else:
            print(f"{ERR}❌ FAIL: Expected status 200, got {response.status_code}{RST}")
            sys.exit(1)
            
    except requests.exceptions.ConnectionError:
        print(f"{ERR}❌ FAIL: Cannot connect to server at {host}:{port}{RST}")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"{ERR}❌ FAIL: Request timeout{RST}")
        sys.exit(1)
    except Exception as e:
        print(f"{ERR}❌ FAIL: Unexpected error: {e}{RST}")
        sys.exit(1)

if __name__ == '__main__':
    test_server()