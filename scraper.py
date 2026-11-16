"""Оркестратор: собирает fetcher + parser + storage в одну функцию."""

import logging
import time
from typing import Callable

from config import (
    COUNTRIES,
    CSV_PATH,
    DEFAULT_LANG,
    EMPTY_PAGE_RETRIES,
    LANGUAGES,
    RETRY_PAUSE,
)
from fetcher import NetworkError, RateLimitError, fetch_page
from models import Review
from parser import parse_reviews
from storage import deduplicate, load_all, load_existing, save

logger = logging.getLogger(__name__)

# Коллбэк прогресса: (номер страницы, всего страниц, код страны).
ProgressCallback = Callable[[int, int, str], None]


def collect_reviews(
    app_id: str,
    pages: int,
    csv_path: str = CSV_PATH,
    lang: str = DEFAULT_LANG,
    on_progress: "ProgressCallback | None" = None,
) -> list:
    """Собирает отзывы со всех страниц и стран и сохраняет их в CSV.

    Возвращает полный объединённый список отзывов (старые из CSV + новые),
    готовый для отображения. Ошибки не глотаются: RateLimitError, NetworkError
    и ValueError пробрасываются наверх — их показом занимается интерфейс.

    Язык определяет, из каких сторов собирать: у каждого языка в LANGUAGES
    задан список стран. Страницы с параметром ?lang при пустом ответе
    перезапрашиваются без языкового фильтра; любая пустая страница
    повторяется несколько раз — у RSS Apple бывают случайные «дыры».

    Args:
        app_id: идентификатор приложения (только цифры).
        pages: сколько страниц фида запрашивать на каждую страну.
        csv_path: путь к файлу накопленных отзывов.
        lang: код языка из LANGUAGES; неизвестный код — сторы по умолчанию.
        on_progress: необязательный коллбэк прогресса (страница, всего страниц, страна).

    Returns:
        Объединённый список Review без дубликатов.

    Raises:
        RateLimitError: Apple ограничил частоту запросов.
        NetworkError: сетевые ошибки и таймаут.
        ValueError: невалидный JSON, плохой статус ответа или файл CSV.
    """
    lang_config = LANGUAGES.get(lang)
    if lang_config:
        countries = lang_config["countries"]
        # Параметр ?lang нужен только для локалей вида xx_yy (en_us, en_gb):
        # для односложных кодов стор сам отдаёт нужный язык, а чужой параметр
        # делает фид пустым.
        lang_param = lang_config.get("lang_param", "")
    else:
        logger.warning("Неизвестный язык %r — использую сторы по умолчанию", lang)
        countries = COUNTRIES
        lang_param = ""

    logger.info(
        "Запуск сбора: app_id=%s, pages=%s, страны=%s, язык=%s", app_id, pages, countries, lang
    )
    collected: list = []
    for country in countries:
        for page in range(1, pages + 1):
            if on_progress:
                on_progress(page, pages, country)

            # У фида Apple бывают «дыры»: случайно пустая страница в середине
            # выборки (зависит от CDN-кэша). Повторяем запрос той же страницы.
            reviews = []
            for attempt in range(EMPTY_PAGE_RETRIES + 1):
                reviews = parse_reviews(fetch_page(country, page, app_id, lang_param), country)
                if reviews:
                    break
                if attempt < EMPTY_PAGE_RETRIES:
                    logger.info(
                        "Пустая страница %s/%s (попытка %s) — повторяю", country, page, attempt + 1
                    )
                    time.sleep(RETRY_PAUSE)
            if not reviews and lang_param:
                # Последний шанс: без языкового параметра (для локалей xx_yy).
                logger.info("Перезапрашиваю %s/%s без языкового фильтра", country, page)
                reviews = parse_reviews(fetch_page(country, page, app_id, ""), country)
            if not reviews:
                logger.warning(
                    "Страница %s/%s осталась пустой — у фида для этого приложения "
                    "может не быть отзывов на выбранном языке",
                    country,
                    page,
                )
            collected.extend(reviews)

    existing_keys = load_existing(csv_path)
    new_reviews = deduplicate(collected, existing_keys)
    save(new_reviews, csv_path)
    all_reviews = load_all(csv_path)
    logger.info("Готово: в %s теперь %s отзывов", csv_path, len(all_reviews))
    return all_reviews
