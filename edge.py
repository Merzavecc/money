from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
import tempfile

def open_edge():
    options = Options()
    # Создаём уникальную временную папку для профиля
    profile_dir = tempfile.mkdtemp(prefix="edge_profile_")
    options.add_argument(f"--user-data-dir={profile_dir}")

    service = Service("/root/money/msedgedriver")  # Заменить на свой путь

    driver = webdriver.Edge(service=service, options=options)
    driver.get("https://www.microsoft.com")
    print("Страница загружена:", driver.title)

    input("Нажмите Enter для закрытия браузера...")
    driver.quit()

if __name__ == "__main__":
    open_edge()
