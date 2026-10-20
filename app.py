"""
app.py
------
This is the main entry point of our Flask web application.

Flask is a lightweight Python web framework. It handles:
  - Serving HTML pages to the browser (the "views")
  - Providing REST API endpoints that return JSON data
  - Connecting the frontend (HTML/CSS/JS) with the backend database

How it works:
  1. The browser (or JavaScript code) sends an HTTP request to a URL.
  2. Flask matches the URL to a Python function (called a "route").
  3. The function runs, talks to the database, and returns a response.
  4. The browser displays the result.
"""

from flask import Flask, jsonify, request, render_template, abort
from database import get_db_connection, init_db
from datetime import datetime

# Create the Flask application instance
# __name__ tells Flask where to look for templates and static files
app = Flask(__name__)

# ──────────────────────────────────────────────
# Valid expense categories (used for validation)
# ──────────────────────────────────────────────
VALID_CATEGORIES = ["Food", "Transport", "Shopping", "Bills", "Education", "Other"]


# ══════════════════════════════════════════════════════════════
#  PAGE ROUTES — these serve HTML pages to the browser
# ══════════════════════════════════════════════════════════════

@app.route("/")
def dashboard():
    """Serve the Dashboard page (index.html)."""
    return render_template("index.html")


@app.route("/expenses")
def expenses_page():
    """Serve the Manage Expenses page (expenses.html)."""
    return render_template("expenses.html")


@app.route("/add")
def add_expense_page():
    """Serve the Add Expense form page (add_expense.html)."""
    return render_template("add_expense.html")


# ══════════════════════════════════════════════════════════════
#  REST API ROUTES — these return JSON data for JavaScript
# ══════════════════════════════════════════════════════════════

