# Нагрузочное тестирование

Инструменты для проверки, держит ли связка **django-ninja + PostgreSQL + Redis**
шквал одновременных запросов и отвечает ли стабильно. Нестабильность под
нагрузкой — сигнал N+1 или отсутствия индексов.

Состав:

- `locustfile.py` — сценарий реальной сессии зрителя (сколько система держит);
- `seed_loadtest` — management-команда наполнения БД (`accounts/management/commands`);
- `profile_queries` — детектор N+1: считает SQL-запросы на ручках (почему тормозит).

## Предохранители

- Сид и профайлер меняют/создают данные и **требуют `LOADTEST=1`** — боевое
  окружение эту переменную не выставляет.
- Сид оперирует только объектами с префиксом `loadtest_`; `--flush` удаляет
  строго их, живых пользователей не трогает.
- Locust **не стартует против нелокального хоста** без `LOADTEST_ALLOW_REMOTE=1`.
- Регистрация в сценарии реально пишет пользователей — почта должна быть
  замокана (`EMAIL_BACKEND=locmem`), иначе уйдут настоящие письма и упрётся в
  таймаут SMTP.

## Быстрый прогон (один скрипт)

Нужен запущенный Docker Desktop. Скрипт поднимает **изолированный** стек
(отдельный compose-проект `steinsgate_loadtest`, свои тома, порт 4273 — локальный
стек на 4173 не затрагивается), наполняет БД, снимает профиль N+1, гоняет Locust
лестницей и в конце сносит стек вместе с одноразовыми томами.

```bash
backend/loadtest/run_loadtest.sh                       # 50 -> 200 -> 500, по 60с
backend/loadtest/run_loadtest.sh --stages "100 500 1000" --time 90s
backend/loadtest/run_loadtest.sh --keep                # оставить стек и данные
backend/loadtest/run_loadtest.sh --down                # снести изолированный стек
```

Отчёты (CSV/HTML/профиль) складываются в `loadtest_out/` (в .gitignore).

## Результаты замера

Прогон на dev-машине (Postgres 16 + Redis 7 + gunicorn gthread за nginx),
конфигурация оверлея `GUNICORN_WORKERS=4 GUNICORN_THREADS=8`. Разовый прогон,
числа зависят от железа.

| Юзеров | RPS | p50 | p95 | Ошибки |
|--------|-----|-----|-----|--------|
| 50 | 26  | 22 ms | 220 ms | 0% |
| 200 | 90  | 49 ms | 2200 ms  | 0% |
| 500 | 234 | 43 ms | 1300 ms  | ~0% |
| 1000 | 275 | 1000 ms | 9400 ms  | ~0% |

До перевода gunicorn на gthread (3 sync-воркера) 500 юзеров давали ~83 RPS и
p95 15000 ms — упор был в число воркеров, не в БД (Postgres держал <1% CPU).
Профиль N+1: страница комментариев — константа по числу запросов (N+1 нет),
кэш каталога срабатывает.

## Ручной прогон

Для точечного запуска против уже поднятого стека (без изоляции скрипта):

```bash
docker compose -f compose.yaml -f compose.loadtest.yaml up -d --build
docker compose -f compose.yaml -f compose.loadtest.yaml exec -e LOADTEST=1 backend python manage.py seed_loadtest --users 500 --comments 150

LOADTEST_USERS=500 locust -f backend/loadtest/locustfile.py --host http://localhost:4173 --headless -u 500 -r 25 -t 5m --csv=loadtest_out/manual --html=loadtest_out/manual.html
```

Оверлей `compose.loadtest.yaml` уже ставит `DEBUG=False`, нейтрализует лимиты
через env, мокает почту на `locmem` и поднимает конкурентность gunicorn —
`settings.py` при этом не меняется.

## Поиск N+1 без нагрузки

```bash
docker compose -f compose.yaml -f compose.loadtest.yaml exec -e LOADTEST=1 backend python manage.py profile_queries   # --verbose-sql — печатать SQL
```

Считает число SQL-запросов на ручках. Если на странице комментариев оно растёт
с числом комментов — это N+1. Данные создаются во временной транзакции и
откатываются, кэш каталога чистится до и после.

## На что смотреть в отчёте

- **p95 / p99** по ручке — резкий рост = узкое место.
- **% ошибок** — всплеск 5xx = падение под конкуренцией (дедлоки, исчерпание
  пула соединений, таймауты).
- **RPS-плато** — перестал расти при добавлении юзеров = достигнут потолок.
- Горячие запросы из `profile_queries` разбираются через `EXPLAIN ANALYZE`.

## Уборка

Скрипт сам делает `down -v` изолированного проекта (если не `--keep`). Вручную:

```bash
docker compose -p steinsgate_loadtest -f compose.yaml -f compose.loadtest.yaml down -v
```

Если сидили в свой стек напрямую — очистка данных без остановки:

```bash
docker compose -f compose.yaml -f compose.loadtest.yaml exec -e LOADTEST=1 backend python manage.py seed_loadtest --flush
```
