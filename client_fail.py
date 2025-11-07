import requests
import sys
import os

HOST = os.environ.get('HOST', 'localhost')
PORT = int(os.environ.get('PORT', 8080))
OK, ERR, RST = "\033[32m", "\033[31m", "\033[0m"

def test_server_always_fail():
    try:
        response = requests.get(f"http://{HOST}:{PORT}/", timeout=5)
        
        print(f"{ERR}Response status code: {response.status_code}{RST}")
        print(f"{ERR}Response content: {response.text}{RST}")
        
        # Этот клиент ВСЕГДА завершается с ошибкой
        print(f"{ERR}❌ FORCED FAIL: This client always fails for testing{RST}")
        sys.exit(1)  # Всегда ошибка - выход с кодом 1
            
    except Exception as e:
        print(f"{ERR}❌ FAIL: {e}{RST}")
        sys.exit(1)

if __name__ == '__main__':
    test_server_always_fail()