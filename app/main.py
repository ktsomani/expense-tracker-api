import os
import sqlite3
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from app.db import connect, transaction

app = FastAPI(title="Expense Tracker API", version="1.0.0")


def get_db():
    conn = connect(os.getenv("EXPENSE_DB", "expenses.db"))
    try:
        yield conn
    finally:
        conn.close()


class ExpenseIn(BaseModel):
    description: str = Field(min_length=1, max_length=200)
    amount_cents: int = Field(gt=0, description="Amount in cents, e.g. 1250 for 12.50")
    category: str = Field(min_length=1, max_length=50)

    @field_validator("description", "category")
    @classmethod
    def not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class Expense(ExpenseIn):
    id: int
    created_on: str


def _row_to_expense(row: sqlite3.Row) -> Expense:
    return Expense(**dict(row))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/expenses", status_code=201, response_model=Expense)
def create_expense(payload: ExpenseIn, db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        cur = db.execute(
            "INSERT INTO expenses (description, amount_cents, category) VALUES (?, ?, ?)",
            (payload.description, payload.amount_cents, payload.category.lower()),
        )
    row = db.execute("SELECT * FROM expenses WHERE id = ?", (cur.lastrowid,)).fetchone()
    return _row_to_expense(row)


@app.get("/expenses", response_model=list[Expense])
def list_expenses(
    category: Optional[str] = Query(default=None),
    db: sqlite3.Connection = Depends(get_db),
):
    if category:
        rows = db.execute(
            "SELECT * FROM expenses WHERE category = ? ORDER BY id", (category.strip().lower(),)
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM expenses ORDER BY id").fetchall()
    return [_row_to_expense(r) for r in rows]


@app.get("/expenses/{expense_id}", response_model=Expense)
def get_expense(expense_id: int, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return _row_to_expense(row)


@app.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: int, db: sqlite3.Connection = Depends(get_db)):
    with transaction(db):
        cur = db.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Expense not found")


@app.get("/reports/summary")
def summary(db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute(
        """
        SELECT category, COUNT(*) AS count, SUM(amount_cents) AS total_cents
        FROM expenses
        GROUP BY category
        ORDER BY total_cents DESC
        """
    ).fetchall()
    return {
        "categories": [dict(r) for r in rows],
        "grand_total_cents": sum(r["total_cents"] for r in rows),
    }
