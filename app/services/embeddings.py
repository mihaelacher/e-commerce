from app.models.product import ProductModel


def build_product_text(product: ProductModel) -> str:
    return (
        f"Product: {product.name}\n"
        f"Description: {product.description or ''}"
    )
