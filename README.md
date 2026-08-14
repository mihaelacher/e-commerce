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

1. Create and activate a virtual environment
2. Install dependencies
3. Copy the environment variables needed for your local setup
4. Start the app:

```bash
uvicorn app.main:app --reload
```

## Run tests

```bash
pytest
```

## Notes

This is a learning project focused on backend architecture, business rules, and clean API design.
