import uuid
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import or_
from app import db
from app.models.user import User
from app.models.product import Product, Category
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem
from app.models.complaint import Complaint
from app.models.rating import Rating
from app.routes.auth_routes import student_required
from app.services.inventory_service import InventoryService
from app.services.order_service import OrderService

student_bp = Blueprint("student", __name__)


@student_bp.route("/marketplace")
def marketplace():
    """Browse catalog with search, category filter, price filter, condition, and sorting."""
    query = Product.query.filter_by(status="active")

    # Search keyword
    q = request.args.get("q", "").strip()
    if q:
        query = query.filter(
            or_(
                Product.title.ilike(f"%{q}%"),
                Product.description.ilike(f"%{q}%")
            )
        )

    # Category filter
    category_slug = request.args.get("category", "").strip()
    selected_category = None
    if category_slug:
        selected_category = Category.query.filter_by(slug=category_slug).first()
        if selected_category:
            query = query.filter_by(category_id=selected_category.id)

    # Price range filter
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    if min_price is not None and min_price >= 0:
        query = query.filter(Product.price >= min_price)
    if max_price is not None and max_price > 0:
        query = query.filter(Product.price <= max_price)

    # Condition filter
    condition = request.args.get("condition", "").strip()
    if condition:
        query = query.filter_by(condition=condition)

    # Sorting
    sort_by = request.args.get("sort", "newest")
    if sort_by == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort_by == "price_desc":
        query = query.order_by(Product.price.desc())
    elif sort_by == "name":
        query = query.order_by(Product.title.asc())
    else:  # newest
        query = query.order_by(Product.created_at.desc())

    products = query.all()
    categories = Category.query.filter_by(is_active=True).all()

    return render_template(
        "student/marketplace.html",
        products=products,
        categories=categories,
        selected_category=selected_category,
        q=q,
        min_price=min_price,
        max_price=max_price,
        condition=condition,
        sort_by=sort_by,
    )


@student_bp.route("/product/<int:product_id>")
def product_detail(product_id: int):
    """Product detail page with seller info, inventory status, and buyer reviews."""
    product = Product.query.get_or_404(product_id)
    related_products = (
        Product.query.filter(
            Product.category_id == product.category_id,
            Product.id != product.id,
            Product.status == "active"
        )
        .limit(4)
        .all()
    )
    return render_template(
        "student/product_detail.html",
        product=product,
        related_products=related_products,
    )


@student_bp.route("/cart")
@login_required
@student_required
def view_cart():
    """Display student's shopping cart."""
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()

    return render_template("student/cart.html", cart=cart)


@student_bp.route("/cart/add/<int:product_id>", methods=["POST"])
@login_required
@student_required
def add_to_cart(product_id: int):
    """Add item to cart or update existing quantity with stock validation."""
    product = Product.query.get_or_404(product_id)

    # Cannot buy own product
    if product.seller_id == current_user.id:
        flash("You cannot add your own listed product to your cart.", "warning")
        return redirect(url_for("student.product_detail", product_id=product_id))

    quantity = request.form.get("quantity", 1, type=int)
    if quantity <= 0:
        flash("Quantity must be at least 1.", "warning")
        return redirect(url_for("student.product_detail", product_id=product_id))

    # Check available stock
    avail, current_stock, msg = InventoryService.check_availability(product_id, quantity)
    if not avail:
        flash(f"Cannot add to cart: {msg}", "danger")
        return redirect(url_for("student.product_detail", product_id=product_id))

    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()

    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product.id).first()
    if cart_item:
        new_qty = cart_item.quantity + quantity
        if new_qty > product.stock_quantity:
            flash(f"Cannot add {quantity} more. Only {product.stock_quantity} left in stock.", "warning")
            return redirect(url_for("student.view_cart"))
        cart_item.quantity = new_qty
    else:
        cart_item = CartItem(cart_id=cart.id, product_id=product.id, quantity=quantity)
        db.session.add(cart_item)

    cart.updated_at = datetime.utcnow()
    db.session.commit()

    flash(f"Added '{product.title}' to your cart!", "success")
    return redirect(url_for("student.view_cart"))


