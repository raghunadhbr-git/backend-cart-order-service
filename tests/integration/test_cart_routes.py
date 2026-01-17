def test_cart_empty(client):
    res = client.get("/api/cart/")
    assert res.status_code in (200, 401)
