from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import time

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

data = []
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

df = pd.DataFrame(data)
df.to_csv("output.csv", index=False)
driver.quit()