@student_bp.route("/cart/update/<int:item_id>", methods=["POST"])
@login_required
@student_required
def update_cart_item(item_id: int):
    """Update cart item quantity."""
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.cart.user_id != current_user.id:
        flash("Unauthorized action.", "danger")
        return redirect(url_for("student.view_cart"))

    action = request.form.get("action")
    if action == "increase":
        if cart_item.quantity + 1 > cart_item.product.stock_quantity:
            flash(f"Maximum available stock reached ({cart_item.product.stock_quantity}).", "warning")
        else:
            cart_item.quantity += 1
            db.session.commit()
    elif action == "decrease":
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            db.session.commit()
        else:
            db.session.delete(cart_item)
            db.session.commit()
            flash("Item removed from cart.", "info")

    return redirect(url_for("student.view_cart"))


@student_bp.route("/cart/remove/<int:item_id>", methods=["POST"])
@login_required
@student_required
def remove_cart_item(item_id: int):
    """Remove item from cart."""
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.cart.user_id != current_user.id:
        flash("Unauthorized action.", "danger")
        return redirect(url_for("student.view_cart"))

    db.session.delete(cart_item)
    db.session.commit()
    flash("Item removed from your cart.", "info")
    return redirect(url_for("student.view_cart"))


@student_bp.route("/checkout", methods=["GET", "POST"])
@login_required
@student_required
def checkout():
    """Checkout page with campus pickup location selection and simulated payment."""
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart or not cart.items:
        flash("Your cart is empty. Add items before checking out.", "info")
        return redirect(url_for("student.marketplace"))

    campus_pickup_points = [
        "Campus Central Library (Ground Floor Helpdesk)",
        "Student Activity Center (SAC Plaza)",
        "Hostel H-3 Common Lounge",
        "Hostel Girls Block 1 Reception",
        "Main Campus Cafeteria / Food Court",
        "Engineering Department Porch",
    ]

    payment_options = [
        ("Campus UPI", "Instant simulated UPI payment (GPay / PhonePe)"),
        ("Cash on Pickup", "Pay in cash during face-to-face campus item handoff"),
        ("Campus Card", "Simulated university student smartcard debit"),
    ]

    if request.method == "POST":
        pickup_location = request.form.get("pickup_location", "").strip()
        custom_location = request.form.get("custom_location", "").strip()
        if pickup_location == "Custom" and custom_location:
            pickup_location = f"Custom: {custom_location}"

        payment_method = request.form.get("payment_method", "Campus UPI")
        notes = request.form.get("notes", "").strip()

        if not pickup_location:
            flash("Please choose or specify a campus pickup location.", "danger")
            return render_template(
                "student/checkout.html",
                cart=cart,
                pickup_points=campus_pickup_points,
                payment_options=payment_options,
            )

        success, orders, msg = OrderService.checkout_cart(
            buyer_id=current_user.id,
            pickup_location=pickup_location,
            payment_method=payment_method,
            notes=notes,
        )

        if not success:
            flash(msg, "danger")
            return redirect(url_for("student.view_cart"))

        flash(msg, "success")
        # Redirect to confirmation of first created order
        return redirect(url_for("student.order_confirmation", order_number=orders[0].order_number))

    return render_template(
        "student/checkout.html",
        cart=cart,
        pickup_points=campus_pickup_points,
        payment_options=payment_options,
    )


@student_bp.route("/order-confirmation/<order_number>")
@login_required
@student_required
def order_confirmation(order_number: str):
    """Confirmation receipt for a placed order."""
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    if order.buyer_id != current_user.id and not current_user.is_admin:
        flash("Unauthorized order access.", "danger")
        return redirect(url_for("student.my_orders"))

    return render_template("student/order_confirmation.html", order=order)


