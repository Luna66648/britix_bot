import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from yandex_cloud_ml_sdk import YCloudML
from yandex_cloud_ml_sdk.search_indexes import StaticIndexChunkingStrategy, TextSearchIndexType

load_dotenv()

# Берем ключи из файла .env
FOLDER_ID = os.getenv("YA_FOLDER_ID")
API_KEY = os.getenv("YA_API_KEY")

if not FOLDER_ID or not API_KEY:
    print("ОШИБКА: Проверьте файл .env (YA_FOLDER_ID и YA_API_KEY)")
    exit()

sdk = YCloudML(folder_id=FOLDER_ID, auth=API_KEY)

URLS = [
    "https://apidocs.bitrix24.ru/api-reference/crm/deals/index.html",
    "https://apidocs.bitrix24.ru/api-reference/crm/contacts/crm-contact-add.html",
    "https://apidocs.bitrix24.ru/api-reference/crm/leads/crm-lead-add.html",
    "https://apidocs.bitrix24.ru/api-reference/crm/companies/crm-company-add.html"
]

def parse_and_save():
    print("Начинаем парсинг документации...")
    for i, url in enumerate(URLS):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            
            filename = f"doc_{i}.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"URL: {url}\n\n{text}")
            print(f"Сохранено: {filename}")
        except Exception as e:
            print(f"Ошибка при парсинге {url}: {e}")

def create_assistant():
    print("Загрузка файлов в Yandex Cloud...")
    files = []
    for i in range(len(URLS)):
        filename = f"doc_{i}.md"
        if os.path.exists(filename):
            file = sdk.files.upload(filename, ttl_days=365, expiration_policy="static")
            files.append(file)
            print(f"Файл {filename} загружен")
            
    if not files:
        print("Нет файлов для загрузки.")
        return

    print("Создание поискового индекса (может занять пару минут)...")
    operation = sdk.search_indexes.create_deferred(
        files,
        index_type=TextSearchIndexType(
            chunking_strategy=StaticIndexChunkingStrategy(
                max_chunk_size_tokens=700,
                chunk_overlap_tokens=300,
            )
        ),
    )
    search_index = operation.wait()
    
    print("Создание Ассистента...")
    tool = sdk.tools.search_index(search_index)
    assistant = sdk.assistants.create('yandexgpt', tools=[tool], ttl_days=365)
    
    print("=" * 50)
    print(f"ГОТОВО! Ваш YA_ASSISTANT_ID: {assistant.id}")
    print("Скопируйте этот ID и вставьте его в файл .env")
    print("=" * 50)

if __name__ == "__main__":
    parse_and_save()
    create_assistant()