import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
YANDEX_GPT_TOKEN = os.getenv("YANDEX_GPT_TOKEN")
YANDEX_GPT_FOLDER_ID = os.getenv("YANDEX_GPT_FOLDER_ID")

def test_yandex_gpt():
    """Test the connection to YandexGPT API"""
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Authorization": f"Api-Key {YANDEX_GPT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    test_question = "What is 2+2?"
    data = {
        "modelUri": f"gpt://{YANDEX_GPT_FOLDER_ID}/yandexgpt",
        "completionOptions": {
            "temperature": 0.7,
            "maxTokens": 2000
        },
        "messages": [
            {
                "role": "user",
                "text": test_question
            }
        ]
    }
    
    print("Testing YandexGPT API connection...")
    print(f"Using token: {YANDEX_GPT_TOKEN}")
    print(f"Using folder ID: {YANDEX_GPT_FOLDER_ID}")
    print(f"Request data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"\nResponse status: {response.status_code}")
        print(f"Response body: {json.dumps(response.json(), indent=2) if response.status_code == 200 else response.text}")
        
        if response.status_code == 200:
            print("\nTest successful!")
            return True, response.json()
        else:
            print("\nTest failed!")
            return False, response.text
    except Exception as e:
        print(f"\nError during test: {str(e)}")
        return False, str(e)

if __name__ == "__main__":
    success, result = test_yandex_gpt()
    if success:
        print("\nYandexGPT API test passed!")
        print(f"Response: {json.dumps(result, indent=2)}")
    else:
        print("\nYandexGPT API test failed!")
        print(f"Error: {result}") 