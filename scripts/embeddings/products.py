from app.core.database import SessionLocal
from app.core.dependencies.ai import get_embedding_client
from app.repositories.product import ProductRepository
from app.services.embeddings import build_product_text


def generate_product_embeddings() -> None:
    embedding_client = get_embedding_client()

    with SessionLocal() as db:
        repository = ProductRepository(db)

        products = repository.get_without_embedding()

        for product in products:
            text = build_product_text(product)

            product.embedding = embedding_client.embed(text)

            print(f"Generated embedding for: {product.name}")

        db.commit()


if __name__ == "__main__":
    generate_product_embeddings()