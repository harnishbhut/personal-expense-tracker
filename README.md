# 💰 Personal Expense Tracker

A full-stack web application for tracking your daily expenses.  
Built with **Python + Flask** (backend), **SQLite** (database), and **HTML/CSS/JavaScript** (frontend).

---

## 📁 Project Structure

```
personal-expense-tracker/
├── app.py            ← Flask application + all REST API routes
├── database.py       ← Database setup and connection helper
├── requirements.txt  ← Python packages needed
├── expenses.db       ← SQLite database (created automatically)
│
├── templates/
│   ├── index.html        ← Dashboard page
│   ├── add_expense.html  ← Add Expense form page
│   └── expenses.html     ← View / Edit / Delete all expenses
│
├── static/
│   ├── style.css   ← All styling (dark theme, cards, layout)
│   └── script.js   ← Shared JavaScript (API calls, helpers)
│
├── tests/
│   └── test_app.py ← Automated tests for the REST API
│
├── .gitignore
└── README.md
```

---

## 🚀 Getting Started

### Step 1 — Install Python
Make sure Python 3.9 or newer is installed.  
Download it from: https://www.python.org/downloads/

Verify: `python --version`

---

### Step 2 — Create and Activate a Virtual Environment

A virtual environment keeps your project's packages isolated from other Python projects on your computer.

```bash
# Create the virtual environment (only do this once)
python -m venv venv

# Activate it on Windows (PowerShell)
venv\Scripts\Activate.ps1

# Activate it on Mac / Linux
source venv/bin/activate
```

You'll see `(venv)` appear at the start of your terminal prompt.

---

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

This installs Flask (the web framework).

---

### Step 4 — Run the Application

```bash
python app.py
```

The first time it runs, it automatically creates `expenses.db` and the `expenses` table.

You'll see:
```
✅ Database initialized — expenses.db is ready.
🚀 Starting Personal Expense Tracker...
🌐 Open your browser and go to: http://127.0.0.1:5000
```

---

### Step 5 — Open the App

Open your browser and go to: **http://127.0.0.1:5000**

---

## 🧪 Running the Tests

Make sure the virtual environment is active, then run:

```bash
# Using pytest (recommended)
pip install pytest
python -m pytest tests/ -v

# Using unittest (built-in, no extra install needed)
python -m unittest discover tests -v
```

You should see all tests listed as `PASSED`.

---

## 🌐 REST API Reference

All API endpoints return **JSON**.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/expenses` | Get all expenses |
| `GET`  | `/api/expenses/<id>` | Get one expense |
| `POST` | `/api/expenses` | Create a new expense |
| `PUT`  | `/api/expenses/<id>` | Update an expense |
| `DELETE` | `/api/expenses/<id>` | Delete an expense |
| `GET`  | `/api/summary` | Get spending summary |

### Filter Options for `GET /api/expenses`

Add query parameters to the URL:

```
GET /api/expenses?search=coffee
GET /api/expenses?category=Food
GET /api/expenses?start_date=2024-01-01&end_date=2024-01-31
```

### POST / PUT Body Example

```json
{
  "title":       "Morning Coffee",
  "amount":      3.50,
  "category":    "Food",
  "date":        "2024-03-15",
  "description": "Latte from the cafe"
}
```

Valid categories: `Food`, `Transport`, `Shopping`, `Bills`, `Education`, `Other`

### Test the API with curl

```bash
# Get all expenses
curl http://127.0.0.1:5000/api/expenses

# Add a new expense
curl -X POST http://127.0.0.1:5000/api/expenses \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Lunch\",\"amount\":12.50,\"category\":\"Food\",\"date\":\"2024-03-15\"}"

# Get summary
curl http://127.0.0.1:5000/api/summary
```

---

## 🛠️ Git Version Control

```bash
# Initialise a new git repository
git init

# Add all project files (respects .gitignore)
git add .

# Create the first commit
git commit -m "Initial commit: Personal Expense Tracker"
```

---

## 🧰 Technology Breakdown

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | Python + Flask | Handles HTTP requests and business logic |
| Database | SQLite | Stores expense records in a local file |
| API | Flask routes | Returns JSON data to the frontend |
| Frontend | HTML | Page structure |
| Styling | CSS | Visual design, layout, dark theme |
| Interactivity | JavaScript (vanilla) | Fetches data, updates the page without reloading |
| Testing | Python unittest / pytest | Automated API tests |

---

## 💡 How It All Works Together

```
Browser (HTML/CSS/JS)
        │
        │  HTTP Requests (GET, POST, PUT, DELETE)
        ▼
Flask (app.py)  ←→  SQLite (expenses.db via database.py)
        │
        │  JSON Responses
        ▼
Browser (JavaScript updates the page)
```

1. The browser sends an HTTP request to a Flask route (e.g. `POST /api/expenses`).
2. Flask validates the data and runs a SQL query against the SQLite database.
3. Flask returns a JSON response (success data or error message).
4. JavaScript receives the JSON and updates what the user sees — without reloading the page.
