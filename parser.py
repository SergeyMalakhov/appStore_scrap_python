"""Разбор JSON фида Apple в модели Review. Только парсинг, без сети и файлов."""

import logging
from datetime import datetime

from models import Review

logger = logging.getLogger(__name__)


def parse_reviews(json_response: dict, country: str) -> list:
    """Превращает JSON-ответ фида в список Review.

    Пустая лента (нет ключа entry) — не ошибка, возвращается пустой список.

    Args:
        json_response: разобранный JSON от fetcher.fetch_page.
        country: код стора, записывается в поле country каждого отзыва.

    Returns:
        Список Review; отзывы с некорректными полями пропускаются с записью в лог.
    """
    feed = json_response.get("feed") if isinstance(json_response, dict) else None
    entries = feed.get("entry") if isinstance(feed, dict) else None
    if not entries:
        logger.info("Лента пуста для страны %s", country)
        return []
    # Фид с единственным отзывом отдаёт объект вместо списка.
    if isinstance(entries, dict):
        entries = [entries]

    reviews = []
    for index, entry in enumerate(entries):
        try:
            reviews.append(
                Review(
                    author=_label(entry, "author", "name"),
                    date=_normalize_date(_label(entry, "updated")),
                    rating=_rating(entry),
                    title=str(_label(entry, "title")),
                    review=str(_label(entry, "content")),
                    review_id=str(_label(entry, "id")),
                    country=country,
                )
            )
        except (AttributeError, TypeError, ValueError) as exc:
            logger.warning("Пропускаю отзыв #%s (%s): некорректные поля", index, country)
            logger.debug("Детали пропуска: %s", exc)
    logger.info("Разобрано %s отзывов из %s (страна %s)", len(reviews), len(entries), country)
    return reviews


def _label(entry: dict, *keys: str, default: str = "") -> str:
    """Достаёт значение .label по цепочке ключей, терпимо к отсутствующим полям."""
    value = entry
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return default
        value = value[key]
    if isinstance(value, dict):
        value = value.get("label")
    return default if value is None else str(value)


def _rating(entry: dict) -> int:
    """Извлекает рейтинг; у отзыва без оценки или со странным значением ставит 0."""
    raw = _label(entry, "im:rating", default="0")
    try:
        return int(raw)
    except ValueError:
        logger.warning("Некорректный рейтинг %r — ставлю 0", raw)
        return 0


def _normalize_date(raw: str) -> str:
    """Приводит дату к формату ГГГГ-ММ-ДД; при сбое возвращает первые 10 символов."""
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return parsed.strftime("%Y-%m-%d")
    except ValueError:
        logger.warning("Не удалось разобрать дату %r — оставляю как есть", raw)
        return raw[:10]
