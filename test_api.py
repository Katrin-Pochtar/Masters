import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
YANDEX_GPT_TOKEN = os.getenv('YANDEX_GPT_TOKEN')
YANDEX_GPT_FOLDER_ID = os.getenv('YANDEX_GPT_FOLDER_ID')

url = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completion'
headers = {
    'Authorization': f'Api-Key {YANDEX_GPT_TOKEN}',
    'Content-Type': 'application/json'
}

data = {
    'modelUri': f'gpt://{YANDEX_GPT_FOLDER_ID}/yandexgpt',
    'completionOptions': {
        'temperature': 0.7,
        'maxTokens': 2000
    },
    'messages': [
        {
            'role': 'user',
            'text': 'What is 2+2?'
        }
    ]
}

try:
    response = requests.post(url, headers=headers, json=data)
    print(f'Status code: {response.status_code}')
    print(f'Response: {response.text}')
except Exception as e:
    print(f'Error: {str(e)}') 