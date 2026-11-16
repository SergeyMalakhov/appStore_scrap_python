"""Модель отзыва. Нижний уровень: никого из проекта не импортирует."""

from dataclasses import dataclass


@dataclass
class Review:
    """Один отзыв из App Store.

    review_id — служебное поле для дедупликации, в CSV не выводится.
    """

    author: str
    date: str        # ГГГГ-ММ-ДД
    rating: int      # 1..5
    title: str
    review: str
    review_id: str
    country: str
    app_version: str = ""
    developer_response: str = ""

    def to_row(self) -> dict:
        """Возвращает словарь-строку для CSV без служебного review_id."""
        return {
            "author": self.author,
            "date": self.date,
            "rating": self.rating,
            "title": self.title,
            "review": self.review,
            "country": self.country,
            "app_version": self.app_version,
            "developer_response": self.developer_response,
        }
