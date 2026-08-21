from fastapi.testclient import TestClient

from app.models.product import ProductModel


def create_product(
    client: TestClient,
    *,
    name: str = "Gaming Laptop",
    price: float = 1000.00,
    stock: int = 10,
) -> dict:
    response = client.post(
        "/products/",
        json={
            "name": name,
            "price": price,
            "stock": stock,
        },
    )

    assert response.status_code == 201

    return response.json()


def create_order(client: TestClient, *, email: str = "customer@example.com") -> dict:
    response = client.post(
        "/checkout/orders",
        json={"email": email},
    )

    assert response.status_code == 201

    return response.json()


def add_product_to_order(
    client: TestClient,
    order_id: int,
    product_id: int,
    quantity: int,
):
    return client.post(
        f"/checkout/orders/{order_id}/items",
        json={
            "product_id": product_id,
            "quantity": quantity,
        },
    )


def test_create_order(client):
    response = client.post(
        "/checkout/orders",
        json={"email": "customer@example.com"},
    )

    assert response.status_code == 201

    data = response.json()

    assert "id" in data
    assert data["status"] == "pending"
    assert data["items"] == []
    assert data["subtotal"] == "0.00"
    assert data["total"] == "0.00"


def test_create_order_requires_email(client):
    response = client.post("/checkout/orders", json={})

    assert response.status_code == 422

    data = response.json()

    assert "email" in str(data).lower()


