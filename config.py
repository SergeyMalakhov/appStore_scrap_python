"""Константы проекта. Только данные, без логики.

Страны, паузы, таймауты и имя файла меняются здесь — в одном месте.
"""

FEED_URL_TEMPLATE = (
    "https://itunes.apple.com/{country}/rss/customerreviews"
    "/page={page}/id={app_id}/sortby=mostrecent/json"
)

# Коды сторов, из которых собираем отзывы.
COUNTRIES = ["ru", "us"]

# Пауза перед каждым запросом, секунды.
REQUEST_PAUSE = 2

# Таймаут одного HTTP-запроса, секунды.
REQUEST_TIMEOUT = 30

# Границы слайдера страниц и значение по умолчанию.
MIN_PAGES = 1
MAX_PAGES = 10
DEFAULT_PAGES = 5

# Имя файла с накопленными отзывами.
CSV_PATH = "reviews.csv"
