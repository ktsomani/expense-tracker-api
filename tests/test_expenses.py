def new_expense(**overrides):
    body = {"description": "Coffee", "amount_cents": 450, "category": "Food"}
    body.update(overrides)
    return body


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_create_returns_201_and_normalises_category(client):
    r = client.post("/expenses", json=new_expense(category="  FOOD  "))
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1
    assert body["category"] == "food"
    assert body["amount_cents"] == 450
    assert body["created_on"]


def test_get_existing_expense(client):
    client.post("/expenses", json=new_expense())
    r = client.get("/expenses/1")
    assert r.status_code == 200
    assert r.json()["description"] == "Coffee"


def test_get_missing_expense_returns_404(client):
    r = client.get("/expenses/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Expense not found"


def test_list_filters_by_category(client):
    client.post("/expenses", json=new_expense(category="food"))
    client.post("/expenses", json=new_expense(category="travel", description="Train"))
    client.post("/expenses", json=new_expense(category="food", description="Lunch"))

    assert len(client.get("/expenses").json()) == 3
    food = client.get("/expenses", params={"category": "Food"}).json()
    assert [e["description"] for e in food] == ["Coffee", "Lunch"]


def test_delete_then_get_returns_404(client):
    client.post("/expenses", json=new_expense())
    assert client.delete("/expenses/1").status_code == 204
    assert client.get("/expenses/1").status_code == 404


def test_delete_missing_returns_404(client):
    assert client.delete("/expenses/42").status_code == 404


def test_summary_totals_by_category(client):
    client.post("/expenses", json=new_expense(category="food", amount_cents=500))
    client.post("/expenses", json=new_expense(category="food", amount_cents=300))
    client.post("/expenses", json=new_expense(category="travel", amount_cents=2000))

    r = client.get("/reports/summary").json()
    assert r["grand_total_cents"] == 2800
    assert r["categories"][0] == {"category": "travel", "count": 1, "total_cents": 2000}
    assert r["categories"][1] == {"category": "food", "count": 2, "total_cents": 800}


def test_summary_empty_database(client):
    assert client.get("/reports/summary").json() == {"categories": [], "grand_total_cents": 0}


def test_rejects_zero_amount(client):
    assert client.post("/expenses", json=new_expense(amount_cents=0)).status_code == 422


def test_rejects_negative_amount(client):
    assert client.post("/expenses", json=new_expense(amount_cents=-100)).status_code == 422


def test_rejects_blank_description(client):
    assert client.post("/expenses", json=new_expense(description="   ")).status_code == 422


def test_rejects_missing_category(client):
    body = new_expense()
    del body["category"]
    assert client.post("/expenses", json=body).status_code == 422
