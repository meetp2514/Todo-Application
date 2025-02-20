from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)

# Configurations
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///mydb.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Assignment Model
class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"{self.id} - {self.title}"

@app.route("/")
def home():
    return redirect(url_for("signup"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("signup"))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered!", "warning")
            return redirect(url_for("signup"))

        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        new_user = User(name=name, email=email, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["user_name"] = user.name
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password!", "danger")

    return render_template("login.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form.get("title")
        desc = request.form.get("desc")

        if not title or not desc:
            flash("Title and Description are required!", "danger")
        else:
            new_assignment = Assignment(title=title, desc=desc)  
            db.session.add(new_assignment)
            db.session.commit()
            flash("Assignment added successfully!", "success")
            return redirect(url_for("dashboard"))

    # Retrieve all assignments
    all_assignments = Assignment.query.all()
    return render_template("dashboard.html", all_assignments=all_assignments, user_name=session["user_name"])

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("user_name", None)
    flash("You have logged out.", "info")
    return redirect(url_for("login"))

@app.route("/update/<int:id>", methods=["GET", "POST"])
def update(id):
    assignment = Assignment.query.get_or_404(id)
    if request.method == "POST":
        assignment.title = request.form["title"]
        assignment.desc = request.form["desc"]
        db.session.commit()
        flash("Assignment updated successfully!", "success")
        return redirect(url_for("dashboard"))
    return render_template("update.html", assignment=assignment)

@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    assignment = Assignment.query.get_or_404(id)
    db.session.delete(assignment)
    db.session.commit()
    flash("Assignment deleted successfully!", "success")
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    with app.app_context():
        if not os.path.exists("mydb.db"):
            db.create_all()
    app.run(debug=True, port=8000)
