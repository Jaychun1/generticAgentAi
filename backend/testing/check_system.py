# File: check_system.py
import time
import requests

def check_backend():
    try:
        start = time.time()
        response = requests.get("http://localhost:8000/health", timeout=5)
        end = time.time()
        print(f"✅ Backend response: {response.status_code} in {end-start:.2f}s")
        return True
    except Exception as e:
        print(f"Backend error: {e}")
        return False

def check_ollama():
    try:
        start = time.time()
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        end = time.time()
        print(f"✅ Ollama response in {end-start:.2f}s")
        return True
    except Exception as e:
        print(f"Ollama error: {e}")
        return False

if __name__ == "__main__":
    print("🕐 Checking system...")
    check_backend()
    check_ollama()