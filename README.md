# E-commerce API

A FastAPI learning project for an e-commerce backend with product management, checkout flow, analytics, AI features, and workflow automation. I am aware that all kind of user authentication and authorization are missing, but this is something I have actually worked with, so it doesn't fall under the "learning" category in this case and is currently with lower priority for the project's purposes.

## Features

- Create, list, update, and delete products
- Create orders and manage order items
- Validate stock before checkout
- Prevent double checkout and invalid order mutations
- Calculate totals, tax, discounts, and shipping
- Send order confirmations asynchronously through Celery
- Sales analytics and reporting
- Semantic product search with pgvector
- AI integration with Gemini
- RAG and AI tool calling
- Multi-turn AI conversations with Redis
- Async AI chat and semantic search
- Order status and cancellation tools
- Confirmation flow for destructive AI actions
- MCP server for external AI integrations
- n8n workflow automation
- High-value order email notifications
- AI-generated daily sales summaries
- Dockerized application and services

## Tech Stack

- FastAPI
- SQLAlchemy
- PostgreSQL + pgvector
- Celery + Redis
- Pandas
- Pydantic
- Gemini
- n8n
- Docker
- Pytest

## Run

```bash
docker compose up -d --build
```
