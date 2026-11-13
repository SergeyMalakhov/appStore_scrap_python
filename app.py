"""Streamlit-интерфейс. Только виджеты и отображение; логика — в scraper.py."""

import logging
import time

import pandas as pd
import streamlit as st

from config import COUNTRIES, CSV_PATH, DEFAULT_PAGES, MAX_PAGES, MIN_PAGES
from fetcher import NetworkError, RateLimitError
from scraper import collect_reviews
from storage import CSV_COLUMNS, load_all

logger = logging.getLogger(__name__)
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

st.set_page_config(page_title="Отзывы из App Store", page_icon="⭐", layout="wide")

st.title("Сбор отзывов из App Store")
st.write(
    "Приложение выкачивает отзывы из бесплатного публичного RSS-фида Apple для "
    "России и США, удаляет повторы и накапливает их в reviews.csv. "
    "Одна страница фида — до 50 отзывов, максимум 10 страниц на страну."
)

LIMIT_MESSAGE = (
    "Слишком частые запросы. Apple временно ограничил доступ — "
    "подождите пару минут и попробуйте снова."
)


def show_reviews(reviews: list) -> None:
    """Показывает метрики, распределение оценок и таблицу отзывов."""
    df = pd.DataFrame([r.to_row() for r in reviews])
    if df.empty:
        st.info("Отзывов пока нет — соберите их кнопкой выше.")
        return
    df = df.sort_values("date", ascending=False).reset_index(drop=True)

    col_total, col_rating = st.columns(2)
    col_total.metric("Всего отзывов", len(df))
    col_rating.metric("Средний рейтинг", round(df["rating"].mean(), 2))
    st.bar_chart(df["rating"].value_counts().sort_index())
    st.dataframe(df[CSV_COLUMNS], use_container_width=True)

    csv_bytes = df[CSV_COLUMNS].to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Скачать CSV",
        data=csv_bytes,
        file_name="reviews.csv",
        mime="text/csv",
    )


# Отзывы между перезапусками скрипта держим в сессии; при первом запуске
# показываем то, что уже накоплено в reviews.csv.
if "reviews" not in st.session_state:
    st.session_state["reviews"] = load_all(CSV_PATH)

app_id = st.text_input("App ID приложения (только цифры)", placeholder="Например, 597986893")
if app_id and not app_id.isdigit():
    st.error("App ID должен состоять только из цифр.")

pages = st.slider(
    "Сколько страниц фида собирать",
    MIN_PAGES,
    MAX_PAGES,
    DEFAULT_PAGES,
    help="На каждой странице до 50 отзывов.",
)

col_run, col_refresh = st.columns(2)
run_clicked = col_run.button("Собрать отзывы", type="primary")
refresh_clicked = col_refresh.button("Обновить данные")


def run_collection() -> None:
    """Запускает сбор с прогресс-баром и показывает понятные ошибки."""
    if not app_id.isdigit():
        st.error("Введите корректный App ID — только цифры.")
        return

    progress_bar = st.progress(0.0, text="Готовимся к загрузке…")
    done_count = 0

    def on_progress(page: int, total_pages: int, country: str) -> None:
        """Обновляет прогресс-бар: «Страница 3 из 7, страна us…»."""
        nonlocal done_count
        done_count += 1
        fraction = done_count / (total_pages * len(COUNTRIES))
        progress_bar.progress(fraction, text=f"Страница {page} из {total_pages}, страна {country}…")

    try:
        reviews = collect_reviews(app_id, pages, CSV_PATH, on_progress)
    except RateLimitError:
        st.error(LIMIT_MESSAGE)
        return
    except NetworkError as exc:
        logger.error("Сетевая ошибка: %s", exc)
        st.error(f"Проблема с сетью или таймаут запроса: {exc}. Проверьте соединение и попробуйте снова.")
        return
    except ValueError as exc:
        logger.error("Ошибка данных: %s", exc)
        st.error(f"Не удалось обработать данные: {exc}")
        return
    progress_bar.progress(1.0, text="Готово!")
    st.session_state["reviews"] = reviews
    st.success(f"Готово! Сейчас в наборе {len(reviews)} отзывов.")
    show_reviews(reviews)


if run_clicked or refresh_clicked:
    run_collection()
elif st.session_state["reviews"]:
    st.subheader("Накопленные отзывы")
    show_reviews(st.session_state["reviews"])