def test_get_order(client):
    order = create_order(client)

    response = client.get(f"/checkout/orders/{order['id']}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == order["id"]
    assert data["status"] == "pending"


def test_get_order_not_found(client):
    response = client.get("/checkout/orders/999")

    assert response.status_code == 404


def test_add_product_to_order(client):
    product = create_product(
        client,
        price=1200.50,
        stock=10,
    )

    order = create_order(client)

    response = add_product_to_order(
        client,
        order["id"],
        product["id"],
        2,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == order["id"]
    assert len(data["items"]) == 1

    item = data["items"][0]

    assert item["product_id"] == product["id"]
    assert item["quantity"] == 2
    assert item["unit_price"] == "1200.50"
    assert item["total_price"] == "2401.00"


def test_add_same_product_increases_quantity(client):
    product = create_product(
        client,
        price=100.00,
        stock=10,
    )

    order = create_order(client)

    response = add_product_to_order(
        client,
        order["id"],
        product["id"],
        2,
    )

    assert response.status_code == 201

    response = add_product_to_order(
        client,
        order["id"],
        product["id"],
        3,
    )

    assert response.status_code == 201

    data = response.json()

    assert len(data["items"]) == 1

    item = data["items"][0]

    assert item["quantity"] == 5
    assert item["unit_price"] == "100.00"
    assert item["total_price"] == "500.00"


def test_add_product_with_insufficient_stock(client):
    product = create_product(
        client,
        stock=2,
    )

    order = create_order(client)

    response = add_product_to_order(
        client,
        order["id"],
        product["id"],
        3,
    )

    assert response.status_code == 400

    data = response.json()

    assert "stock" in data["detail"].lower()


def test_remove_order_item(client):
    product = create_product(
        client,
        stock=10,
    )

    order = create_order(client)

    response = add_product_to_order(
        client,
        order["id"],
        product["id"],
        2,
    )

    assert response.status_code == 201

    data = response.json()
    item_id = data["items"][0]["id"]

    response = client.delete(f"/checkout/orders/{order['id']}/items/{item_id}")

    assert response.status_code == 204

    response = client.get(f"/checkout/orders/{order['id']}")

    assert response.status_code == 200

    data = response.json()

    assert data["items"] == []
    assert data["subtotal"] == "0.00"
    assert data["total"] == "0.00"


def test_decrease_order_item(client):
    product = create_product(
        client,
        price=100.00,
        stock=10,
    )

    order = create_order(client)

    response = add_product_to_order(
        client,
        order["id"],
        product["id"],
        3,
    )

    assert response.status_code == 201

    data = response.json()
    item_id = data["items"][0]["id"]

    response = client.patch(f"/checkout/orders/{order['id']}/items/{item_id}/decrease")

    assert response.status_code == 200

    data = response.json()

    assert data["items"][0]["quantity"] == 2
    assert data["items"][0]["total_price"] == "200.00"


def test_decrease_last_quantity_removes_item(client):
    product = create_product(
        client,
        price=100.00,
        stock=10,
    )

    order = create_order(client)

    response = add_product_to_order(
        client,
        order["id"],
        product["id"],
        1,
    )

    assert response.status_code == 201

    data = response.json()
    item_id = data["items"][0]["id"]

    response = client.patch(f"/checkout/orders/{order['id']}/items/{item_id}/decrease")

    assert response.status_code == 200

    data = response.json()

    assert data["items"] == []
    assert data["subtotal"] == "0.00"
    assert data["total"] == "0.00"


def test_checkout_order(client):
    product = create_product(
        client,
        price=100.00,
        stock=10,
    )

    order = create_order(client)

    response = add_product_to_order(
        client,
        order["id"],
        product["id"],
        2,
    )

    assert response.status_code == 201

    response = client.post(f"/checkout/orders/{order['id']}/checkout")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == order["id"]
    assert data["status"] == "payment_pending"
    assert data["subtotal"] == "200.00"
    assert data["tax"] == "40.00"
    assert data["shipping"] == "0.00"
    assert data["discount"] == "0.00"
    assert data["total"] == "240.00"


def test_checkout_decreases_stock(client):
    product = create_product(
        client,
        stock=10,
    )

    order = create_order(client)

    response = add_product_to_order(
        client,
        order["id"],
        product["id"],
        3,
    )

    assert response.status_code == 201

    response = client.post(f"/checkout/orders/{order['id']}/checkout")

    assert response.status_code == 200

    response = client.get(f"/products/{product['id']}")

    assert response.status_code == 200

    data = response.json()

    assert data["stock"] == 7


def test_checkout_empty_order(client):
    order = create_order(client)

    response = client.post(f"/checkout/orders/{order['id']}/checkout")

    assert response.status_code == 400

    data = response.json()

    assert "empty" in data["detail"].lower()


def test_checkout_fails_when_stock_is_no_longer_available(client, db):
    product = create_product(
        client,
        stock=5,
    )

    order = create_order(client)

    response = add_product_to_order(
        client,
        order["id"],
        product["id"],
        5,
    )

    assert response.status_code == 201

    db_product = db.get(ProductModel, product["id"])
    db_product.stock = 2
    db.commit()

    response = client.post(f"/checkout/orders/{order['id']}/checkout")

    assert response.status_code == 400

    response = client.get(f"/checkout/orders/{order['id']}")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "pending"


def test_cannot_checkout_order_twice(client):
    product = create_product(
        client,
        stock=10,
    )

    order = create_order(client)

    response = add_product_to_order(
        client,
        order["id"],
        product["id"],
        1,
    )

    assert response.status_code == 201

    response = client.post(f"/checkout/orders/{order['id']}/checkout")

    assert response.status_code == 200

    response = client.post(f"/checkout/orders/{order['id']}/checkout")

    assert response.status_code == 400


def test_cannot_modify_completed_order(client):
    product = create_product(
        client,
        stock=10,
    )

    order = create_order(client)

    response = add_product_to_order(
        client,
        order["id"],
        product["id"],
        1,
    )

    assert response.status_code == 201

    response = client.post(f"/checkout/orders/{order['id']}/checkout")
    assert response.status_code == 200

    response = add_product_to_order(
        client,
        order["id"],
        product["id"],
        1,
    )

    assert response.status_code == 400
    assert "processed" in response.json()["detail"].lower()
