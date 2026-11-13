# Сбор отзывов из App Store ⭐

Python-приложение с веб-интерфейсом на Streamlit, которое выкачивает отзывы приложений из бесплатного публичного RSS-фида Apple для российского и американского сторов, удаляет повторы и накапливает их в CSV-файле.

## Ключевые возможности

- 🌍 Сбор отзывов из двух сторов: Россия (`ru`) и США (`us`) — список стран задаётся в [`config.py`](config.py).
- 📄 До 10 страниц фида на страну, до 50 отзывов на страницу (настройки `MIN_PAGES` / `MAX_PAGES` / `DEFAULT_PAGES`).
- 🧹 Дедупликация: внутри запуска по служебному `review_id`, против уже сохранённых данных — по составному ключу «автор + дата + заголовок» (см. [`storage.py`](storage.py)).
- 💾 Накопление данных: новые отзывы добавляются к уже лежащим в `reviews.csv`, файл пишется в `utf-8-sig`, поэтому кириллица корректно открывается в Excel.
- 🖥️ Веб-интерфейс: прогресс-бар загрузки, метрики (всего отзывов, средний рейтинг), гистограмма оценок, таблица и кнопка скачивания CSV (см. [`app.py`](app.py)).
- ⚠️ Понятная обработка ошибок: ограничение частоты запросов Apple (HTTP 403), сетевые сбои и таймауты, невалидный JSON ([`fetcher.py`](fetcher.py)).
- 🔀 Чистое разделение слоёв: сеть, парсинг, хранение и интерфейс не зависят друг от друга напрямую.

## Оглавление

