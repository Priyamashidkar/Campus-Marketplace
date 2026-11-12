import os
import uuid
from decimal import Decimal
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models.product import Product, Category
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.transaction import Transaction
from app.routes.auth_routes import student_required
from app.services.inventory_service import InventoryService
from app.services.order_service import OrderService

seller_bp = Blueprint("seller", __name__)


def allowed_file(filename: str) -> bool:
    """Validate upload image extension."""
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config.get("ALLOWED_EXTENSIONS", {"png", "jpg", "jpeg", "webp", "gif"})


@seller_bp.route("/dashboard")
@login_required
@student_required
def dashboard():
    """Seller overview with sales metrics, active listings, and incoming orders."""
    seller_id = current_user.id

    active_listings_count = Product.query.filter_by(seller_id=seller_id, status="active").count()
    total_listings_count = Product.query.filter_by(seller_id=seller_id).count()

    pending_orders_count = Order.query.filter_by(seller_id=seller_id, status="Pending").count()
    completed_orders_count = Order.query.filter_by(seller_id=seller_id, status="Completed").count()

    # Total earnings from completed orders
    total_earnings = (
        db.session.query(func.sum(Order.total_amount))
        .filter(Order.seller_id == seller_id, Order.status == "Completed")
        .scalar()
        or Decimal("0.00")
    )

    recent_incoming_orders = (
        Order.query.filter_by(seller_id=seller_id)
        .order_by(Order.created_at.desc())
        .limit(5)
        .all()
    )

    my_products = (
        Product.query.filter_by(seller_id=seller_id)
        .order_by(Product.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "seller/dashboard.html",
        active_listings_count=active_listings_count,
        total_listings_count=total_listings_count,
        pending_orders_count=pending_orders_count,
        completed_orders_count=completed_orders_count,
        total_earnings=total_earnings,
        recent_orders=recent_incoming_orders,
        my_products=my_products,
    )


@seller_bp.route("/products")
@login_required
@student_required
def manage_products():
    """List all products owned by this student seller."""
    products = Product.query.filter_by(seller_id=current_user.id).order_by(Product.created_at.desc()).all()
    return render_template("seller/manage_products.html", products=products)


@seller_bp.route("/products/add", methods=["GET", "POST"])
@login_required
@student_required
def add_product():
    """Add a new product listing with image upload and inventory initialization."""
    categories = Category.query.filter_by(is_active=True).all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category_id = request.form.get("category_id", type=int)
        price_val = request.form.get("price", type=float)
        quantity = request.form.get("quantity", 1, type=int)
        condition = request.form.get("condition", "Good")
        description = request.form.get("description", "").strip()

        # Validation
        if not title or not category_id or price_val is None or not description:
            flash("Please fill in all required fields.", "danger")
            return render_template("seller/product_form.html", categories=categories, product=None)

        if price_val <= 0:
            flash("Price must be greater than zero.", "danger")
            return render_template("seller/product_form.html", categories=categories, product=None)

        if quantity < 0:
            flash("Quantity cannot be negative.", "danger")
            return render_template("seller/product_form.html", categories=categories, product=None)

        # Image upload handling
        image_filename = "default_product.png"
        image_file = request.files.get("product_image")
        if image_file and image_file.filename:
            if allowed_file(image_file.filename):
                ext = secure_filename(image_file.filename).rsplit(".", 1)[1].lower()
                unique_name = f"prod_{uuid.uuid4().hex[:10]}.{ext}"
                upload_folder = current_app.config["UPLOAD_FOLDER"]
                image_file.save(os.path.join(upload_folder, unique_name))
                image_filename = unique_name
            else:
                flash("Invalid image format. Allowed formats: PNG, JPG, JPEG, WEBP, GIF.", "warning")

        # Create product
        new_product = Product(
            seller_id=current_user.id,
            category_id=category_id,
            title=title,
            description=description,
            price=Decimal(str(price_val)),
            condition=condition,
            image_url=image_filename,
            status="active" if quantity > 0 else "out_of_stock",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(new_product)
        db.session.flush()

        # Initialize linked Inventory
        InventoryService.initialize_inventory(new_product, initial_quantity=quantity)
        db.session.commit()

        flash(f"Product '{new_product.title}' listed successfully!", "success")
        return redirect(url_for("seller.manage_products"))

    return render_template("seller/product_form.html", categories=categories, product=None)


@seller_bp.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
@student_required
def edit_product(product_id: int):
    """Edit an existing product listing."""
    product = Product.query.get_or_404(product_id)
    if product.seller_id != current_user.id and not current_user.is_admin:
        flash("You do not have permission to edit this listing.", "danger")
        return redirect(url_for("seller.manage_products"))

    categories = Category.query.filter_by(is_active=True).all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category_id = request.form.get("category_id", type=int)
        price_val = request.form.get("price", type=float)
        quantity = request.form.get("quantity", type=int)
        condition = request.form.get("condition", "Good")
        description = request.form.get("description", "").strip()
        status = request.form.get("status", "active")

        if not title or not category_id or price_val is None or not description:
            flash("Please fill in all required fields.", "danger")
            return render_template("seller/product_form.html", categories=categories, product=product)

        # Image update
        image_file = request.files.get("product_image")
        if image_file and image_file.filename and allowed_file(image_file.filename):
            ext = secure_filename(image_file.filename).rsplit(".", 1)[1].lower()
            unique_name = f"prod_{uuid.uuid4().hex[:10]}.{ext}"
            upload_folder = current_app.config["UPLOAD_FOLDER"]
            image_file.save(os.path.join(upload_folder, unique_name))
            product.image_url = unique_name

        product.title = title
        product.category_id = category_id
        product.price = Decimal(str(price_val))
        product.condition = condition
        product.description = description
        product.status = status
        product.updated_at = datetime.utcnow()

        # Update stock in inventory
        if quantity is not None:
            InventoryService.update_stock(product.id, quantity)

        db.session.commit()
        flash(f"Product '{product.title}' updated successfully.", "success")
        return redirect(url_for("seller.manage_products"))

    return render_template("seller/product_form.html", categories=categories, product=product)


@seller_bp.route("/products/toggle-status/<int:product_id>", methods=["POST"])
@login_required
@student_required
def toggle_status(product_id: int):
    """Toggle listing between active and deactivated."""
    product = Product.query.get_or_404(product_id)
    if product.seller_id != current_user.id and not current_user.is_admin:
        flash("Unauthorized action.", "danger")
        return redirect(url_for("seller.manage_products"))

    if product.status == "active":
        product.status = "deactivated"
        flash(f"'{product.title}' has been deactivated from marketplace.", "info")
    else:
        product.status = "active" if product.stock_quantity > 0 else "out_of_stock"
        flash(f"'{product.title}' is now active.", "success")

    db.session.commit()
    return redirect(url_for("seller.manage_products"))


@seller_bp.route("/products/delete/<int:product_id>", methods=["POST"])
@login_required
@student_required
def delete_product(product_id: int):
    """Safely delete listing or deactivate if historical orders exist."""
    product = Product.query.get_or_404(product_id)
    if product.seller_id != current_user.id and not current_user.is_admin:
        flash("Unauthorized action.", "danger")
        return redirect(url_for("seller.manage_products"))

    if product.order_items:
        # Cannot hard delete due to order history integrity; deactivate instead
        product.status = "deactivated"
        db.session.commit()
        flash(f"Product '{product.title}' has prior orders and was deactivated rather than deleted to preserve history.", "warning")
    else:
        db.session.delete(product)
        db.session.commit()
        flash("Product listing deleted successfully.", "success")

    return redirect(url_for("seller.manage_products"))


@seller_bp.route("/orders")
@login_required
@student_required
def incoming_orders():
    """Incoming orders received from student buyers."""
    orders = (
        Order.query.filter_by(seller_id=current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return render_template("seller/incoming_orders.html", orders=orders)


@seller_bp.route("/orders/update-status/<int:order_id>", methods=["POST"])
@login_required
@student_required
def update_order_status(order_id: int):
    """Update incoming order status (e.g. Accept, Ready for Pickup, Complete, Reject)."""
    new_status = request.form.get("status", "")
    success, msg = OrderService.update_order_status(
        order_id=order_id,
        new_status=new_status,
        actor_id=current_user.id,
        is_admin=False,
    )
    if success:
        flash(msg, "success")
    else:
        flash(msg, "danger")

    return redirect(url_for("seller.incoming_orders"))


@seller_bp.route("/sales-history")
@login_required
@student_required
def sales_history():
    """Historical completed sales and earnings summary."""
    orders = (
        Order.query.filter_by(seller_id=current_user.id, status="Completed")
        .order_by(Order.updated_at.desc())
        .all()
    )
    total_revenue = sum((o.total_amount for o in orders), Decimal("0.00"))
    return render_template("seller/sales_history.html", orders=orders, total_revenue=total_revenue)
