import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_simple_chat():
    """Test chat với các câu đơn giản"""
    print("🤖 Testing simple chat queries...\n")
    
    test_cases = [
        ("hi", "Simple greeting"),
        ("hello", "Greeting"),
        ("how are you?", "Casual question"),
        ("what can you do?", "Capabilities question"),
        ("thanks", "Thank you"),
        ("bye", "Goodbye")
    ]
    
    for query, description in test_cases:
        print(f"📝 Testing: {description}")
        print(f"   Query: '{query}'")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/chat/",
                json={"message": query, "stream": False},
                timeout=10  # Timeout ngắn
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"Success in {elapsed:.2f}s")
                print(f"Agent: {data.get('agent_used', 'unknown')}")
                print(f"Response: {data.get('response', '')[:100]}...")
            else:
                print(f"Failed ({response.status_code}) in {elapsed:.2f}s")
                print(f"Error: {response.text[:100]}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout after {time.time() - start_time:.2f}s")
        except Exception as e:
            print(f"   Exception: {str(e)}")
        
        print("-" * 50)

def test_complex_chat():
    """Test chat với câu phức tạp"""
    print("\n💰 Testing complex chat queries...\n")
    
    test_cases = [
        ("What was Amazon revenue 2023?", "Financial query"),
        ("Who are the top employees?", "SQL query"),
        ("Latest AI news", "Web query")
    ]
    
    for query, description in test_cases:
        print(f"📝 Testing: {description}")
        print(f"   Query: '{query}'")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/chat/",
                json={"message": query, "stream": False},
                timeout=30  # Timeout dài hơn cho complex queries
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"Success in {elapsed:.2f}s")
                print(f"Agent: {data.get('agent_used', 'unknown')}")
                print(f"Response length: {len(data.get('response', ''))} chars")
                if data.get('response'):
                    print(f"   Preview: {data.get('response', '')[:150]}...")
            else:
                print(f"Failed ({response.status_code}) in {elapsed:.2f}s")
                print(f"Error: {response.text[:100]}")
                
        except requests.exceptions.Timeout:
            print(f"Timeout after {time.time() - start_time:.2f}s")
        except Exception as e:
            print(f"Exception: {str(e)}")
        
        print("-" * 50)

if __name__ == "__main__":
    print("🚀 Starting Agent AI Chat Tests")
    print(f"📡 Base URL: {BASE_URL}")
    print("=" * 60)
    
    # Test simple queries first
    test_simple_chat()
    
    # Test complex queries
    test_complex_chat()
    
    print("\n🎉 Tests completed!")