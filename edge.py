from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options

def open_edge():
    options = Options()
    # Если хочешь, можешь раскомментировать для headless режима:
    # options.add_argument("--headless=new")

    # Укажи путь к msedgedriver
    service = Service("/root/money/msedgedriver")  # Замените на свой путь

    driver = webdriver.Edge(service=service, options=options)
    driver.get("https://www.microsoft.com")
    print("Страница загружена:", driver.title)

    driver.quit()

if __name__ == "__main__":
    open_edge()
