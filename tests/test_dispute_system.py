import uuid
from datetime import datetime
from app import db
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.complaint import Complaint


def test_unique_ticket_id_generation(client, student_buyer, app):
    """Test that multiple submitted disputes generate unique ticket IDs."""
    client.post("/auth/login", data={"email": student_buyer.email, "password": "Student@123"})
    ticket_ids = set()

    for i in range(5):
        resp = client.post("/student/complaints", data={
            "subject": f"Dispute Ticket Issue {i}",
            "description": f"Detailed issue description for ticket test {i}.",
        }, follow_redirects=True)
        assert resp.status_code == 200

    with app.app_context():
        complaints = Complaint.query.filter_by(student_id=student_buyer.id).all()
        for comp in complaints:
            assert comp.ticket_number.startswith("TKT-")
            assert comp.ticket_number not in ticket_ids
            ticket_ids.add(comp.ticket_number)

    assert len(ticket_ids) >= 5


def test_order_dispute_link_and_persistence(client, student_buyer, student_seller, sample_product, app):
    """Test lodging a complaint linked to a specific order."""
    # Create an order
    with app.app_context():
        order = Order(
            order_number=f"ORD-TEST-{uuid.uuid4().hex[:6].upper()}",
            buyer_id=student_buyer.id,
            seller_id=student_seller.id,
            total_amount=sample_product.price,
            status="Completed",
            pickup_location="Library Lawn",
            created_at=datetime.utcnow(),
        )
        db.session.add(order)
        db.session.flush()

        item = OrderItem(
            order_id=order.id,
            product_id=sample_product.id,
            quantity=1,
            unit_price=sample_product.price,
            subtotal=sample_product.price,
        )
        db.session.add(item)
        db.session.commit()
        order_id = order.id
        order_num = order.order_number

    # Student logs in and accesses complaints page with order_id query param
    client.post("/auth/login", data={"email": student_buyer.email, "password": "Student@123"})
    prefill_resp = client.get(f"/student/complaints?order_id={order_id}")
    assert prefill_resp.status_code == 200
    assert f'value="{order_id}" selected' in prefill_resp.data.decode("utf-8")

    # Submit complaint linked to that order
    submit_resp = client.post("/student/complaints", data={
        "order_id": order_id,
        "subject": "Item was not received in agreed condition",
        "description": "Calculations keypad buttons are sticking and unusable.",
    }, follow_redirects=True)
    assert submit_resp.status_code == 200

    # Verify persistence in database
    with app.app_context():
        comp = Complaint.query.filter_by(order_id=order_id).first()
        assert comp is not None
        assert comp.order.order_number == order_num
        assert comp.student.id == student_buyer.id
        assert comp.status == "Pending"
        assert comp.status_badge_class == "bg-warning text-dark"
        assert comp.created_at is not None


def test_admin_dashboard_shows_actual_db_records(client, admin_user, student_buyer, app):
    """Verify admin dashboard displays real database dispute tickets, not hardcoded data."""
    # 1. Clear or check DB state
    with app.app_context():
        unique_subj = f"Database Sync Test {uuid.uuid4().hex[:8]}"
        comp = Complaint(
            ticket_number=f"TKT-SYNC-{uuid.uuid4().hex[:6].upper()}",
            student_id=student_buyer.id,
            subject=unique_subj,
            description="Testing live synchronization between DB and dashboard.",
            status="Under Review",
            created_at=datetime.utcnow(),
        )
        db.session.add(comp)
        db.session.commit()
        tkt_no = comp.ticket_number

    # Admin visits dashboard
    client.post("/auth/admin-login", data={"email": admin_user.email, "password": "Admin@123"})
    dash_resp = client.get("/admin/dashboard")
    assert dash_resp.status_code == 200
    html = dash_resp.data.decode("utf-8")

    # The actual database record must be rendered
    assert tkt_no in html
    assert unique_subj in html
    assert "Under Review" in html
    assert "bg-info text-dark" in html


