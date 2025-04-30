import os
import logging
import asyncio
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
YANDEX_GPT_TOKEN = os.getenv("YANDEX_GPT_TOKEN")
YANDEX_GPT_FOLDER_ID = os.getenv("YANDEX_GPT_FOLDER_ID")

async def test_yandex_gpt():
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
    
    logger.info("Testing YandexGPT API connection...")
    logger.info(f"Using token: {YANDEX_GPT_TOKEN}")
    logger.info(f"Using folder ID: {YANDEX_GPT_FOLDER_ID}")
    logger.info(f"Request data: {data}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                logger.info(f"Response status: {response.status}")
                response_text = await response.text()
                logger.info(f"Response body: {response_text}")
                
                if response.status == 200:
                    result = await response.json()
                    logger.info("Test successful!")
                    return True, result
                else:
                    logger.error(f"Test failed with status {response.status}")
                    return False, response_text
    except Exception as e:
        logger.error(f"Error during test: {str(e)}", exc_info=True)
        return False, str(e)

async def main():
    success, result = await test_yandex_gpt()
    if success:
        logger.info("YandexGPT API test passed!")
        logger.info(f"Response: {result}")
    else:
        logger.error("YandexGPT API test failed!")
        logger.error(f"Error: {result}")

if __name__ == "__main__":
    asyncio.run(main())