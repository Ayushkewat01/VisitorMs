"""
Apartment Visitor Management System
=====================================
Main Flask Application File
Author: Antigravity AI
Description: Handles all backend routes, database operations, and authentication
"""

import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, make_response
import sqlite3
import csv
import io
from datetime import datetime, date
from functools import wraps

# ─────────────────────────────────────────────
# App Configuration
# ─────────────────────────────────────────────
# Use __file__ so Flask finds templates/static even if launched from a different cwd
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__,
            template_folder=os.path.join(_BASE_DIR, 'templates'),
            static_folder=os.path.join(_BASE_DIR, 'static'))
app.secret_key = 'visitor_mgmt_secret_2024'  # Change this in production!

DATABASE = 'visitors.db'

# Default admin credentials (in production, store hashed passwords in DB)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'


# ─────────────────────────────────────────────
# Database Helper Functions
# ─────────────────────────────────────────────

def get_db_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn


def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create visitors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS visitors (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            phone       TEXT    NOT NULL,
            purpose     TEXT    NOT NULL,
            flat_number TEXT    NOT NULL,
            check_in    TEXT    NOT NULL,
            check_out   TEXT,
            status      TEXT    DEFAULT 'Inside',
            created_at  TEXT    DEFAULT (datetime('now', 'localtime'))
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully.")


# ─────────────────────────────────────────────
# Authentication Decorator
# ─────────────────────────────────────────────

def login_required(f):
    """Decorator to protect routes that require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ─────────────────────────────────────────────
# Authentication Routes
# ─────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle admin login."""
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            flash('Welcome back, Admin! 👋', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Handle admin logout."""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


# ─────────────────────────────────────────────
# Dashboard Route
# ─────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    """Display dashboard with statistics."""
    conn = get_db_connection()

    # Total visitors ever
    total_visitors = conn.execute('SELECT COUNT(*) FROM visitors').fetchone()[0]

    # Today's visitors
    today = date.today().strftime('%Y-%m-%d')
    today_visitors = conn.execute(
        "SELECT COUNT(*) FROM visitors WHERE check_in LIKE ?", (f'{today}%',)
    ).fetchone()[0]

    # Currently inside (not checked out)
    currently_inside = conn.execute(
        "SELECT COUNT(*) FROM visitors WHERE status = 'Inside'"
    ).fetchone()[0]

    # Total exited
    total_exited = conn.execute(
        "SELECT COUNT(*) FROM visitors WHERE status = 'Exited'"
    ).fetchone()[0]

    # Recent 5 visitors
    recent_visitors = conn.execute(
        'SELECT * FROM visitors ORDER BY id DESC LIMIT 5'
    ).fetchall()

    conn.close()

    return render_template(
        'dashboard.html',
        total_visitors=total_visitors,
        today_visitors=today_visitors,
        currently_inside=currently_inside,
        total_exited=total_exited,
        recent_visitors=recent_visitors
    )


# ─────────────────────────────────────────────
# Visitor Routes (CRUD)
# ─────────────────────────────────────────────

@app.route('/')
@login_required
def index():
    """Main page to display all visitors with search/filter."""
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()

    conn = get_db_connection()
    query = 'SELECT * FROM visitors WHERE 1=1'
    params = []

    # Search by name, phone, or flat number
    if search:
        query += ' AND (name LIKE ? OR phone LIKE ? OR flat_number LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])

    # Filter by status
    if status_filter in ('Inside', 'Exited'):
        query += ' AND status = ?'
        params.append(status_filter)

    query += ' ORDER BY id DESC'
    visitors = conn.execute(query, params).fetchall()
    conn.close()

    return render_template('index.html', visitors=visitors, search=search, status_filter=status_filter)


@app.route('/add', methods=['POST'])
@login_required
def add_visitor():
    """Add a new visitor entry."""
    name        = request.form.get('name', '').strip()
    phone       = request.form.get('phone', '').strip()
    purpose     = request.form.get('purpose', '').strip()
    flat_number = request.form.get('flat_number', '').strip()
    check_in    = request.form.get('check_in', '').strip()

    # Basic server-side validation
    if not all([name, phone, purpose, flat_number, check_in]):
        flash('All fields are required!', 'danger')
        return redirect(url_for('index'))

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO visitors (name, phone, purpose, flat_number, check_in, status) VALUES (?, ?, ?, ?, ?, ?)',
        (name, phone, purpose, flat_number, check_in, 'Inside')
    )
    conn.commit()
    conn.close()

    flash(f'Visitor "{name}" has been added successfully! ✅', 'success')
    return redirect(url_for('index'))


@app.route('/checkout/<int:visitor_id>')
@login_required
def checkout(visitor_id):
    """Mark a visitor as checked out."""
    check_out_time = datetime.now().strftime('%Y-%m-%d %H:%M')

    conn = get_db_connection()
    visitor = conn.execute('SELECT * FROM visitors WHERE id = ?', (visitor_id,)).fetchone()

    if not visitor:
        flash('Visitor not found!', 'danger')
        conn.close()
        return redirect(url_for('index'))

    if visitor['status'] == 'Exited':
        flash('Visitor has already checked out.', 'warning')
        conn.close()
        return redirect(url_for('index'))

    conn.execute(
        "UPDATE visitors SET status = 'Exited', check_out = ? WHERE id = ?",
        (check_out_time, visitor_id)
    )
    conn.commit()
    conn.close()

    flash(f'Visitor "{visitor["name"]}" has been checked out. 👋', 'success')
    return redirect(url_for('index'))


@app.route('/delete/<int:visitor_id>')
@login_required
def delete_visitor(visitor_id):
    """Delete a visitor record."""
    conn = get_db_connection()
    visitor = conn.execute('SELECT * FROM visitors WHERE id = ?', (visitor_id,)).fetchone()

    if not visitor:
        flash('Visitor not found!', 'danger')
        conn.close()
        return redirect(url_for('index'))

    conn.execute('DELETE FROM visitors WHERE id = ?', (visitor_id,))
    conn.commit()
    conn.close()

    flash(f'Visitor "{visitor["name"]}" has been deleted. 🗑️', 'info')
    return redirect(url_for('index'))


# ─────────────────────────────────────────────
# API Route for Stats (used by dashboard charts)
# ─────────────────────────────────────────────

@app.route('/api/stats')
@login_required
def api_stats():
    """Return JSON statistics for dashboard."""
    conn = get_db_connection()
    today = date.today().strftime('%Y-%m-%d')

    stats = {
        'total':   conn.execute('SELECT COUNT(*) FROM visitors').fetchone()[0],
        'today':   conn.execute("SELECT COUNT(*) FROM visitors WHERE check_in LIKE ?", (f'{today}%',)).fetchone()[0],
        'inside':  conn.execute("SELECT COUNT(*) FROM visitors WHERE status='Inside'").fetchone()[0],
        'exited':  conn.execute("SELECT COUNT(*) FROM visitors WHERE status='Exited'").fetchone()[0],
    }
    conn.close()
    return jsonify(stats)


# ─────────────────────────────────────────────
# Export to CSV Route
# ─────────────────────────────────────────────

@app.route('/export')
@login_required
def export_csv():
    """Export all visitor data as a CSV file."""
    conn = get_db_connection()
    visitors = conn.execute('SELECT * FROM visitors ORDER BY id DESC').fetchall()
    conn.close()

    # Create in-memory CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header row
    writer.writerow(['ID', 'Name', 'Phone', 'Purpose', 'Flat No.', 'Check In', 'Check Out', 'Status', 'Created At'])

    # Write data rows
    for v in visitors:
        writer.writerow([
            v['id'], v['name'], v['phone'], v['purpose'],
            v['flat_number'], v['check_in'], v['check_out'] or 'N/A',
            v['status'], v['created_at']
        ])

    # Create response with CSV file
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=visitors_export.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response


# ─────────────────────────────────────────────
# Run the Application
# ─────────────────────────────────────────────

if __name__ == '__main__':
    init_db()  # Create tables if they don't exist
    print("🏢 Apartment Visitor Management System")
    print("🚀 Starting server at http://127.0.0.1:5000")
    app.run(debug=True)
