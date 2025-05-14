from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options

# Путь к msedgedriver (скачай с https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/)
EDGE_DRIVER_PATH = '/root/money/msedgedriver'  # замените на свой путь


def open_edge():
    options = Options()
    # Если нужно, можно включить headless режим:
    # options.add_argument("--headless")

    service = Service(executable_path=EDGE_DRIVER_PATH)
    driver = webdriver.Edge(service=service, options=options)

    driver.get("https://www.microsoft.com")  # Открываем сайт Microsoft
    print("Браузер открыт и загружена страница")

    # Чтобы не закрывать сразу, можно подождать
    input("Нажмите Enter для закрытия браузера...")
    driver.quit()


if __name__ == "__main__":
    open_edge()
