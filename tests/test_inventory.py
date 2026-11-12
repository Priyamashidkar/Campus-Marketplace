from app import db
from app.models.inventory import Inventory
from app.services.inventory_service import InventoryService
from app.services.order_service import OrderService


def test_inventory_atomic_deduction(sample_product, app):
    """Test inventory deduction logic directly."""
    with app.app_context():
        # Initial quantity is 3
        inv = Inventory.query.filter_by(product_id=sample_product.id).first()
        assert inv.stock_quantity == 3

        # Deduct 2
        success = InventoryService.deduct_stock(sample_product.id, 2)
        assert success is True
        assert inv.stock_quantity == 1
        assert inv.product.status == "active"

        # Deduct 1 more (depleting to 0)
        success_deplete = InventoryService.deduct_stock(sample_product.id, 1)
        assert success_deplete is True
        assert inv.stock_quantity == 0
        assert inv.product.status == "out_of_stock"


def test_overselling_prevention(client, student_buyer, sample_product, app):
    """Ensure ordering more than available stock is rejected."""
    client.post("/auth/login", data={"email": student_buyer.email, "password": "Student@123"})

    # Attempt to add 10 items when only 3 exist
    add_resp = client.post(f"/student/cart/add/{sample_product.id}", data={"quantity": 10}, follow_redirects=True)
    assert b"Only 3 item(s) left in stock" in add_resp.data

    with app.app_context():
        # Verify no items added and inventory untouched
        inv = Inventory.query.filter_by(product_id=sample_product.id).first()
        assert inv.stock_quantity == 3


def test_inventory_restoration_on_cancellation(client, student_buyer, student_seller, sample_product, app):
    """Test stock restoration when an order is cancelled or rejected."""
    client.post("/auth/login", data={"email": student_buyer.email, "password": "Student@123"})

    # Add 2 items to cart and checkout
    client.post(f"/student/cart/add/{sample_product.id}", data={"quantity": 2})
    client.post("/student/checkout", data={
        "pickup_location": "Hostel H-3 Common Room",
        "payment_method": "Campus UPI",
    })

    with app.app_context():
        inv = Inventory.query.filter_by(product_id=sample_product.id).first()
        assert inv.stock_quantity == 1  # 3 - 2 = 1

        order = student_buyer.orders_placed.first()
        assert order is not None

    # Cancel order as buyer
    cancel_resp = client.post(f"/student/order/{order.id}/cancel", follow_redirects=True)
    assert cancel_resp.status_code == 200

    with app.app_context():
        inv_after = Inventory.query.filter_by(product_id=sample_product.id).first()
        # Stock restored from 1 back to 3
        assert inv_after.stock_quantity == 3
        order_after = student_buyer.orders_placed.first()
        assert order_after.status == "Cancelled"
        assert order_after.transaction.payment_status == "Refunded"


def test_admin_stock_adjustment(client, admin_user, sample_product, app):
    """Test admin inventory update."""
    client.post("/auth/admin-login", data={"email": admin_user.email, "password": "Admin@123"})

    resp = client.post("/admin/inventory", data={
        "product_id": sample_product.id,
        "stock_quantity": 15,
        "low_stock_threshold": 5,
    }, follow_redirects=True)

    assert resp.status_code == 200
    with app.app_context():
        inv = Inventory.query.filter_by(product_id=sample_product.id).first()
        assert inv.stock_quantity == 15
        assert inv.low_stock_threshold == 5