1. [Ключевые возможности](#ключевые-возможности)
2. [Инструменты и технологии](#инструменты-и-технологии)
3. [Требования](#требования)
4. [Установка](#установка)
5. [Запуск](#запуск)
6. [Структура проекта](#структура-проекта)
7. [Как это работает](#как-это-работает)
8. [Лицензия и автор](#лицензия-и-автор)

## Инструменты и технологии

| Инструмент | Назначение | Документация |
|---|---|---|
| Python 3 | язык проекта | [MDN: Python-подобный синтаксис в JavaScript не нужен 🙂, но основы регулярных выражений](https://developer.mozilla.org/ru/docs/Web/JavaScript/Guide/Regular_expressions) и общие веб-стандарты описаны на [MDN Web Docs](https://developer.mozilla.org/ru/) |
| [requests](https://pypi.org/project/requests/) | HTTP-запросы к RSS-фиду Apple | [MDN: HTTP](https://developer.mozilla.org/ru/docs/Web/HTTP) — статусы ответов, заголовки, таймауты |
| [Streamlit](https://streamlit.io/) | веб-интерфейс | [MDN: Web-приложения](https://developer.mozilla.org/ru/docs/Learn/Web) — как устроен фронтенд, который рендерит Streamlit |
| [pandas](https://pandas.pydata.org/) | таблицы, метрики, графики | [MDN: JSON](https://developer.mozilla.org/ru/docs/Learn/JavaScript/Objects/JSON) и [CSV-подобные данные](https://developer.mozilla.org/ru/docs/Web/API/Blob) — форматы обмена данными в вебе |
| CSV (`utf-8-sig`) | хранение отзывов | [MDN: символ-кодировки (UTF-8, BOM)](https://developer.mozilla.org/ru/docs/Web/API/Encoding_API) |
| RSS-фид Apple | источник данных | [MDN: XML/RSS-подобные форматы](https://developer.mozilla.org/ru/docs/Web/API/XMLHttpRequest) и [JSON](https://developer.mozilla.org/ru/docs/Learn/JavaScript/Objects/JSON) — фид отдаётся в JSON |

## Требования

- **ОС:** Windows, macOS или Linux.
- **Python 3.10+** (в коде используется синтаксис `X | None` в аннотациях).
- **Браузер** для веб-интерфейса (Streamlit открывает локальную страницу):
  - Google Chrome / Microsoft Edge 90+
  - Mozilla Firefox 90+
  - Safari 14+
- Доступ в интернет — приложение ходит на `itunes.apple.com`.
- Зависимости из [`requirements.txt`](requirements.txt):

```
requests
streamlit
pandas
```

## Установка

1. Склонируйте или скачайте проект и перейдите в его папку:

   ```powershell
   cd appStore_scrap_python
   ```

2. (Рекомендуется) создайте виртуальное окружение:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1      # Windows PowerShell
   source .venv/bin/activate       # macOS / Linux
   ```

3. Установите зависимости:

   ```powershell
   pip install -r requirements.txt
   ```

## Запуск

1. Запустите Streamlit-приложение:

   ```powershell
   streamlit run app.py
   ```

2. Браузер откроется автоматически на `http://localhost:8501`.
3. В поле ввода укажите **App ID приложения** (только цифры, например `597986893`).
4. Ползунком выберите, сколько страниц фида собирать (1–10 на страну).
5. Нажмите **«Собрать отзывы»** — прогресс-бар покажет, какая страница и страна обрабатываются.
6. Результат смотрится прямо на странице и накапливается в `reviews.csv`; кнопка **«Обновить данные»** перечитывает файл, а **«Скачать CSV»** выгружает текущий набор.

Все настройки (страны, пауза и таймаут запросов, границы слайдера, имя файла) меняются в одном месте — [`config.py`](config.py).

## Структура проекта

```
appStore_scrap_python/
├── app.py            # Streamlit-интерфейс: виджеты, прогресс-бар, отображение
├── scraper.py        # Оркестратор: собирает fetcher + parser + storage
├── fetcher.py        # Сетевая часть: запросы к RSS-фиду Apple
├── parser.py         # Разбор JSON фида в модель Review
├── storage.py        # Чтение/запись reviews.csv и дедупликация
├── models.py         # Модель Review (dataclass)
├── config.py         # Все константы проекта в одном месте
├── requirements.txt  # Зависимости
├── reviews.csv       # Накопленные отзывы (создаётся автоматически)
└── README.md
```

### Описание директорий и файлов

- [`app.py`](app.py) — точка входа и слой представления. Только виджеты Streamlit и вывод данных; вся логика вызывается через одну функцию `collect_reviews`. Здесь же перехватываются и красиво показываются исключения.
- [`scraper.py`](scraper.py) — оркестратор: в цикле обходит страны и страницы, склеивает `fetcher` → `parser` → `storage` и возвращает объединённый список отзывов.
- [`fetcher.py`](fetcher.py) — только сеть: формирует URL по шаблону, соблюдает паузу между запросами, различает 403 (ограничение Apple), прочие статусы и невалидный JSON.
- [`parser.py`](parser.py) — только парсинг: превращает JSON-записи фида в модели `Review`, терпимо относится к отсутствующим полям и приводит даты к формату `ГГГГ-ММ-ДД`.
- [`storage.py`](storage.py) — только файлы: читает и пишет `reviews.csv` (в `utf-8-sig` для Excel), дедуплицирует отзывы и возвращает данные для интерфейса.
- [`models.py`](models.py) — нижний уровень: dataclass `Review` и метод `to_row()` для CSV; никого из проекта не импортирует.
- [`config.py`](config.py) — константы: шаблон URL фида, страны, паузы, таймауты, границы слайдера и имя файла.
- `reviews.csv` — файл данных; создаётся автоматически при первом запуске, `review_id` в него не пишется.

## Как это работает

Данные проходят путь: `fetcher` скачивает страницу фида → `parser` разбирает её в список `Review` → `storage` дедуплицирует и дописывает в CSV → `app` показывает результат. Ошибки не глотаются: `RateLimitError`, `NetworkError` и `ValueError` пробрасываются до интерфейса.

Полезные ссылки для понимания форматов и веб-технологий, с которыми работает проект:

- [MDN: Обзор HTTP](https://developer.mozilla.org/ru/docs/Web/HTTP) — статусы ответов, включая `403 Forbidden`;
- [MDN: Работа с JSON](https://developer.mozilla.org/ru/docs/Learn/JavaScript/Objects/JSON) — структура фида Apple;
- [MDN: Кодировки и Encoding API](https://developer.mozilla.org/ru/docs/Web/API/Encoding_API) — почему CSV пишется в `utf-8-sig`;
- [MDN: Fetch API](https://developer.mozilla.org/ru/docs/Web/API/Fetch_API) — как те же запросы выглядели бы в браузере.

## Лицензия и автор

Проект распространяется под лицензией [MIT License](https://opensource.org/licenses/MIT) — код можно свободно использовать, изменять и распространять с сохранением этого уведомления.

**Автор:** Richa
**Проект:** appStore_scrap_python (2026)

Если проект оказался полезным — расскажите о нём или заведите issue с предложениями.
