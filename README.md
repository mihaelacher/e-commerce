# E-commerce API

A small FastAPI project for an e-commerce backend with product management and checkout flow.

## Features

- Create, list, update, and delete products
- Create orders and manage order items
- Validate stock before checkout
- Prevent double checkout and invalid order mutations
- Calculate totals, tax, and shipping values
- Send order confirmation asynchronously through Celery

## Tech stack

- FastAPI
- SQLAlchemy
- PostgreSQL
- Celery + Redis
- Pydantic
- Pytest

## Run locally

Start PostgreSQL and Redis:

```bash
docker compose up -d db redis
```

Install dependencies and start the app:

```bash
uv sync
uv run uvicorn app.main:app --reload
```

## Run tests

```bash
uv run pytest -q
```

The test suite uses a separate PostgreSQL database named `ecommerce_test`.
It is created automatically using the PostgreSQL credentials in
`.env`. You can override the connection explicitly with `TEST_DATABASE_URL`.

## Notes

This is a learning project focused on backend architecture, business rules, and clean API design.