def test_admin_updates_status_to_under_review_and_resolved(client, admin_user, student_buyer, app):
    """Verify admin status updates persist and reflect on dashboard and student view."""
    with app.app_context():
        comp = Complaint(
            ticket_number=f"TKT-STATUS-{uuid.uuid4().hex[:6].upper()}",
            student_id=student_buyer.id,
            subject="Status Progression Test",
            description="Testing Pending -> Under Review -> Resolved transitions.",
            status="Pending",
            created_at=datetime.utcnow(),
        )
        db.session.add(comp)
        db.session.commit()
        comp_id = comp.id
        tkt_no = comp.ticket_number

    client.post("/auth/admin-login", data={"email": admin_user.email, "password": "Admin@123"})

    # Step A: Update to 'Under Review' without mandatory notes
    resp1 = client.post("/admin/complaints", data={
        "complaint_id": comp_id,
        "status": "Under Review",
        "admin_notes": "",
        "next": "/admin/dashboard",
    }, follow_redirects=True)
    assert resp1.status_code == 200

    with app.app_context():
        c1 = db.session.get(Complaint, comp_id)
        assert c1.status == "Under Review"

    # Verify dashboard reflects 'Under Review' (cyan badge)
    dash1 = client.get("/admin/dashboard")
    assert dash1.status_code == 200
    assert "Under Review" in dash1.data.decode("utf-8")
    assert "bg-info text-dark" in dash1.data.decode("utf-8")

    # Step B: Update to 'Resolved' with resolution notes
    resp2 = client.post(f"/admin/complaints/{comp_id}", data={
        "status": "Resolved",
        "admin_notes": "Both students met at the student council office and resolved the dispute.",
        "next": "/admin/dashboard",
    }, follow_redirects=True)
    assert resp2.status_code == 200

    with app.app_context():
        c2 = db.session.get(Complaint, comp_id)
        assert c2.status == "Resolved"
        assert "Both students met" in c2.admin_notes

    # Verify dashboard reflects 'Resolved' (green badge)
    dash2 = client.get("/admin/dashboard")
    assert dash2.status_code == 200
    assert "Resolved" in dash2.data.decode("utf-8")
    assert "bg-success" in dash2.data.decode("utf-8")

    # Step C: Verify resolved ticket remains in history and filter
    filter_resolved = client.get("/admin/complaints?status=Resolved")
    assert filter_resolved.status_code == 200
    assert tkt_no in filter_resolved.data.decode("utf-8")

    filter_all = client.get("/admin/complaints?status=all")
    assert filter_all.status_code == 200
    assert tkt_no in filter_all.data.decode("utf-8")


def test_student_restricted_from_admin_complaints_routes(client, student_buyer, app):
    """Verify students cannot view or edit admin dispute management interfaces."""
    with app.app_context():
        comp = Complaint(
            ticket_number="TKT-PERM-TEST",
            student_id=student_buyer.id,
            subject="Permission enforcement",
            description="Testing role guard.",
            status="Pending",
            created_at=datetime.utcnow(),
        )
        db.session.add(comp)
        db.session.commit()
        comp_id = comp.id

    client.post("/auth/login", data={"email": student_buyer.email, "password": "Student@123"})

    # Try listing
    r1 = client.get("/admin/complaints", follow_redirects=True)
    assert b"Administrator privileges required" in r1.data

    # Try detail
    r2 = client.get(f"/admin/complaints/{comp_id}", follow_redirects=True)
    assert b"Administrator privileges required" in r2.data

    # Try post update
    r3 = client.post(f"/admin/complaints/{comp_id}", data={"status": "Resolved"}, follow_redirects=True)
    assert b"Administrator privileges required" in r3.data

    r4 = client.post("/admin/complaints", data={"complaint_id": comp_id, "status": "Resolved"}, follow_redirects=True)
    assert b"Administrator privileges required" in r4.data
