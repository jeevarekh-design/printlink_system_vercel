from flask import Flask, render_template, request, redirect, session, send_from_directory
import os
from utils.db import get_db_connection, execute_query

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)
app.secret_key = os.getenv("SECRET_KEY", "printlink_secret")

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure uploads folder exists (local Dev only; Vercel writes are ephemeral)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------------- HOME ----------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------- STUDENT MENU ----------------

@app.route("/student")
def student_menu():
    return render_template("student_menu.html")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        try:
            cursor = execute_query(
                conn,
                "INSERT INTO students (name,email,password) VALUES (?,?,?)",
                (name, email, password),
            )
            conn.commit()
            return redirect("/login")
        except Exception:
            return render_template("register.html", error="Email already registered. Please login.")
        finally:
            conn.close()

    return render_template("register.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        try:
            cursor = execute_query(
                conn,
                "SELECT * FROM students WHERE email=? AND password=?",
                (email, password),
            )
            user = cursor.fetchone()
            if user:
                session["student"] = user["name"]
                return redirect("/dashboard")
        finally:
            conn.close()

    return render_template("login.html")


# ---------------- STUDENT DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():
    if "student" not in session:
        return redirect("/login")
    return render_template("student_dashboard.html")


# ---------------- UPLOAD PAGE ----------------

@app.route("/upload")
def upload():
    if "student" not in session:
        return redirect("/login")
    return render_template("upload.html")


# ---------------- FILE UPLOAD ----------------

@app.route("/upload_file", methods=["POST"])
def upload_file():
    student_name = request.form["student_name"]
    copies = request.form["copies"]
    print_type = request.form["print_type"]

    file = request.files["file"]
    filename = file.filename

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    conn = get_db_connection()
    try:
        execute_query(
            conn,
            "INSERT INTO orders (student_name,file_name,copies,print_type,status,seen) VALUES (?,?,?,?,?,?)",
            (student_name, filename, copies, print_type, "Inbox", 0),
        )
        conn.commit()
    finally:
        conn.close()

    return redirect("/dashboard")


# ---------------- SERVE UPLOADED FILE ----------------

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ---------------- TRACK ORDERS ----------------

@app.route("/track")
def track():
    if "student" not in session:
        return redirect("/login")

    conn = get_db_connection()
    try:
        cursor = execute_query(
            conn,
            "SELECT * FROM orders WHERE student_name=?",
            (session["student"],),
        )
        orders = cursor.fetchall()
    finally:
        conn.close()

    return render_template("track_order.html", orders=orders)


# =================================================
# ADMIN SECTION
# =================================================


# ---------------- ADMIN LOGIN ----------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["admin"] = username
            return redirect("/admin/dashboard")

    return render_template("admin/login.html")


# ---------------- ADMIN DASHBOARD ----------------

@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin/login")

    conn = get_db_connection()
    try:
        cursor = execute_query(conn, "SELECT COUNT(*) AS cnt FROM orders")
        total = cursor.fetchone()["cnt"]

        cursor = execute_query(conn, "SELECT COUNT(*) AS cnt FROM orders WHERE status='Inbox'")
        inbox = cursor.fetchone()["cnt"]

        cursor = execute_query(conn, "SELECT COUNT(*) AS cnt FROM orders WHERE status='Printing'")
        printing = cursor.fetchone()["cnt"]

        cursor = execute_query(conn, "SELECT COUNT(*) AS cnt FROM orders WHERE status='Ready'")
        ready = cursor.fetchone()["cnt"]

        cursor = execute_query(conn, "SELECT COUNT(*) AS cnt FROM orders WHERE status='Delivered'")
        delivered = cursor.fetchone()["cnt"]

        cursor = execute_query(conn, "SELECT COUNT(*) AS cnt FROM orders WHERE seen=0")
        notifications = cursor.fetchone()["cnt"]
    finally:
        conn.close()

    return render_template(
        "admin/dashboard.html",
        total=total,
        inbox=inbox,
        printing=printing,
        ready=ready,
        delivered=delivered,
        notifications=notifications,
    )


# ---------------- ADMIN INBOX ----------------

@app.route("/admin/inbox")
def admin_inbox():
    if "admin" not in session:
        return redirect("/admin/login")

    conn = get_db_connection()
    try:
        cursor = execute_query(conn, "SELECT * FROM orders WHERE status='Inbox'")
        orders = cursor.fetchall()
        execute_query(conn, "UPDATE orders SET seen=1 WHERE seen=0")
        conn.commit()
    finally:
        conn.close()

    return render_template("admin/inbox.html", orders=orders)


# ---------------- ADMIN PRINTING ----------------

@app.route("/admin/printing")
def admin_printing():
    if "admin" not in session:
        return redirect("/admin/login")

    conn = get_db_connection()
    try:
        cursor = execute_query(conn, "SELECT * FROM orders WHERE status='Printing'")
        orders = cursor.fetchall()
    finally:
        conn.close()

    return render_template("admin/printing.html", orders=orders)


# ---------------- ADMIN READY ----------------

@app.route("/admin/ready")
def admin_ready():
    if "admin" not in session:
        return redirect("/admin/login")

    conn = get_db_connection()
    try:
        cursor = execute_query(conn, "SELECT * FROM orders WHERE status='Ready'")
        orders = cursor.fetchall()
    finally:
        conn.close()

    return render_template("admin/ready.html", orders=orders)


# ---------------- ADMIN DELIVERED ----------------

@app.route("/admin/delivered")
def admin_delivered():
    if "admin" not in session:
        return redirect("/admin/login")

    conn = get_db_connection()
    try:
        cursor = execute_query(conn, "SELECT * FROM orders WHERE status='Delivered'")
        orders = cursor.fetchall()
    finally:
        conn.close()

    return render_template("admin/delivered.html", orders=orders)


# ---------------- UPDATE ORDER STATUS ----------------

@app.route("/update_status/<int:id>/<status>")
def update_status(id, status):
    if "admin" not in session:
        return redirect("/admin/login")

    conn = get_db_connection()
    try:
        execute_query(conn, "UPDATE orders SET status=? WHERE id=?", (status, id))
        conn.commit()
    finally:
        conn.close()

    if status == "Printing":
        return redirect("/admin/printing")
    if status == "Ready":
        return redirect("/admin/ready")
    if status == "Delivered":
        return redirect("/admin/delivered")
    return redirect("/admin/dashboard")


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.pop("student", None)
    session.pop("admin", None)
    return redirect("/")


# ---------------- RUN APP ----------------

if __name__ == "__main__":
    app.run(debug=True)
