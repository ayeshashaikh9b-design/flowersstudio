from flask import Flask, render_template, request, redirect, session, g
import sqlite3
import random

app = Flask(__name__)
app.secret_key = "super_secret_key"

DATABASE = "database.db"

# ---------------- DATABASE ----------------
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# ---------------- INIT DB ----------------
def init_db():
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    db.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            date TEXT,
            guests TEXT
        )
    ''')
    db.execute('''
        CREATE TABLE IF NOT EXISTS enquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            message TEXT
        )
    ''')
    db.commit()

# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template(
        "index.html",
        admin_access=session.get('admin_logged_in', False),
        user_access=session.get('user_logged_in', False),
        username=session.get('username')
    )

# ---------------- SIGNUP ----------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            db.commit()
            return redirect('/login')
        except sqlite3.IntegrityError:
            return render_template("signup.html", error="User already exists ❌")

    return render_template("signup.html")

# ---------------- USER LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username=? AND password=?", (username, password)
        ).fetchone()

        if user:
            session['user_logged_in'] = True
            session['username'] = username
            return redirect('/')
        else:
            # Guest login if fields are empty
            if not username and not password:
                session['user_logged_in'] = True
                session['username'] = "Guest" + str(random.randint(1000,9999))
                return redirect('/')
            return render_template('login.html', error="Invalid username or password ❌")

    return render_template('login.html')

# ---------------- ADMIN LOGIN ----------------
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin_name = request.form.get('admin_name')
        admin_pass = request.form.get('admin_pass')

        # Hard-coded admin credentials
        if admin_name == 'hamza' and admin_pass == 'admin123':
            session['admin_logged_in'] = True
            session['username'] = admin_name
            return redirect('/')
        return render_template('admin-login.html', error="Invalid admin credentials ❌")

    return render_template('admin-login.html')

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.pop('user_logged_in', None)
    session.pop('admin_logged_in', None)
    session.pop('username', None)
    return redirect('/')

# ---------------- ADMIN PANEL ----------------
@app.route('/admin')
def admin_panel():
    if not session.get('admin_logged_in'):
        return redirect('/admin-login')

    db = get_db()
    bookings = db.execute("SELECT * FROM bookings").fetchall()
    enquiries = db.execute("SELECT * FROM enquiries").fetchall()

    return render_template("admin.html", bookings=bookings, enquiries=enquiries)

# ---------------- BOOKING ----------------
@app.route('/book', methods=['POST'])
def book():
    db = get_db()
    db.execute('''
        INSERT INTO bookings (name, email, date, guests)
        VALUES (?, ?, ?, ?)
    ''', (
        request.form.get('name'),
        request.form.get('email'),
        request.form.get('date'),
        request.form.get('guests')
    ))
    db.commit()
    return redirect('/report')

# ---------------- ENQUIRY ----------------
@app.route('/enquiry', methods=['POST'])
def enquiry():
    db = get_db()
    db.execute('''
        INSERT INTO enquiries (name, email, message)
        VALUES (?, ?, ?)
    ''', (
        request.form.get('name'),
        request.form.get('email'),
        request.form.get('message')
    ))
    db.commit()
    return redirect('/report')

# ---------------- REPORT ----------------
@app.route('/report')
def report():
    db = get_db()
    bookings = db.execute("SELECT * FROM bookings").fetchall()
    enquiries = db.execute("SELECT * FROM enquiries").fetchall()

    return render_template(
        "report.html",
        bookings=bookings,
        enquiries=enquiries,
        admin_access=session.get('admin_logged_in', False)
    )

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True)