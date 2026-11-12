from decimal import Decimal
from app import db
from app.models.cart import Cart, CartItem
from app.models.order import Order
from app.models.transaction import Transaction


def test_cart_operations(client, student_buyer, sample_product, app):
    """Test adding, updating and removing items from shopping cart."""
    client.post("/auth/login", data={"email": student_buyer.email, "password": "Student@123"})

    # 1. Add item to cart
    add_resp = client.post(f"/student/cart/add/{sample_product.id}", data={"quantity": 1}, follow_redirects=True)
    assert add_resp.status_code == 200
    assert b"Added &#39;Engineering Mathematics Test Edition&#39; to your cart" in add_resp.data

    with app.app_context():
        cart = Cart.query.filter_by(user_id=student_buyer.id).first()
        assert cart.item_count == 1
        assert cart.total_amount == Decimal("400.00")
        item = cart.items[0]

    # 2. Increase quantity in cart
    client.post(f"/student/cart/update/{item.id}", data={"action": "increase"}, follow_redirects=True)
    with app.app_context():
        cart = Cart.query.filter_by(user_id=student_buyer.id).first()
        assert cart.item_count == 2
        assert cart.total_amount == Decimal("800.00")

    # 3. Remove item from cart
    client.post(f"/student/cart/remove/{item.id}", follow_redirects=True)
    with app.app_context():
        cart = Cart.query.filter_by(user_id=student_buyer.id).first()
        assert cart.item_count == 0


def test_order_placement_and_transaction_creation(client, student_buyer, sample_product, app):
    """Test full checkout flow: Order generation, transaction log, and cart clearing."""
    client.post("/auth/login", data={"email": student_buyer.email, "password": "Student@123"})

    # Add to cart
    client.post(f"/student/cart/add/{sample_product.id}", data={"quantity": 2}, follow_redirects=True)

    # Checkout
    checkout_resp = client.post("/student/checkout", data={
        "pickup_location": "Campus Central Library (Ground Floor Helpdesk)",
        "payment_method": "Campus UPI",
        "notes": "Available at 4 PM",
    }, follow_redirects=True)

    assert checkout_resp.status_code == 200
    assert b"Order Placed Successfully" in checkout_resp.data

    with app.app_context():
        # Cart is cleared
        cart = Cart.query.filter_by(user_id=student_buyer.id).first()
        assert cart.item_count == 0

        # Order created
        order = Order.query.filter_by(buyer_id=student_buyer.id).first()
        assert order is not None
        assert order.status == "Pending"
        assert order.total_amount == Decimal("800.00")
        assert len(order.items) == 1
        assert order.items[0].quantity == 2

        # Inventory decremented from 3 to 1
        assert sample_product.inventory.stock_quantity == 1

        # Transaction created
        txn = Transaction.query.filter_by(order_id=order.id).first()
        assert txn is not None
        assert txn.amount == Decimal("800.00")
        assert txn.payment_method == "Campus UPI"
        assert txn.is_simulated is True


def test_cannot_buy_own_product(client, student_seller, sample_product):
    """Verify that sellers cannot buy their own listed products."""
    client.post("/auth/login", data={"email": student_seller.email, "password": "Student@123"})
    resp = client.post(f"/student/cart/add/{sample_product.id}", data={"quantity": 1}, follow_redirects=True)
    assert b"You cannot add your own listed product" in resp.data
