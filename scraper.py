"""Оркестратор: собирает fetcher + parser + storage в одну функцию."""

import logging
from typing import Callable

from config import COUNTRIES, CSV_PATH
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
    on_progress: "ProgressCallback | None" = None,
) -> list:
    """Собирает отзывы со всех страниц и стран и сохраняет их в CSV.

    Возвращает полный объединённый список отзывов (старые из CSV + новые),
    готовый для отображения. Ошибки не глотаются: RateLimitError, NetworkError
    и ValueError пробрасываются наверх — их показом занимается интерфейс.

    Args:
        app_id: идентификатор приложения (только цифры).
        pages: сколько страниц фида запрашивать на каждую страну.
        csv_path: путь к файлу накопленных отзывов.
        on_progress: необязательный коллбэк прогресса (страница, всего страниц, страна).

    Returns:
        Объединённый список Review без дубликатов.

    Raises:
        RateLimitError: Apple ограничил частоту запросов.
        NetworkError: сетевые ошибки и таймаут.
        ValueError: невалидный JSON, плохой статус ответа или файл CSV.
    """
    logger.info("Запуск сбора: app_id=%s, pages=%s, страны=%s", app_id, pages, COUNTRIES)
    collected: list = []
    for country in COUNTRIES:
        for page in range(1, pages + 1):
            if on_progress:
                on_progress(page, pages, country)
            collected.extend(parse_reviews(fetch_page(country, page, app_id), country))

    existing_keys = load_existing(csv_path)
    new_reviews = deduplicate(collected, existing_keys)
    save(new_reviews, csv_path)
    all_reviews = load_all(csv_path)
    logger.info("Готово: в %s теперь %s отзывов", csv_path, len(all_reviews))
    return all_reviews