@student_bp.route("/my-orders")
@login_required
@student_required
def my_orders():
    """List of all orders placed by the current student buyer."""
    orders = (
        Order.query.filter_by(buyer_id=current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return render_template("student/my_orders.html", orders=orders)


@student_bp.route("/order-tracking/<order_number>")
@login_required
@student_required
def order_tracking(order_number: str):
    """Step progress tracking for an order."""
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    if order.buyer_id != current_user.id and order.seller_id != current_user.id and not current_user.is_admin:
        flash("Unauthorized access to order tracker.", "danger")
        return redirect(url_for("student.my_orders"))

    return render_template("student/order_tracking.html", order=order)


@student_bp.route("/order/<int:order_id>/cancel", methods=["POST"])
@login_required
@student_required
def cancel_order(order_id: int):
    """Cancel an order (only allowed if Pending or Accepted)."""
    success, msg = OrderService.update_order_status(
        order_id=order_id,
        new_status="Cancelled",
        actor_id=current_user.id,
        is_admin=False,
    )
    if success:
        flash(msg, "success")
    else:
        flash(msg, "danger")
    return redirect(url_for("student.my_orders"))


@student_bp.route("/order/<int:order_id>/review", methods=["POST"])
@login_required
@student_required
def review_order(order_id: int):
    """Submit rating and feedback for completed order."""
    order = Order.query.get_or_404(order_id)
    if order.buyer_id != current_user.id:
        flash("Only the buyer can review this order.", "danger")
        return redirect(url_for("student.my_orders"))

    if order.status != "Completed":
        flash("You can only review completed orders.", "warning")
        return redirect(url_for("student.my_orders"))

    score = request.form.get("score", 5, type=int)
    review_text = request.form.get("review_text", "").strip()

    if score < 1 or score > 5:
        flash("Rating score must be between 1 and 5.", "danger")
        return redirect(url_for("student.my_orders"))

    # Rate each item in the order if not already rated
    for item in order.items:
        existing_rating = Rating.query.filter_by(product_id=item.product_id, order_id=order.id, buyer_id=current_user.id).first()
        if not existing_rating:
            rating = Rating(
                product_id=item.product_id,
                order_id=order.id,
                buyer_id=current_user.id,
                score=score,
                review_text=review_text,
                created_at=datetime.utcnow(),
            )
            db.session.add(rating)

    db.session.commit()
    flash("Thank you for your rating and feedback!", "success")
    return redirect(url_for("student.my_orders"))


@student_bp.route("/complaints", methods=["GET", "POST"])
@login_required
@student_required
def complaints():
    """List student's complaints and lodge new dispute tickets."""
    if request.method == "POST":
        order_id = request.form.get("order_id", type=int)
        subject = request.form.get("subject", "").strip()
        description = request.form.get("description", "").strip()

        if not subject or not description:
            flash("Please provide both subject and description for your complaint.", "danger")
            return redirect(url_for("student.complaints"))

        # Verify order if specified
        if order_id:
            order = db.session.get(Order, order_id)
            if not order or (order.buyer_id != current_user.id and order.seller_id != current_user.id):
                flash("Invalid order reference.", "danger")
                return redirect(url_for("student.complaints"))

        ticket_number = f"TKT-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        complaint = Complaint(
            ticket_number=ticket_number,
            order_id=order_id if order_id else None,
            student_id=current_user.id,
            subject=subject,
            description=description,
            status="Pending",
            created_at=datetime.utcnow(),
        )
        db.session.add(complaint)
        db.session.commit()

        flash(f"Complaint {ticket_number} lodged successfully. Campus Admin will review it shortly.", "success")
        return redirect(url_for("student.complaints"))

    selected_order_id = request.args.get("order_id", type=int)
    my_complaints = Complaint.query.filter_by(student_id=current_user.id).order_by(Complaint.created_at.desc()).all()
    my_orders = Order.query.filter_by(buyer_id=current_user.id).order_by(Order.created_at.desc()).all()

    return render_template(
        "student/my_complaints.html",
        complaints=my_complaints,
        orders=my_orders,
        selected_order_id=selected_order_id,
    )


@student_bp.route("/profile", methods=["GET", "POST"])
@login_required
@student_required
def profile():
    """Student profile information and contact updates."""
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        campus_block = request.form.get("campus_block", "").strip()

        current_user.phone = phone
        current_user.campus_block = campus_block
        db.session.commit()
        flash("Profile contact information updated successfully.", "success")
        return redirect(url_for("student.profile"))

    orders_count = Order.query.filter_by(buyer_id=current_user.id).count()
    listings_count = Product.query.filter_by(seller_id=current_user.id).count()
    complaints_count = Complaint.query.filter_by(student_id=current_user.id).count()

    return render_template(
        "student/profile.html",
        orders_count=orders_count,
        listings_count=listings_count,
        complaints_count=complaints_count,
    )
