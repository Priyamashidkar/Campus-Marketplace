from datetime import datetime
from decimal import Decimal
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user
from app import db
from app.models.user import User
from app.models.product import Product, Category
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.transaction import Transaction
from app.models.complaint import Complaint
from app.models.rating import Rating
from app.routes.auth_routes import admin_required
from app.services.inventory_service import InventoryService
from app.services.order_service import OrderService
from app.services.erp_service import ERPService

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    """Central ERP Dashboard displaying summary KPIs, visual charts, and recent activities."""
    kpis = ERPService.get_summary_kpis()
    recent = ERPService.get_recent_activities(limit=6)
    return render_template(
        "admin/dashboard.html",
        kpis=kpis,
        recent_orders=recent["recent_orders"],
        recent_complaints=recent["recent_complaints"],
        low_stock_items=recent["low_stock_items"],
    )


@admin_bp.route("/api/chart-data")
@admin_required
def api_chart_data():
    """API endpoint providing dynamic live data for Chart.js in ERP dashboard."""
    monthly_trends = ERPService.get_monthly_order_trends(months=6)
    category_dist = ERPService.get_category_distribution()
    inventory_health = ERPService.get_inventory_status_breakdown()

    return jsonify({
        "monthly_trends": monthly_trends,
        "category_distribution": category_dist,
        "inventory_health": inventory_health,
    })


@admin_bp.route("/users")
@admin_required
def users():
    """ERP User Management: View registered students and sellers, toggle account status."""
    q = request.args.get("q", "").strip()
    role_filter = request.args.get("role", "all")
    status_filter = request.args.get("status", "all")

    query = User.query

    if q:
        query = query.filter(
            (User.full_name.ilike(f"%{q}%")) |
            (User.email.ilike(f"%{q}%")) |
            (User.student_id.ilike(f"%{q}%"))
        )

    if role_filter == "admin":
        query = query.filter_by(is_admin=True)
    elif role_filter == "student":
        query = query.filter_by(is_admin=False)

    if status_filter == "active":
        query = query.filter_by(is_active=True)
    elif status_filter == "inactive":
        query = query.filter_by(is_active=False)

    all_users = query.order_by(User.created_at.desc()).all()
    return render_template(
        "admin/users.html",
        users=all_users,
        q=q,
        role_filter=role_filter,
        status_filter=status_filter,
    )


@admin_bp.route("/users/toggle-status/<int:user_id>", methods=["POST"])
@admin_required
def toggle_user_status(user_id: int):
    """Activate or deactivate student accounts."""
    if user_id == current_user.id:
        flash("You cannot deactivate your own administrator account.", "danger")
        return redirect(url_for("admin.users"))

    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()

    status_str = "activated" if user.is_active else "deactivated"
    flash(f"User '{user.full_name}' ({user.email}) has been {status_str}.", "info")
    return redirect(url_for("admin.users"))


@admin_bp.route("/products")
@admin_required
def products():
    """ERP Product Management: Moderate listings, inspect sellers and inventory."""
    category_id = request.args.get("category_id", type=int)
    status_filter = request.args.get("status", "all")
    q = request.args.get("q", "").strip()

    query = Product.query

    if q:
        query = query.filter(Product.title.ilike(f"%{q}%"))
    if category_id:
        query = query.filter_by(category_id=category_id)
    if status_filter != "all":
        query = query.filter_by(status=status_filter)

    all_products = query.order_by(Product.created_at.desc()).all()
    categories = Category.query.all()

    return render_template(
        "admin/products.html",
        products=all_products,
        categories=categories,
        category_id=category_id,
        status_filter=status_filter,
        q=q,
    )


@admin_bp.route("/products/toggle-status/<int:product_id>", methods=["POST"])
@admin_required
def toggle_product_status(product_id: int):
    """Admin moderation to toggle product listing status."""
    product = Product.query.get_or_404(product_id)
    if product.status == "active":
        product.status = "deactivated"
        flash(f"Product '{product.title}' was deactivated by administrator.", "warning")
    else:
        product.status = "active" if product.stock_quantity > 0 else "out_of_stock"
        flash(f"Product '{product.title}' has been activated.", "success")

    db.session.commit()
    return redirect(url_for("admin.products"))


