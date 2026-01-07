# Multichart v4

Проект создаёт HTTP API для управления сеткой вкладок Chrome через CDP и снимков экрана.

## Структура

- `server.py` — HTTP API.
- `chrome.py` — CDP управление Chrome.
- `capture.py` — retina-скриншоты и crop.
- `ui.py` — логика сетки Multichart.
- `config.py` — DPI, viewport и координаты crop.

## Установка зависимостей

```bash
pip install websockets pillow
```

## Запуск

1. Запустите Chrome с CDP (пример):

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

2. Запустите HTTP API:

```bash
python server.py
```

## HTTP API

- `GET /health` — проверка сервиса.
- `POST /open` — открыть URL и назначить ячейку.
  - JSON: `{ "url": "https://example.com", "row": 0, "col": 1 }`
- `POST /click` — клик по ячейке (активация вкладки).
  - JSON: `{ "x": 100, "y": 200 }`
- `POST /capture` — снимок ячейки.
  - JSON: `{ "row": 0, "col": 1, "output": "captures/cell-0-1.png" }`
