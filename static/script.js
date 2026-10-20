/**
 * script.js
 * ---------
 * Shared JavaScript utilities used across all pages.
 *
 * JavaScript runs in the browser and is responsible for:
 *   - Fetching data from our Flask API (without reloading the page)
 *   - Building HTML tables and cards dynamically
 *   - Handling user interactions (clicks, form submissions)
 *   - Showing/hiding elements and modals
 *
 * We use the built-in `fetch()` function to talk to our REST API.
 * It sends HTTP requests (GET, POST, PUT, DELETE) and handles
 * the JSON responses.
 */

'use strict';

// ─────────────────────────────────────────────────────────────
//  CONSTANTS
// ─────────────────────────────────────────────────────────────

/** All valid expense categories */
const CATEGORIES = ['Food', 'Transport', 'Shopping', 'Bills', 'Education', 'Other'];

/** Emoji icons for each category */
const CATEGORY_ICONS = {
  Food:       '🍔',
  Transport:  '🚗',
  Shopping:   '🛍️',
  Bills:      '⚡',
  Education:  '📚',
  Other:      '📦',
};

/** Bar chart colours for each category */
const CATEGORY_COLORS = {
  Food:       '#f97316',
  Transport:  '#3b82f6',
  Shopping:   '#ec4899',
  Bills:      '#f59e0b',
  Education:  '#10b981',
  Other:      '#8b5cf6',
};

// ─────────────────────────────────────────────────────────────
//  HELPER FUNCTIONS
// ─────────────────────────────────────────────────────────────

/**
 * Format a number as currency.
 * e.g. formatCurrency(1234.5) → "$1,234.50"
 */
function formatCurrency(amount) {
  return new Intl.NumberFormat('en-US', {
    style:    'currency',
    currency: 'USD',
  }).format(amount);
}

/**
 * Format a date string (YYYY-MM-DD) to a human-readable format.
 * e.g. formatDate("2024-03-15") → "Mar 15, 2024"
 */
function formatDate(dateStr) {
  if (!dateStr) return '—';
  // Add time to avoid timezone shifting the date
  const date = new Date(dateStr + 'T00:00:00');
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

/**
 * Build a category badge HTML string.
 * e.g. makeBadge("Food") → '<span class="badge badge-Food">🍔 Food</span>'
 */
function makeBadge(category) {
  const icon = CATEGORY_ICONS[category] || '📦';
  return `<span class="badge badge-${category}">${icon} ${category}</span>`;
}

/**
 * Show a toast-style alert inside an element.
 * @param {string} elementId - The ID of the alert <div>
 * @param {string} message   - The text to display
 * @param {string} type      - 'success' or 'error'
 */
function showAlert(elementId, message, type = 'success') {
  const el = document.getElementById(elementId);
  if (!el) return;

  const icon = type === 'success' ? '✅' : '❌';
  el.innerHTML = `${icon} ${message}`;
  el.className = `alert alert-${type} visible`;

  // Auto-hide after 4 seconds
  setTimeout(() => {
    el.className = `alert`;
  }, 4000);
}

/**
 * Show a loading spinner inside a container element.
 */
function showLoading(containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = `
    <div class="loading-container">
      <div class="spinner"></div>
      <span>Loading…</span>
    </div>`;
}

/**
 * Show an empty state message inside a container element.
 */
function showEmpty(containerId, message = 'No expenses found.') {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">🗂️</div>
      <h3>Nothing here yet</h3>
      <p>${message}</p>
      <a href="/add" class="btn btn-primary">➕ Add First Expense</a>
    </div>`;
}

// ─────────────────────────────────────────────────────────────
//  API FUNCTIONS
//  Each function sends an HTTP request to a Flask API endpoint
//  and returns the JSON result as a JavaScript object.
// ─────────────────────────────────────────────────────────────

/**
 * Fetch all expenses (with optional filters).
 * @param {Object} filters - e.g. { search: 'coffee', category: 'Food' }
 */
async function fetchExpenses(filters = {}) {
  // Build a query string from the filters object
  // e.g. { search: 'coffee' } → "?search=coffee"
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.append(key, value);
  });

  const url = '/api/expenses' + (params.toString() ? '?' + params.toString() : '');
  const response = await fetch(url);

  if (!response.ok) throw new Error('Failed to load expenses.');
  return response.json();
}

/**
 * Fetch a single expense by ID.
 */
async function fetchExpense(id) {
  const response = await fetch(`/api/expenses/${id}`);
  if (!response.ok) throw new Error('Expense not found.');
  return response.json();
}

/**
 * Fetch the summary statistics from the API.
 */
async function fetchSummary() {
  const response = await fetch('/api/summary');
  if (!response.ok) throw new Error('Failed to load summary.');
  return response.json();
}

/**
 * Create a new expense via POST request.
 * @param {Object} data - The expense fields
 */
async function createExpense(data) {
  const response = await fetch('/api/expenses', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(data),
  });
  const result = await response.json();
  // Return both the HTTP status and the parsed JSON body
  return { ok: response.ok, status: response.status, data: result };
}

/**
 * Update an existing expense via PUT request.
 */
async function updateExpense(id, data) {
  const response = await fetch(`/api/expenses/${id}`, {
    method:  'PUT',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(data),
  });
  const result = await response.json();
  return { ok: response.ok, status: response.status, data: result };
}

/**
 * Delete an expense via DELETE request.
 */
async function deleteExpense(id) {
  const response = await fetch(`/api/expenses/${id}`, { method: 'DELETE' });
  const result = await response.json();
  return { ok: response.ok, data: result };
}

// ─────────────────────────────────────────────────────────────
//  SIDEBAR / MOBILE MENU
// ─────────────────────────────────────────────────────────────

/**
 * Set up mobile sidebar toggle and highlight the active nav link.
 * Called once when the DOM is ready.
 */
function initSidebar() {
  // Highlight the correct nav item based on the current URL
  const path = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(item => {
    const href = item.getAttribute('href') || item.dataset.href;
    if (href && (path === href || (href !== '/' && path.startsWith(href)))) {
      item.classList.add('active');
    }
  });

  // Mobile menu toggle
  const toggle = document.getElementById('menuToggle');
  const sidebar = document.getElementById('sidebar');
  if (toggle && sidebar) {
    toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
    // Close sidebar when clicking outside of it on mobile
    document.addEventListener('click', e => {
      if (!sidebar.contains(e.target) && e.target !== toggle) {
        sidebar.classList.remove('open');
      }
    });
  }
}

// Run initSidebar when the page is fully loaded
document.addEventListener('DOMContentLoaded', initSidebar);
