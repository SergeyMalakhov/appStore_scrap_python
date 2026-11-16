"""Сетевая часть: запросы к RSS-фиду Apple. Только запросы, без парсинга."""

import logging
import time

import requests

from config import DEFAULT_LANG, FEED_URL_TEMPLATE, REQUEST_PAUSE, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

# Псевдоним сетевого исключения: другим модулям не нужен прямой импорт requests.
NetworkError = requests.RequestException


class RateLimitError(Exception):
    """Apple ограничил частоту запросов (HTTP 403)."""


def fetch_page(country: str, page: int, app_id: str, lang: str = DEFAULT_LANG) -> dict:
    """Скачивает одну страницу отзывов фида Apple и возвращает её как dict.

    Args:
        country: код стора, например "ru" или "us".
        page: номер страницы фида (1..10).
        app_id: числовой идентификатор приложения.
        lang: язык отзывов; пустая строка — без языкового фильтра.
        lang: язык отзывов, например "ru" или "en_us".

    Returns:
        Разобранный в dict JSON фида.

    Raises:
        RateLimitError: если Apple вернул 403.
        NetworkError: при сетевых сбоях и таймауте.
        ValueError: при невалидном JSON или неожиданном статусе ответа.
    """
    url = FEED_URL_TEMPLATE.format(country=country, page=page, app_id=app_id)
    if lang:
        url += f"?lang={lang}"
    logger.info("Запрос фида: country=%s, page=%s, app_id=%s, lang=%s", country, page, app_id, lang)
    time.sleep(REQUEST_PAUSE)

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
    except NetworkError as exc:
        logger.error("Сетевая ошибка при запросе %s: %s", url, exc)
        raise

    if response.status_code == 403:
        logger.warning("Apple вернул 403 — сработало ограничение частоты")
        raise RateLimitError(
            "Слишком частые запросы. Apple временно ограничил доступ — "
            "подождите пару минут и попробуйте снова."
        )
    if response.status_code != 200:
        logger.error("Неожиданный статус %s для %s", response.status_code, url)
        raise ValueError(f"Фид Apple ответил кодом {response.status_code}.")

    try:
        data = response.json()
    except ValueError as exc:
        logger.error("Невалидный JSON в ответе %s: %s", url, exc)
        raise ValueError("Apple вернул ответ, который не удалось разобрать как JSON.") from exc

    logger.info("Фид получен: country=%s, page=%s", country, page)
    return data
