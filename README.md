# Hybrid Thesis Topic Novelty Assessment Model

[![Python CI and package candidate](https://github.com/Tsarkashrk/novelty-similarity-detection-model/actions/workflows/ci.yml/badge.svg)](https://github.com/Tsarkashrk/novelty-similarity-detection-model/actions/workflows/ci.yml)

Этот проект реализует модель для темы диссертации:

> Интеллектуальная платформа для управления дипломными и магистерскими проектами с функциями оценки новизны тем, устранения дублирования, назначения руководителей и мониторинга основных этапов.

Фокус репозитория: модуль оценки новизны тем и устранения дублирования.

## Что реализовано

Модель построена как hybrid pipeline:

```text
New thesis topic
    -> preprocessing
    -> sentence embedding
    -> cosine similarity search
    -> keyword uniqueness
    -> domain rarity
    -> novelty score
    -> duplicate / near duplicate / novel classification
```

Итоговая формула:

```text
NoveltyScore =
    alpha * (1 - max_semantic_similarity)
  + beta  * keyword_uniqueness
  + gamma * domain_rarity
```

По умолчанию:

```text
alpha = 0.60
beta  = 0.25
gamma = 0.15
```

Классификация:

```text
similarity >= 0.90 -> duplicate
similarity >= 0.75 -> near_duplicate
otherwise          -> novel
```

## Почему это подходит для магистерской

Модель не сводится к одному embedding model. Научная часть здесь состоит в объяснимой гибридной архитектуре:

- semantic similarity определяет близость темы к существующим работам;
- keyword uniqueness показывает редкость ключевых слов;
- domain rarity учитывает редкость доменной области и комбинаций domain + keyword;
- duplicate classification превращает score в практическое решение для платформы.

Такой подход легко описать в диссертации, воспроизвести в эксперименте и сравнить с baseline-моделями.

## Установка

Минимальная версия работает без внешних ML-зависимостей:

```bash
python3 -m pip install -e .
```

Для production-like embeddings:

```bash
python3 -m pip install -e ".[embeddings,api,experiment]"
```

Рекомендуемая embedding-модель:

```text
intfloat/multilingual-e5-base
```

Для более лёгкого запуска можно использовать:

```text
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

## CLI пример

```bash
PYTHONPATH=src python3 -m thesis_novelty.cli \
  --data data/sample_topics.csv \
  --title "Платформа анализа новизны тем дипломных проектов с использованием semantic embeddings" \
  --domain "education technology" \
  --keywords "semantic embeddings, novelty detection, thesis management"
```

С Sentence-BERT / E5:

```bash
PYTHONPATH=src python3 -m thesis_novelty.cli \
  --data data/sample_topics.csv \
  --embedding-model intfloat/multilingual-e5-base \
  --title "Интеллектуальная система оценки уникальности тем магистерских диссертаций"
```

## FastAPI

```bash
PYTHONPATH=src uvicorn thesis_novelty.api:create_app --factory --reload
```

Endpoint:

```text
POST /assess
```

Example body:

```json
{
  "title": "Интеллектуальная система оценки новизны тем дипломных проектов",
  "abstract": "Система использует multilingual embeddings, анализ ключевых слов и классификацию дублирования.",
  "keywords": ["semantic similarity", "novelty detection", "thesis management"],
  "domain": "education technology"
}
```

## Эксперимент

Проверка threshold-ов на размеченных парах:

```bash
PYTHONPATH=src python3 experiments/evaluate_thresholds.py \
  --topics data/sample_topics.csv \
  --pairs data/sample_pairs.csv
```

Скрипт выводит precision, recall и F1 для классов duplicate / near_duplicate / novel.

## PostgreSQL + pgvector

В папке `sql/` лежит схема таблиц для хранения тем, embedding-векторов и результатов сравнения. В текущем прототипе используется in-memory search, но интерфейс модели совместим с переходом на pgvector.

## Разработка и проверка

Нужен Python 3.10 или новее. Минимальная установка и тесты не требуют скачивания ML-модели:

```bash
python3 -m pip install -e .
python3 -m unittest discover -s tests -v
python3 -m compileall -q src
```

Изменения ведутся через Git. Для новой задачи создайте ветку, добавьте тест или воспроизводимый пример и откройте pull request. Шаблоны для ошибок и исследовательских задач доступны в [Issues](https://github.com/Tsarkashrk/novelty-similarity-detection-model/issues/new/choose). Не публикуйте реальные студенческие данные в issues или тестах.

[GitHub Actions](https://github.com/Tsarkashrk/novelty-similarity-detection-model/actions/workflows/ci.yml) запускает тесты на Python 3.10 и 3.12 для push и pull request. После успешных тестов push в `main` создаёт wheel-файл и сохраняет его как артефакт workflow. Это кандидат для ручного выпуска; автоматического развёртывания в университетскую систему пока нет. Конфигурация: [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

Проект распространяется по [лицензии MIT](LICENSE). В исследовательской работе фиксируйте версию корпуса, модель embeddings, веса, пороги и набор размеченных пар; результаты hashing fallback не следует считать итоговой проверкой качества многоязычной модели.

## Структура

```text
src/thesis_novelty/
  api.py                FastAPI application factory
  cli.py                command-line inference
  config.py             weights and thresholds
  embeddings.py         SentenceTransformer backend + deterministic fallback
  io.py                 CSV loading
  keyword_analysis.py   keyword uniqueness and domain rarity
  model.py              hybrid novelty model
  preprocessing.py      multilingual normalization and tokenization
  schemas.py            dataclasses for topics and results
experiments/
  evaluate_thresholds.py
data/
  sample_topics.csv
  sample_pairs.csv
sql/
  pgvector_schema.sql
tests/
  test_model.py
```