@admin_bp.route("/categories", methods=["GET", "POST"])
@admin_required
def categories():
    """ERP Category Management: Add and edit categories."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        icon = request.form.get("icon", "bi-tag").strip()

        if not name:
            flash("Category name is required.", "danger")
            return redirect(url_for("admin.categories"))

        slug = name.lower().replace(" ", "-")
        existing = Category.query.filter((Category.name == name) | (Category.slug == slug)).first()
        if existing:
            flash(f"Category '{name}' already exists.", "warning")
            return redirect(url_for("admin.categories"))

        new_cat = Category(name=name, slug=slug, description=description, icon=icon, is_active=True)
        db.session.add(new_cat)
        db.session.commit()
        flash(f"Category '{name}' created successfully.", "success")
        return redirect(url_for("admin.categories"))

    all_categories = Category.query.all()
    return render_template("admin/categories.html", categories=all_categories)


@admin_bp.route("/categories/toggle/<int:category_id>", methods=["POST"])
@admin_required
def toggle_category(category_id: int):
    """Enable or disable category."""
    cat = Category.query.get_or_404(category_id)
    cat.is_active = not cat.is_active
    db.session.commit()
    flash(f"Category '{cat.name}' visibility toggled.", "info")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/inventory", methods=["GET", "POST"])
@admin_required
def inventory():
    """ERP Inventory Control: Real-time stock audit and administrative replenishment."""
    if request.method == "POST":
        product_id = request.form.get("product_id", type=int)
        new_quantity = request.form.get("stock_quantity", type=int)
        new_threshold = request.form.get("low_stock_threshold", type=int)

        if product_id is not None and new_quantity is not None:
            InventoryService.update_stock(product_id, new_quantity, new_threshold)
            flash("Inventory stock updated successfully.", "success")
            return redirect(url_for("admin.inventory"))

    filter_type = request.args.get("filter", "all")
    query = Inventory.query.join(Product)

    if filter_type == "low_stock":
        query = query.filter(Inventory.stock_quantity <= Inventory.low_stock_threshold, Inventory.stock_quantity > 0)
    elif filter_type == "out_of_stock":
        query = query.filter(Inventory.stock_quantity <= 0)

    inventory_items = query.order_by(Inventory.stock_quantity.asc()).all()

    return render_template(
        "admin/inventory.html",
        inventory_items=inventory_items,
        filter_type=filter_type,
    )


@admin_bp.route("/orders")
@admin_required
def orders():
    """ERP Order Management: Global campus marketplace orders."""
    status_filter = request.args.get("status", "all")
    q = request.args.get("q", "").strip()

    query = Order.query

    if q:
        query = query.filter(
            (Order.order_number.ilike(f"%{q}%")) |
            (Order.pickup_location.ilike(f"%{q}%"))
        )

    if status_filter != "all":
        query = query.filter_by(status=status_filter)

    all_orders = query.order_by(Order.created_at.desc()).all()
    return render_template("admin/orders.html", orders=all_orders, status_filter=status_filter, q=q)


@admin_bp.route("/orders/update-status/<int:order_id>", methods=["POST"])
@admin_required
def update_order_status(order_id: int):
    """Admin override to update order status."""
    new_status = request.form.get("status", "")
    success, msg = OrderService.update_order_status(
        order_id=order_id,
        new_status=new_status,
        actor_id=current_user.id,
        is_admin=True,
    )
    if success:
        flash(msg, "success")
    else:
        flash(msg, "danger")

    return redirect(url_for("admin.orders"))


@admin_bp.route("/transactions")
@admin_required
def transactions():
    """ERP Financial Audit Log: Detailed simulated transaction records."""
    status_filter = request.args.get("payment_status", "all")
    method_filter = request.args.get("payment_method", "all")

    query = Transaction.query

    if status_filter != "all":
        query = query.filter_by(payment_status=status_filter)
    if method_filter != "all":
        query = query.filter_by(payment_method=method_filter)

    all_txns = query.order_by(Transaction.transaction_date.desc()).all()
    total_val = sum((t.amount for t in all_txns), Decimal("0.00"))

    return render_template(
        "admin/transactions.html",
        transactions=all_txns,
        total_val=total_val,
        status_filter=status_filter,
        method_filter=method_filter,
    )


@admin_bp.route("/complaints", methods=["GET", "POST"])
@admin_required
def complaints():
    """ERP Complaint Resolution Panel: Review student tickets and resolve disputes."""
    if request.method == "POST":
        complaint_id = request.form.get("complaint_id", type=int)
        new_status = request.form.get("status", "")
        admin_notes = request.form.get("admin_notes", "").strip()

        complaint = Complaint.query.get_or_404(complaint_id)
        if new_status:
            complaint.status = new_status
        if "admin_notes" in request.form:
            complaint.admin_notes = admin_notes
        complaint.updated_at = datetime.utcnow()

        db.session.commit()
        flash(f"Complaint {complaint.ticket_number} updated to '{complaint.status}'.", "success")
        next_url = request.form.get("next") or request.referrer or url_for("admin.complaints")
        return redirect(next_url)

    status_filter = request.args.get("status", "all")
    query = Complaint.query

    if status_filter != "all":
        query = query.filter_by(status=status_filter)

    all_complaints = query.order_by(Complaint.created_at.desc()).all()
    return render_template("admin/complaints.html", complaints=all_complaints, status_filter=status_filter)


@admin_bp.route("/complaints/<int:complaint_id>", methods=["GET", "POST"])
@admin_required
def complaint_detail(complaint_id: int):
    """ERP Dispute Details: View complete ticket info and update status."""
    complaint = Complaint.query.get_or_404(complaint_id)
    if request.method == "POST":
        new_status = request.form.get("status", "")
        admin_notes = request.form.get("admin_notes", "").strip()

        if new_status:
            complaint.status = new_status
        if "admin_notes" in request.form:
            complaint.admin_notes = admin_notes
        complaint.updated_at = datetime.utcnow()

        db.session.commit()
        flash(f"Complaint {complaint.ticket_number} updated to '{complaint.status}'.", "success")
        next_url = request.form.get("next") or request.referrer or url_for("admin.complaint_detail", complaint_id=complaint.id)
        return redirect(next_url)

    return render_template("admin/complaint_detail.html", complaint=complaint)


@admin_bp.route("/reports")
@admin_required
def reports():
    """ERP Reports & Analytics: Comprehensive operational and financial metrics."""
    kpis = ERPService.get_summary_kpis()
    monthly_trends = ERPService.get_monthly_order_trends(months=6)
    category_dist = ERPService.get_category_distribution()
    top_products = ERPService.get_top_selling_products(limit=8)

    return render_template(
        "admin/reports.html",
        kpis=kpis,
        monthly_trends=monthly_trends,
        category_dist=category_dist,
        top_products=top_products,
    )
