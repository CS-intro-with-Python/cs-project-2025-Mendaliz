import requests
import sys

def test_server():
    try:
        response = requests.get('http://localhost:5000/', timeout=5)
        
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Server returned 200 OK")
            sys.exit(0)  # Успех - выход с кодом 0
        else:
            print(f"❌ FAIL: Expected status 200, got {response.status_code}")
            sys.exit(1)  # Ошибка - выход с кодом 1
            
    except requests.exceptions.ConnectionError:
        print("❌ FAIL: Cannot connect to server")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("❌ FAIL: Request timeout")
        sys.exit(1)
    except Exception as e:
        print(f"❌ FAIL: Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    test_server()