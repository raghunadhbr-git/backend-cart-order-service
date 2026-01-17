def test_checkout_requires_auth(client):
    res = client.post("/api/checkout/", json={
        "contact": "9999999999",
        "address": "Test",
        "total_price": 100
    })
    assert res.status_code == 401
