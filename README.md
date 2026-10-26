# Expense Tracker API

A REST API for recording and summarising expenses, built with FastAPI and
SQLite. Includes pytest tests and a GitHub Actions workflow that runs them on
every push.

## Endpoints

| Method | Path                  | Purpose                              |
|--------|-----------------------|--------------------------------------|
| GET    | /health               | Liveness check                       |
| POST   | /expenses             | Create an expense (returns 201)      |
| GET    | /expenses             | List expenses, optional `?category=` |
| GET    | /expenses/{id}        | Get one expense (404 if missing)     |
| DELETE | /expenses/{id}        | Delete an expense (204 or 404)       |
| GET    | /reports/summary      | Totals per category and overall      |

Amounts are stored in cents (`1250` = 12.50) to avoid floating-point errors.

## Run locally

```bash
pip install -r requirements-dev.txt
uvicorn app.main:app --reload     # docs at http://127.0.0.1:8000/docs
pytest -v
```

The database file defaults to `expenses.db`. Set `EXPENSE_DB` to change it.

## Example

```bash
curl -X POST http://127.0.0.1:8000/expenses \
  -H "Content-Type: application/json" \
  -d '{"description": "Coffee", "amount_cents": 450, "category": "food"}'
```

## Design decisions

- **Validation at the edge.** Pydantic rejects bad input with a 422 before it
  reaches the database. A CHECK constraint in SQLite is a second safety net.
- **Parameterised SQL only.** All queries use `?` placeholders, which prevents SQL injection.
- **Each request gets its own connection,** closed when the request finishes.
- **Integer money.** Storing cents avoids rounding errors.

## Tests

Tests use a temporary database per test, so they never touch real data. They
cover the happy path, 404s, filtering, the summary report, and input validation.

## How this was built

_Describe your process here: which AI coding tool you used, one prompt that
worked, and one time the output was wrong and how you caught it. Delete this
section if it is not true._
