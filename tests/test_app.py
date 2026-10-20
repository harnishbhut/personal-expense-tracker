"""
tests/test_app.py
-----------------
Automated tests for the Personal Expense Tracker REST API.

We use Python's built-in 'unittest' module together with
Flask's built-in test client.

The test client lets us send fake HTTP requests to our Flask
app without actually starting a server — it's faster and more
reliable for testing.

How to run these tests:
    python -m pytest tests/ -v
or:
    python -m unittest discover tests
"""

import unittest
import json
import sys
import os
import tempfile

# Add the parent directory to the Python path so we can import app.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
import database


class TestExpenseTracker(unittest.TestCase):
    """
    Test suite for the Expense Tracker REST API.

    setUp()    runs before EACH test — creates a fresh temporary database file.
    tearDown() runs after  EACH test — deletes the temporary file.

    WHY A TEMP FILE AND NOT ':memory:'?
    SQLite's ':memory:' creates a brand-new empty database for every call to
    sqlite3.connect(). That means the table created by init_db() disappears the
    moment that connection is closed, so all subsequent queries fail with
    "no such table". A real (temporary) file persists across connections.
    """

    def setUp(self):
        """Create a temporary SQLite file and wire up the Flask test client."""
        app.config['TESTING'] = True
        self.client = app.test_client()

        # Create a named temp file; delete=False so we can reopen it later
        self._db_fd, self._db_path = tempfile.mkstemp(suffix='.db')
        os.close(self._db_fd)   # close the raw file descriptor

        # Save the real DB path and point the database module at our temp file
        self._orig_db = database.DATABASE
        database.DATABASE = self._db_path
        database.init_db()   # creates the 'expenses' table in the temp file

    def tearDown(self):
        """Restore original DB path and remove the temporary database file."""
        database.DATABASE = self._orig_db
        try:
            os.unlink(self._db_path)
        except OSError:
            pass

    # ── Helper ────────────────────────────────────────────────
    def _create_expense(self, **kwargs):
        """
        Helper method to POST a new expense and return the response.
        Defaults are provided so tests only need to override what matters.
        """
        payload = {
            'title':       'Test Coffee',
            'amount':      3.50,
            'category':    'Food',
            'date':        '2024-03-15',
            'description': 'Morning coffee',
        }
        payload.update(kwargs)

        return self.client.post(
            '/api/expenses',
            data=json.dumps(payload),
            content_type='application/json'
        )

    # ══════════════════════════════════════════════════════════
    #  TEST: CREATE (POST /api/expenses)
    # ══════════════════════════════════════════════════════════

    def test_create_expense_success(self):
        """A valid expense should be created and return 201."""
        resp = self._create_expense()
        self.assertEqual(resp.status_code, 201)

        data = json.loads(resp.data)
        self.assertEqual(data['title'],    'Test Coffee')
        self.assertEqual(data['amount'],   3.50)
        self.assertEqual(data['category'], 'Food')
        self.assertEqual(data['date'],     '2024-03-15')
        self.assertIn('id', data)          # The new row should have an ID

    def test_create_expense_missing_title(self):
        """Missing title should return 422 Unprocessable Entity."""
        resp = self._create_expense(title='')
        self.assertEqual(resp.status_code, 422)
        data = json.loads(resp.data)
        self.assertIn('errors', data)
        self.assertIn('title', data['errors'])

    def test_create_expense_invalid_amount_zero(self):
        """Amount of zero should fail validation."""
        resp = self._create_expense(amount=0)
        self.assertEqual(resp.status_code, 422)
        data = json.loads(resp.data)
        self.assertIn('amount', data['errors'])

    def test_create_expense_invalid_amount_negative(self):
        """Negative amount should fail validation."""
        resp = self._create_expense(amount=-10)
        self.assertEqual(resp.status_code, 422)
        data = json.loads(resp.data)
        self.assertIn('amount', data['errors'])

    def test_create_expense_invalid_category(self):
        """An unrecognised category should fail validation."""
        resp = self._create_expense(category='Gambling')
        self.assertEqual(resp.status_code, 422)
        data = json.loads(resp.data)
        self.assertIn('category', data['errors'])

    def test_create_expense_missing_date(self):
        """Missing date should fail validation."""
        resp = self._create_expense(date='')
        self.assertEqual(resp.status_code, 422)

    # ══════════════════════════════════════════════════════════
    #  TEST: READ (GET /api/expenses  and  GET /api/expenses/<id>)
    # ══════════════════════════════════════════════════════════

    def test_get_all_expenses_empty(self):
        """GET /api/expenses on an empty database should return an empty list."""
        resp = self.client.get('/api/expenses')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 0)

    def test_get_all_expenses_returns_created(self):
        """After creating an expense, GET /api/expenses should include it."""
        self._create_expense(title='Lunch')
        self._create_expense(title='Bus ticket', category='Transport', amount=2.00)

        resp = self.client.get('/api/expenses')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(len(data), 2)

    def test_get_single_expense(self):
        """GET /api/expenses/<id> should return the correct expense."""
        create_resp = self._create_expense(title='Unique Item')
        created_id  = json.loads(create_resp.data)['id']

        resp = self.client.get(f'/api/expenses/{created_id}')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data['title'], 'Unique Item')

    def test_get_nonexistent_expense(self):
        """GET /api/expenses/9999 (no such ID) should return 404."""
        resp = self.client.get('/api/expenses/9999')
        self.assertEqual(resp.status_code, 404)
        data = json.loads(resp.data)
        self.assertIn('error', data)

    # ══════════════════════════════════════════════════════════
    #  TEST: UPDATE (PUT /api/expenses/<id>)
    # ══════════════════════════════════════════════════════════

    def test_update_expense_success(self):
        """A valid PUT request should update the expense and return 200."""
        create_resp = self._create_expense(title='Old Title', amount=10.00)
        expense_id  = json.loads(create_resp.data)['id']

        resp = self.client.put(
            f'/api/expenses/{expense_id}',
            data=json.dumps({
                'title':    'New Title',
                'amount':   25.00,
                'category': 'Shopping',
                'date':     '2024-04-01',
            }),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data['title'],  'New Title')
        self.assertEqual(data['amount'], 25.00)

    def test_update_nonexistent_expense(self):
        """PUT on a non-existent ID should return 404."""
        resp = self.client.put(
            '/api/expenses/9999',
            data=json.dumps({'title': 'X', 'amount': 1, 'category': 'Food', 'date': '2024-01-01'}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 404)

    # ══════════════════════════════════════════════════════════
    #  TEST: DELETE (DELETE /api/expenses/<id>)
    # ══════════════════════════════════════════════════════════

    def test_delete_expense_success(self):
        """Deleting an existing expense should return 200."""
        create_resp = self._create_expense()
        expense_id  = json.loads(create_resp.data)['id']

        resp = self.client.delete(f'/api/expenses/{expense_id}')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIn('message', data)

        # Verify the expense is really gone
        check_resp = self.client.get(f'/api/expenses/{expense_id}')
        self.assertEqual(check_resp.status_code, 404)

    def test_delete_nonexistent_expense(self):
        """Deleting a non-existent expense should return 404."""
        resp = self.client.delete('/api/expenses/9999')
        self.assertEqual(resp.status_code, 404)

    # ══════════════════════════════════════════════════════════
    #  TEST: SEARCH & FILTER
    # ══════════════════════════════════════════════════════════

    def test_search_by_title(self):
        """Search should only return expenses whose title matches."""
        self._create_expense(title='Morning Coffee')
        self._create_expense(title='Bus Ticket', category='Transport', amount=2.0)

        resp = self.client.get('/api/expenses?search=coffee')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], 'Morning Coffee')

    def test_filter_by_category(self):
        """Category filter should only return matching expenses."""
        self._create_expense(title='Lunch',   category='Food',      amount=12.00)
        self._create_expense(title='Bus',     category='Transport', amount=2.00)
        self._create_expense(title='Dinner',  category='Food',      amount=20.00)

        resp = self.client.get('/api/expenses?category=Food')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 2)
        self.assertTrue(all(e['category'] == 'Food' for e in data))

    # ══════════════════════════════════════════════════════════
    #  TEST: SUMMARY
    # ══════════════════════════════════════════════════════════

    def test_summary_empty(self):
        """Summary on empty database should return zeros."""
        resp = self.client.get('/api/summary')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data['total_amount'], 0)
        self.assertEqual(data['total_count'],  0)

    def test_summary_with_expenses(self):
        """Summary should correctly calculate totals."""
        self._create_expense(title='A', amount=10.00, category='Food')
        self._create_expense(title='B', amount=20.00, category='Food')
        self._create_expense(title='C', amount=15.00, category='Transport')

        resp = self.client.get('/api/summary')
        data = json.loads(resp.data)
        self.assertEqual(data['total_count'],  3)
        self.assertAlmostEqual(data['total_amount'], 45.00, places=2)
        self.assertEqual(len(data['by_category']), 2)

    # ══════════════════════════════════════════════════════════
    #  TEST: PAGE ROUTES (HTML pages)
    # ══════════════════════════════════════════════════════════

    def test_dashboard_page_loads(self):
        """The dashboard (/) should return HTTP 200."""
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)

    def test_add_expense_page_loads(self):
        """/add should return HTTP 200."""
        resp = self.client.get('/add')
        self.assertEqual(resp.status_code, 200)

    def test_expenses_page_loads(self):
        """/expenses should return HTTP 200."""
        resp = self.client.get('/expenses')
        self.assertEqual(resp.status_code, 200)


# Run with: python -m pytest tests/ -v
if __name__ == '__main__':
    unittest.main(verbosity=2)
