from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import asyncio
import time
from datetime import datetime, timedelta, timezone
import re
from database import db


def read_webpage():
    # Запуск браузера
    driver = webdriver.Chrome()
    driver.get(
        "https://poufe.ru/anons.php?type=all&day=today&anons=&page=&sorted=&filt=11111111"
    )
    time.sleep(3)  # Дать странице полностью загрузиться

    # Находим целевую таблицу
    target_table = driver.find_element(
        By.CSS_SELECTOR,
        "#podlozh > center > table > tbody > tr > td:nth-child(2) > center:nth-child(2) > table > tbody > tr > td:nth-child(2) > table > tbody > tr:nth-child(3) > td > table > tbody > tr:nth-child(2) > td > table",
    )

    translater = {
        "locations": [
            {"title": '"Башкирия", lifestyle-центр', "id": 12},
            {"title": '"Глобал Синема в ТРЦ "Меркурий", кинотеатр', "id": 1},
            {"title": '"Дом-музей В.И. Ленина", музей', "id": 11},
            {"title": '"Киномакс Нео", кинотеатр', "id": 14},
            {"title": '"Кинопростор", кинотеатр', "id": 15},
            {"title": '"Мегаполис", кинотеатр', "id": 7},
            {"title": '"Мемориальный дом-музей С.Т. Аксакова", музей', "id": 16},
            {
                "title": '"Музей 112-й Башкирской кавалерийской дивизии", музей',
                "id": 20,
            },
            {"title": '"Музей археологии и этнографии УНЦ РАН", музей', "id": 9},
            {"title": '"Музей им. М.В.Нестерова"', "id": 10},
            {"title": '"Национальный музей РБ", музей', "id": 17},
            {"title": '"Республиканский музей Боевой Славы", музей', "id": 18},
            {"title": '"Родина", кинотеатр', "id": 6},
            {
                "title": '"Россия — моя история", мультимедийный исторический парк',
                "id": 4,
            },
            {"title": '"Синема 5 в ТРЦ "АкварИн", кинотеатр', "id": 8},
            {"title": '"Синема Парк" в "Галерее ART", кинотеатр', "id": 13},
            {"title": '"Синема Парк" в ТРК "СемьЯ", кинотеатр', "id": 2},
            {"title": '"Урал", галерея народного искусства', "id": 3},
            {"title": '"Уфимская художественная галерея", галерея', "id": 19},
            {"title": '"Центральная городская библиотека"', "id": 5},
            {"title": '"Дом-музей А.Э.Тюлькина", музей', "id": 21},
            {"title": '"Музей истории города Уфы"', "id": 22},
        ],
        "events_types": [
            {"title": "выставка", "id": 4},
            {"title": "интерактивная выставка", "id": 3},
            {"title": "мультфильм", "id": 2},
            {"title": "мультфильмы", "id": 2},
            {"title": "кинофильм", "id": 1},
        ],
    }

    data = []  # Список данных из сайта
    events = []  # Готовый для сохранения в БД список событий
    if target_table:
        rows = target_table.find_elements(By.TAG_NAME, "tr")
        for row in rows[2:]:  # Пропустить заголовок и пагинатор
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 4:
                data.append(
                    {
                        "event": cols[0].text.strip(),
                        "location": cols[1].text.strip(),
                        "time": cols[2].text.strip(),
                        "price": cols[3].text.strip(),
                    }
                )

                location = next(
                    (
                        loc
                        for loc in translater["locations"]
                        if loc["title"] == cols[1].text.strip()
                    ),
                    None,
                )
                if location is not None:
                    # Извлекаем название события из двойных кавычек
                    event_text = cols[0].text.strip()

                    # Используем регулярное выражение для извлечения текста в двойных кавычках
                    title_match = re.search(r'"(.*?)"', event_text)
                    if title_match:
                        event_title = title_match.group(1)
                    else:
                        # Если кавычек нет, используем текст до первой запятой как запасной вариант
                        event_title = event_text.split(",")[0]

                    # Извлекаем тип события (текст после кавычек)
                    event_type_text = event_text.split('"')[-1].strip()
                    if event_type_text.startswith(","):
                        event_type_text = event_type_text[1:].strip()

                    event_type = next(
                        (
                            loc
                            for loc in translater["events_types"]
                            if loc["title"] == event_type_text
                        ),
                        None,
                    )
                    if event_type is not None:
                        start_date_str = cols[2].text.strip()
                        hours, minutes = start_date_str.split(".")
                        start_time_str = f"{hours}:{minutes}"
                        today_str = datetime.now(
                            tz=timezone(offset=timedelta(hours=5))
                        ).strftime("%Y-%m-%d")
                        start_date = datetime.strptime(
                            f"{today_str} {start_time_str}", "%Y-%m-%d %H:%M"
                        )
                        start_date_formatted = start_date.strftime(
                            "%Y-%m-%d %H:%M:%S+05"
                        )
                        price_value = cols[3].text.strip().split(" ")[0]
                        # Если цена не указана, устанавливаем ее в 0
                        try:
                            price = int(price_value)
                        except ValueError:
                            price = 0

                        events.append(
                            {
                                "title": event_title,
                                "start_date": start_date_formatted,
                                "location_id": location["id"],
                                "category_id": event_type["id"],
                                "price": price,
                            }
                        )
                    else:
                        print("Event type not found", event_type_text)
                else:
                    print("Location not found", cols[1].text.strip())

    df = pd.DataFrame(data)
    df.to_csv("data.csv", index=False)

    df = pd.DataFrame(events)
    df.to_csv("events.csv", index=False)

    driver.quit()


async def load_events_to_db():
    await db.connect()

    # Read events.csv
    df = pd.read_csv("events.csv")

    # Convert to list of dicts
    events_data = []
    for _, row in df.iterrows():
        event = {
            "title": str(row["title"]),
            "start_date": str(row["start_date"]),
            "location_id": int(row["location_id"]),
            "category_id": int(row["category_id"]),
            "price": (
                int(row["price"])
                if pd.notna(row["price"]) and row["price"] != ""
                else None
            ),
        }
        events_data.append(event)

    # Convert to JSONB array format for PostgreSQL
    import json

    events_jsonb = [json.dumps(event) for event in events_data]

    # Call the stored procedure
    try:
        results = await db.execute_procedure("create_events_secure", events_jsonb)
        print("Events loaded successfully. Results:")
        for result in results:
            print(
                f"ID: {result['created_id']}, Status: {result['status']}, Error: {result['error_message']}"
            )
    except Exception as e:
        print(f"Error loading events: {e}")


read_webpage()
# asyncio.run(load_events_to_db())
