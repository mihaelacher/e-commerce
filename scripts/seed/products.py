from app.core.database import SessionLocal, transaction
from app.repositories.product.sync_product import ProductRepository
from scripts.seed.product_data import PRODUCTS


def seed_products() -> None:
    db = SessionLocal()

    try:
        repository = ProductRepository(db)

        with transaction(db):
            for product_data in PRODUCTS:
                repository.create(
                    {
                        key: value
                        for key, value in product_data.items()
                        if key != "sales_weight"
                    }
                )
    finally:
        db.close()


if __name__ == "__main__":
    seed_products()
    print(f"Seeded {len(PRODUCTS)} products.")
