from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
from app.models.cart import Cart
from app.services.email_verifier import is_valid_campus_email, is_valid_student_id

auth_bp = Blueprint("auth", __name__)


def admin_required(f):
    """Decorator to restrict access to administrator accounts only."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in with administrator credentials.", "warning")
            return redirect(url_for("auth.admin_login", next=request.url))
        if not current_user.is_admin:
            flash("Access denied. Administrator privileges required.", "danger")
            return redirect(url_for("public.index"))
        return f(*args, **kwargs)
    return decorated_function


def student_required(f):
    """Decorator to ensure active student accounts."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to your student account.", "info")
            return redirect(url_for("auth.login", next=request.url))
        if current_user.is_admin:
            flash("You are logged in as an administrator. Please use a student account for marketplace actions.", "info")
            return redirect(url_for("admin.dashboard"))
        if not current_user.is_active:
            flash("Your account has been deactivated. Please contact campus administration.", "danger")
            logout_user()
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        student_id = request.form.get("student_id", "").strip().upper()
        email = request.form.get("email", "").strip().lower()
        campus_block = request.form.get("campus_block", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Form validations
        if not all([full_name, student_id, email, password, confirm_password]):
            flash("Please fill in all required fields.", "danger")
            return render_template("auth/register.html")

        if password != confirm_password:
            flash("Passwords do not match. Please re-enter.", "danger")
            return render_template("auth/register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("auth/register.html")

        if not is_valid_student_id(student_id):
            flash("Student ID must be 4 to 20 alphanumeric characters.", "danger")
            return render_template("auth/register.html")

        valid_email, email_err = is_valid_campus_email(email)
        if not valid_email:
            flash(email_err, "danger")
            return render_template("auth/register.html")

        # Check existing user
        if User.query.filter_by(email=email).first():
            flash("An account with this email address already exists.", "warning")
            return render_template("auth/register.html")

        if User.query.filter_by(student_id=student_id).first():
            flash("An account with this Student ID already exists.", "warning")
            return render_template("auth/register.html")

        # Create new student user
        new_user = User(
            full_name=full_name,
            student_id=student_id,
            email=email,
            phone=phone,
            campus_block=campus_block,
            is_admin=False,
            is_active=True,
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush()

        # Create associated cart
        cart = Cart(user_id=new_user.id)
        db.session.add(cart)
        db.session.commit()

        flash("Registration successful! You can now log in with your university credentials.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("student.marketplace"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Invalid email or password. Please try again.", "danger")
            return render_template("auth/login.html")

        if not user.is_active:
            flash("Your account has been deactivated. Please contact the administrator.", "danger")
            return render_template("auth/login.html")

        login_user(user, remember=remember)
        flash(f"Welcome back, {user.full_name}!", "success")

        next_page = request.args.get("next")
        if next_page and not next_page.startswith("//") and not next_page.startswith("http"):
            return redirect(next_page)

        if user.is_admin:
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("student.marketplace"))

    return render_template("auth/login.html")


@auth_bp.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    """Dedicated login route for ERP administrators."""
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Invalid administrator credentials.", "danger")
            return render_template("auth/admin_login.html")

        if not user.is_admin:
            flash("Access denied. This account does not possess administrator rights.", "danger")
            return render_template("auth/admin_login.html")

        if not user.is_active:
            flash("Administrator account is inactive.", "danger")
            return render_template("auth/admin_login.html")

        login_user(user)
        flash(f"Welcome to ERP Control Center, Administrator {user.full_name}!", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("auth/admin_login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been safely logged out.", "info")
    return redirect(url_for("public.index"))
