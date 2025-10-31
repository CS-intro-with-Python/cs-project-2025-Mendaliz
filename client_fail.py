import requests
import sys

def test_server_always_fail():
    try:
        response = requests.get('http://localhost:5000/', timeout=5)
        
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")
        
        # Этот клиент ВСЕГДА завершается с ошибкой
        print("❌ FORCED FAIL: This client always fails for testing")
        sys.exit(1)  # Всегда ошибка - выход с кодом 1
            
    except Exception as e:
        print(f"❌ FAIL: {e}")
        sys.exit(1)

if __name__ == '__main__':
    test_server_always_fail()