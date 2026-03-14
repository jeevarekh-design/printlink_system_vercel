from flask import Flask, render_template, request, redirect, session, send_from_directory
import os
import psycopg2
import psycopg2.extras

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)

app.secret_key = os.getenv("SECRET_KEY", "printlink_secret")

UPLOAD_FOLDER = "/tmp/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ================= DATABASE =================

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    conn = psycopg2.connect(
        DATABASE_URL,
        sslmode="require",
        cursor_factory=psycopg2.extras.RealDictCursor
    )
    return conn


# ================= HOME =================

@app.route("/")
def index():
    return render_template("index.html")


# ================= STUDENT MENU =================

@app.route("/student")
def student_menu():
    return render_template("student_menu.html")


# ================= REGISTER =================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO students (name,email,password) VALUES (%s,%s,%s)",
                (name, email, password),
            )
            conn.commit()
            return redirect("/login")

        except Exception:
            return render_template(
                "register.html",
                error="Email already registered. Please login."
            )

        finally:
            cur.close()
            conn.close()

    return render_template("register.html")


# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM students WHERE email=%s AND password=%s",
            (email, password),
        )

        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            session["student"] = user["name"]
            return redirect("/dashboard")

    return render_template("login.html")


# ================= STUDENT DASHBOARD =================

@app.route("/dashboard")
def dashboard():
    if "student" not in session:
        return redirect("/login")

    return render_template("student_dashboard.html")


# ================= UPLOAD PAGE =================

@app.route("/upload")
def upload():
    if "student" not in session:
        return redirect("/login")

    return render_template("upload.html")


# ================= FILE UPLOAD =================

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
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO orders (student_name,file_name,copies,print_type,status,seen)
        VALUES (%s,%s,%s,%s,%s,%s)
        """,
        (student_name, filename, copies, print_type, "Inbox", False),
    )

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/dashboard")


# ================= SERVE FILE =================

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ================= TRACK ORDERS =================

@app.route("/track")
def track():

    if "student" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM orders WHERE student_name=%s",
        (session["student"],),
    )

    orders = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("track_order.html", orders=orders)


# =================================================
# ADMIN SECTION
# =================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["admin"] = username
            return redirect("/admin/dashboard")

    return render_template("admin/login.html")


# ================= ADMIN DASHBOARD =================

@app.route("/admin/dashboard")
def admin_dashboard():

    if "admin" not in session:
        return redirect("/admin/login")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM orders")
    total = cur.fetchone()["count"]

    cur.execute("SELECT COUNT(*) FROM orders WHERE status='Inbox'")
    inbox = cur.fetchone()["count"]

    cur.execute("SELECT COUNT(*) FROM orders WHERE status='Printing'")
    printing = cur.fetchone()["count"]

    cur.execute("SELECT COUNT(*) FROM orders WHERE status='Ready'")
    ready = cur.fetchone()["count"]

    cur.execute("SELECT COUNT(*) FROM orders WHERE status='Delivered'")
    delivered = cur.fetchone()["count"]

    cur.execute("SELECT COUNT(*) FROM orders WHERE seen=false")
    notifications = cur.fetchone()["count"]

    cur.close()
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


# ================= UPDATE STATUS =================

@app.route("/update_status/<int:id>/<status>")
def update_status(id, status):

    if "admin" not in session:
        return redirect("/admin/login")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE orders SET status=%s WHERE id=%s",
        (status, id),
    )

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/admin/dashboard")


# ================= LOGOUT =================

@app.route("/logout")
def logout():

    session.pop("student", None)
    session.pop("admin", None)

    return redirect("/")


# Vercel expects the Flask instance named "app"