"""Хранение отзывов: чтение, запись и дедупликация reviews.csv. Без сети."""

import csv
import logging
from pathlib import Path

from config import CSV_PATH
from models import Review

logger = logging.getLogger(__name__)

# Колонки итогового CSV. review_id служебный и в файл не пишется.
CSV_COLUMNS = ["author", "date", "rating", "title", "review", "country", "app_version", "developer_response"]


def load_existing(path: str = CSV_PATH) -> set:
    """Читает существующий CSV и возвращает множество ключей сохранённых отзывов.

    review_id в файл не пишется, поэтому дедупликация против CSV идёт по
    составному ключу "author|date|title". Файла нет — вернётся пустое множество.

    Args:
        path: путь к CSV-файлу.

    Returns:
        Множество строк-ключей уже сохранённых отзывов.

    Raises:
        ValueError: если файл существует, но не читается.
    """
    csv_path = Path(path)
    if not csv_path.exists():
        logger.info("Файл %s не найден — начинаем с чистого листа", path)
        return set()
    try:
        with csv_path.open(encoding="utf-8-sig", newline="") as file:
            keys = {key for key in (_row_key(row) for row in csv.DictReader(file)) if key}
    except (OSError, csv.Error) as exc:
        logger.error("Не удалось прочитать %s: %s", path, exc)
        raise ValueError(f"Файл {path} повреждён или недоступен для чтения.") from exc
    logger.info("В %s найдено %s сохранённых отзывов", path, len(keys))
    return keys


def deduplicate(reviews: list, existing_keys: set) -> list:
    """Убирает повторы: внутри запуска по review_id, против CSV — по ключу строки.

    Args:
        reviews: список Review, собранных за один запуск.
        existing_keys: множество ключей из существующего CSV (см. load_existing).

    Returns:
        Список Review без дубликатов, в порядке поступления.
    """
    seen_ids: set = set()
    seen_keys: set = set(existing_keys)
    unique = []
    for review in reviews:
        if review.review_id in seen_ids:
            continue
        key = _row_key(review.to_row())
        if key in seen_keys:
            continue
        seen_ids.add(review.review_id)
        seen_keys.add(key)
        unique.append(review)
    logger.info("Дедупликация: убрано %s повторов из %s отзывов", len(reviews) - len(unique), len(reviews))
    return unique


def save(reviews: list, path: str = CSV_PATH) -> None:
    """Объединяет новые отзывы с уже лежащими в CSV и перезаписывает файл.

    Запись в utf-8-sig — кириллица корректно открывается в Excel.

    Args:
        reviews: новые (уже продедуплицированные) отзывы.
        path: путь к CSV-файлу.

    Raises:
        ValueError: если файл недоступен для записи.
    """
    old_rows = _read_rows(path)
    new_rows = [review.to_row() for review in reviews]
    try:
        with Path(path).open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS, restval="")
            writer.writeheader()
            writer.writerows(old_rows)
            writer.writerows(new_rows)
    except OSError as exc:
        logger.error("Не удалось записать %s: %s", path, exc)
        raise ValueError(f"Файл {path} недоступен для записи.") from exc
    logger.info("Сохранено: %s старых + %s новых отзывов в %s", len(old_rows), len(new_rows), path)


def load_all(path: str = CSV_PATH) -> list:
    """Читает весь CSV обратно в модели Review — например, для показа в интерфейсе.

    Args:
        path: путь к CSV-файлу.

    Returns:
        Список Review из файла; пустой список, если файла нет.
    """
    reviews = []
    for row in _read_rows(path):
        try:
            reviews.append(
                Review(
                    author=row["author"],
                    date=row["date"],
                    rating=int(row.get("rating") or 0),
                    title=row["title"],
                    review=row["review"],
                    review_id="",
                    country=row["country"],
                    app_version=row.get("app_version", ""),
                    developer_response=row.get("developer_response", ""),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning("Пропускаю некорректную строку CSV: %s (%s)", row, exc)
    return reviews


def _row_key(row: dict):
    """Составной ключ строки для дедупликации против CSV; None, если полей не хватает."""
    author, date, title = row.get("author"), row.get("date"), row.get("title")
    if author is None or date is None or title is None:
        return None
    return f"{author}|{date}|{title}"


def _read_rows(path: str) -> list:
    """Читает CSV в список словарей, отбрасывая полностью пустые строки."""
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    try:
        with csv_path.open(encoding="utf-8-sig", newline="") as file:
            rows = [
                row
                for row in csv.DictReader(file)
                if any((value or "").strip() for value in row.values())
            ]
    except (OSError, csv.Error) as exc:
        logger.error("Не удалось прочитать %s: %s", path, exc)
        raise ValueError(f"Файл {path} повреждён или недоступен для чтения.") from exc
    return rows
