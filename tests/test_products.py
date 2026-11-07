from fastapi import status


def test_create_product(client):
    response = client.post(
        "/products/",
        json={
            "name": "Gaming Laptop",
            "price": 1200.55,
            "stock": 10,
        },
    )

    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()

    assert data["name"] == "Gaming Laptop"
    assert data["price"] == "1200.55"
    assert data["stock"] == 10
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_get_product_not_found(client):
    response = client.get("/products/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Product 999 not found"}


def test_get_product(client):
    create_response = client.post(
        "/products/",
        json={
            "name": "Gaming Laptop",
            "price": 1200.55,
            "stock": 10,
        },
    )

    product_id = create_response.json()["id"]

    response = client.get(f"/products/{product_id}")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["id"] == product_id
    assert data["name"] == "Gaming Laptop"
    assert data["price"] == "1200.55"
    assert data["stock"] == 10


def test_update_product(client):
    create_response = client.post(
        "/products/",
        json={
            "name": "Gaming Laptop",
            "price": 1200.55,
            "stock": 10,
        },
    )

    product_id = create_response.json()["id"]

    response = client.patch(
        f"/products/{product_id}",
        json={
            "price": 999.99,
            "stock": 5,
        },
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["id"] == product_id
    assert data["name"] == "Gaming Laptop"
    assert data["price"] == "999.99"
    assert data["stock"] == 5


def test_delete_product(client):
    create_response = client.post(
        "/products/",
        json={
            "name": "Gaming Laptop",
            "price": 1200.55,
            "stock": 10,
        },
    )

    product_id = create_response.json()["id"]

    response = client.delete(f"/products/{product_id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    get_response = client.get(f"/products/{product_id}")

    assert get_response.status_code == status.HTTP_404_NOT_FOUND