# ── GET /api/expenses ──────────────────────────────────────────
# Returns all expenses, with optional search and filter support.
@app.route("/api/expenses", methods=["GET"])
def get_expenses():
    """
    Retrieve all expenses from the database.

    Supports optional query parameters:
      ?search=coffee        → filters by title containing 'coffee'
      ?category=Food        → filters by category
      ?start_date=2024-01-01 → filters from this date
      ?end_date=2024-01-31   → filters to this date
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Start building a SQL query
    query = "SELECT * FROM expenses WHERE 1=1"
    params = []  # We use parameterized queries to prevent SQL injection

    # Apply optional search filter
    search = request.args.get("search", "").strip()
    if search:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")  # % means "any characters"

    # Apply optional category filter
    category = request.args.get("category", "").strip()
    if category and category in VALID_CATEGORIES:
        query += " AND category = ?"
        params.append(category)

    # Apply optional date range filters
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    # Sort newest first
    query += " ORDER BY date DESC, created_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    # Convert each row to a plain Python dictionary so Flask can turn it into JSON
    expenses = [dict(row) for row in rows]
    return jsonify(expenses), 200


# ── GET /api/expenses/<id> ─────────────────────────────────────
# Returns a single expense by its ID.
@app.route("/api/expenses/<int:expense_id>", methods=["GET"])
def get_expense(expense_id):
    """Retrieve one expense by ID."""
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    conn.close()

    if row is None:
        # 404 means "Not Found"
        return jsonify({"error": f"Expense with ID {expense_id} not found."}), 404

    return jsonify(dict(row)), 200


# ── POST /api/expenses ─────────────────────────────────────────
# Creates a new expense.
@app.route("/api/expenses", methods=["POST"])
def create_expense():
    """
    Add a new expense to the database.

    Expects a JSON body with:
      title, amount, category, date
      description (optional)
    """
    data = request.get_json()  # Parse the JSON body sent from JavaScript

    if not data:
        return jsonify({"error": "No data provided."}), 400

    # ── Validate required fields ──────────────────────────────
    errors = {}

    title = str(data.get("title", "")).strip()
    if not title:
        errors["title"] = "Title is required."

    try:
        amount = float(data.get("amount", 0))
        if amount <= 0:
            errors["amount"] = "Amount must be greater than zero."
    except (ValueError, TypeError):
        errors["amount"] = "Amount must be a valid number."

    category = str(data.get("category", "")).strip()
    if category not in VALID_CATEGORIES:
        errors["category"] = f"Category must be one of: {', '.join(VALID_CATEGORIES)}."

    date = str(data.get("date", "")).strip()
    if not date:
        errors["date"] = "Date is required."
    else:
        try:
            datetime.strptime(date, "%Y-%m-%d")  # Validate date format
        except ValueError:
            errors["date"] = "Date must be in YYYY-MM-DD format."

    description = str(data.get("description", "")).strip()

    # Return all errors at once so the user can fix them all
    if errors:
        return jsonify({"errors": errors}), 422

    # ── Insert into database ───────────────────────────────────
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO expenses (title, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (title, amount, category, date, description)
    )
    conn.commit()
    new_id = cursor.lastrowid  # Get the ID of the newly created row
    conn.close()

    # Return the created expense with 201 Created status
    return get_expense(new_id)[0], 201


# ── PUT /api/expenses/<id> ─────────────────────────────────────
# Updates an existing expense.
@app.route("/api/expenses/<int:expense_id>", methods=["PUT"])
def update_expense(expense_id):
    """Update an existing expense by ID."""
    # First check the expense exists
    conn = get_db_connection()
    existing = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    conn.close()

    if existing is None:
        return jsonify({"error": f"Expense with ID {expense_id} not found."}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided."}), 400

    # ── Validate fields ───────────────────────────────────────
    errors = {}

    title = str(data.get("title", existing["title"])).strip()
    if not title:
        errors["title"] = "Title is required."

    try:
        amount = float(data.get("amount", existing["amount"]))
        if amount <= 0:
            errors["amount"] = "Amount must be greater than zero."
    except (ValueError, TypeError):
        errors["amount"] = "Amount must be a valid number."

    category = str(data.get("category", existing["category"])).strip()
    if category not in VALID_CATEGORIES:
        errors["category"] = f"Category must be one of: {', '.join(VALID_CATEGORIES)}."

    date = str(data.get("date", existing["date"])).strip()
    if not date:
        errors["date"] = "Date is required."
    else:
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            errors["date"] = "Date must be in YYYY-MM-DD format."

    description = str(data.get("description", existing["description"] or "")).strip()

    if errors:
        return jsonify({"errors": errors}), 422

    # ── Update database ────────────────────────────────────────
    conn = get_db_connection()
    conn.execute(
        "UPDATE expenses SET title=?, amount=?, category=?, date=?, description=? WHERE id=?",
        (title, amount, category, date, description, expense_id)
    )
    conn.commit()
    conn.close()

    return get_expense(expense_id)[0], 200


# ── DELETE /api/expenses/<id> ──────────────────────────────────
# Deletes an expense.
@app.route("/api/expenses/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    """Delete an expense by ID."""
    conn = get_db_connection()
    existing = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()

    if existing is None:
        conn.close()
        return jsonify({"error": f"Expense with ID {expense_id} not found."}), 404

    conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()

    # 200 OK with a success message
    return jsonify({"message": f"Expense '{existing['title']}' deleted successfully."}), 200


# ── GET /api/summary ───────────────────────────────────────────
# Returns spending summaries and statistics.
@app.route("/api/summary", methods=["GET"])
def get_summary():
    """
    Returns an overview of spending:
      - Total amount spent
      - Total number of expenses
      - Amount spent this month
      - Breakdown of spending by category
      - Monthly totals for the last 12 months
    """
    conn = get_db_connection()

    # Total spending and count
    totals = conn.execute(
        "SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total FROM expenses"
    ).fetchone()

    # This month's spending
    current_month = datetime.now().strftime("%Y-%m")
    month_total = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) as total FROM expenses WHERE date LIKE ?",
        (f"{current_month}%",)
    ).fetchone()

    # Spending by category
    by_category = conn.execute(
        """SELECT category,
                  COUNT(*) as count,
                  SUM(amount) as total
           FROM expenses
           GROUP BY category
           ORDER BY total DESC"""
    ).fetchall()

    # Monthly totals (last 12 months)
    monthly = conn.execute(
        """SELECT strftime('%Y-%m', date) as month,
                  SUM(amount) as total
           FROM expenses
           GROUP BY month
           ORDER BY month DESC
           LIMIT 12"""
    ).fetchall()

    # Recent expenses (last 5)
    recent = conn.execute(
        "SELECT * FROM expenses ORDER BY date DESC, created_at DESC LIMIT 5"
    ).fetchall()

    conn.close()

    return jsonify({
        "total_amount":  round(totals["total"], 2),
        "total_count":   totals["count"],
        "month_total":   round(month_total["total"], 2),
        "by_category":   [dict(r) for r in by_category],
        "monthly":       [dict(r) for r in monthly],
        "recent":        [dict(r) for r in recent]
    }), 200


# ══════════════════════════════════════════════════════════════
#  Start the application
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    import os

    # Allow custom port via CLI argument (e.g. python app.py 5001 or --port 5001)
    # or via environment variable PORT, defaulting to 5001
    port = 5001
    if len(sys.argv) > 1:
        for idx, arg in enumerate(sys.argv[1:]):
            if arg in ("--port", "-p") and idx + 1 < len(sys.argv[1:]):
                try:
                    port = int(sys.argv[idx + 2])
                except ValueError:
                    pass
            elif arg.isdigit():
                port = int(arg)
    elif os.environ.get("PORT"):
        try:
            port = int(os.environ.get("PORT"))
        except ValueError:
            pass

    init_db()   # Make sure the database and table exist
    print("[START] Starting Personal Expense Tracker...")
    print(f"[URL]   Open your browser and go to: http://127.0.0.1:{port}")
    app.run(debug=True, port=port)
