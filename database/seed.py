import os
import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timedelta

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app import create_app, db
from app.models.user import User
from app.models.product import Category, Product
from app.models.inventory import Inventory
from app.models.cart import Cart
from app.models.order import Order, OrderItem
from app.models.transaction import Transaction
from app.models.complaint import Complaint
from app.models.rating import Rating


def seed_database():
    """Populate database with demonstration data for academic college evaluation."""
    app = create_app()

    with app.app_context():
        print("Initializing database tables...")
        db.create_all()

        # Check if already seeded
        if User.query.filter_by(email="admin@campus.edu").first():
            print("Database already contains seed data. Skipping seeder.")
            return

        print("Seeding campus categories...")
        categories_data = [
            ("Books", "books", "Academic textbooks, reference manuals, and semester notes.", "bi-book"),
            ("Electronics", "electronics", "Calculators, laptops, chargers, headphones, and components.", "bi-laptop"),
            ("Stationery", "stationery", "Drafters, drawing boards, pens, notebooks, and binders.", "bi-pencil"),
            ("Hostel Essentials", "hostel-essentials", "Coolers, kettles, study lamps, bedsheets, and storage.", "bi-house-heart"),
            ("Furniture", "furniture", "Study tables, ergonomic chairs, bookshelves, and shoe racks.", "bi-lamp"),
            ("Clothing", "clothing", "College hoodies, lab aprons, sports wear, and winter coats.", "bi-bag"),
            ("Lab Equipment", "lab-equipment", "Breadboards, multimeters, Arduino kits, and safety glasses.", "bi-tools"),
            ("Others", "others", "Bicycles, musical instruments, umbrellas, and general gear.", "bi-box-seam"),
        ]

        cat_map = {}
        for name, slug, desc, icon in categories_data:
            cat = Category(name=name, slug=slug, description=desc, icon=icon, is_active=True)
            db.session.add(cat)
            cat_map[slug] = cat

        db.session.flush()

        print("Seeding administrator and student user accounts...")
        # 1. Administrator
        admin = User(
            student_id="ADMIN001",
            full_name="Campus ERP Administrator",
            email="admin@campus.edu",
            phone="+91 9876500001",
            campus_block="Administration Block, Level 2",
            is_admin=True,
            is_active=True,
            created_at=datetime.utcnow() - timedelta(days=60),
        )
        admin.set_password("Admin@123")
        db.session.add(admin)

        # 2. Student 1 (Aarav Sharma - Active Seller & Buyer)
        student1 = User(
            student_id="CS2024001",
            full_name="Aarav Sharma",
            email="student1@campus.edu",
            phone="+91 9876500002",
            campus_block="Hostel H-3, Room 204",
            is_admin=False,
            is_active=True,
            created_at=datetime.utcnow() - timedelta(days=45),
        )
        student1.set_password("Student@123")
        db.session.add(student1)

        # 3. Student 2 (Priya Patel - Active Seller & Buyer)
        student2 = User(
            student_id="EC2024045",
            full_name="Priya Patel",
            email="student2@campus.edu",
            phone="+91 9876500003",
            campus_block="Hostel Girls Block 1, Room 112",
            is_admin=False,
            is_active=True,
            created_at=datetime.utcnow() - timedelta(days=40),
        )
        student2.set_password("Student@123")
        db.session.add(student2)

        # 4. Student 3 (Rohan Verma - Student Buyer)
        student3 = User(
            student_id="ME2024012",
            full_name="Rohan Verma",
            email="student3@campus.edu",
            phone="+91 9876500004",
            campus_block="Day Scholar (Civil Lines)",
            is_admin=False,
            is_active=True,
            created_at=datetime.utcnow() - timedelta(days=30),
        )
        student3.set_password("Student@123")
        db.session.add(student3)

        # 5. Student 4 (Sneha Rao - Student Buyer)
        student4 = User(
            student_id="IT2024089",
            full_name="Sneha Rao",
            email="student4@campus.edu",
            phone="+91 9876500005",
            campus_block="Hostel H-5, Room 408",
            is_admin=False,
            is_active=True,
            created_at=datetime.utcnow() - timedelta(days=25),
        )
        student4.set_password("Student@123")
        db.session.add(student4)

        db.session.flush()

        # Initialize carts
        for u in [student1, student2, student3, student4]:
            cart = Cart(user_id=u.id)
            db.session.add(cart)

        db.session.flush()

        print("Seeding realistic campus marketplace products & inventory records...")
        products_data = [
            # Seller: student1
            (student1.id, "books", "Higher Engineering Mathematics by B.S. Grewal (44th Ed)",
             "Standard textbook for 1st & 2nd year engineering mathematics. Good condition with minimal pencil highlighting.",
             Decimal("450.00"), "Good", 2, 2, "default_product.png"),

            (student1.id, "electronics", "Casio fx-991EX ClassWiz Scientific Calculator",
             "Non-programmable scientific calculator permitted in university exams. High-resolution screen, all keys crisp and responsive.",
             Decimal("850.00"), "Like New", 3, 2, "default_product.png"),

            (student1.id, "lab-equipment", "Arduino UNO Rev3 Starter Kit with 20+ Sensors",
             "Complete IoT & embedded kit with breadboard, ultrasonic sensor, RFID, servo motor, and jumper wires.",
             Decimal("1200.00"), "Like New", 2, 1, "default_product.png"),

            (student1.id, "furniture", "Ergonomic Mesh Study Chair with Lumbar Support",
             "Breathable black mesh back, height adjustable gas lift. Bought last semester, moving out of hostel.",
             Decimal("1500.00"), "Good", 1, 1, "default_product.png"),

            (student1.id, "clothing", "University CS Department Winter Hoodie (Size L)",
             "Navy blue cotton blend hoodie with university crest on chest. Unworn with original tags.",
             Decimal("650.00"), "Brand New", 2, 1, "default_product.png"),

            (student1.id, "hostel-essentials", "Rechargeable LED Study Lamp (Touch Dimmer)",
             "3 color temperature settings (warm, white, daylight) with USB-C rechargeable battery. Ideal for night study.",
             Decimal("320.00"), "Like New", 4, 2, "default_product.png"),

            # Seller: student2
            (student2.id, "books", "C++ Primer (5th Edition) - Stanley Lippman",
             "Comprehensive C++ reference textbook. Clean pages, no torn sheets, hardcover.",
             Decimal("550.00"), "Good", 1, 1, "default_product.png"),

            (student2.id, "hostel-essentials", "Havells Personal Mini Room Cooler (12 Litres)",
             "Compact evaporative cooler with honeycomb pads. Kept hostel room very cool during peak summer.",
             Decimal("2200.00"), "Good", 1, 1, "default_product.png"),

            (student2.id, "stationery", "Mini Drafter with Compass & Drawing Board Clips",
             "Engineering graphics mini drafter with steel scale and clamp. Working smoothly.",
             Decimal("280.00"), "Fair", 3, 2, "default_product.png"),

            (student2.id, "lab-equipment", "Unisex White Cotton Laboratory Coat (Size M)",
             "100% thick white cotton lab apron suitable for Chemistry and Physics practical sessions.",
             Decimal("250.00"), "Good", 5, 2, "default_product.png"),

            (student2.id, "electronics", "Raspberry Pi 4 Model B (4GB RAM) with Acrylic Case",
             "Single-board computer with official 5V 3A Type-C power adapter and micro-HDMI cable.",
             Decimal("3800.00"), "Like New", 1, 1, "default_product.png"),

            (student2.id, "others", "Hero Sprint 26T Mountain Bicycle (Single Speed)",
             "Campus commute bicycle with front basket and rear reflector. Recently serviced, tires have good grip.",
             Decimal("2600.00"), "Good", 1, 1, "default_product.png"),
        ]

        created_products = []
        for seller_id, cat_slug, title, desc, price, condition, stock_qty, threshold, img in products_data:
            p = Product(
                seller_id=seller_id,
                category_id=cat_map[cat_slug].id,
                title=title,
                description=desc,
                price=price,
                condition=condition,
                image_url=img,
                status="active" if stock_qty > 0 else "out_of_stock",
                created_at=datetime.utcnow() - timedelta(days=20),
                updated_at=datetime.utcnow() - timedelta(days=20),
            )
            db.session.add(p)
            db.session.flush()

            inv = Inventory(
                product_id=p.id,
                stock_quantity=stock_qty,
                low_stock_threshold=threshold,
                last_updated=datetime.utcnow() - timedelta(days=20),
            )
            db.session.add(inv)
            created_products.append(p)

        db.session.flush()

        print("Seeding demonstration orders, transactions, and reviews...")
        # Order 1: Completed Order (student3 bought Casio Calculator from student1)
        p_calc = created_products[1]
        ord1 = Order(
            order_number="ORD-20261101-A109B4",
            buyer_id=student3.id,
            seller_id=student1.id,
            total_amount=p_calc.price,
            status="Completed",
            pickup_location="Campus Central Library (Ground Floor Helpdesk)",
            notes="Met near the library entrance after 3 PM.",
            created_at=datetime.utcnow() - timedelta(days=10),
            updated_at=datetime.utcnow() - timedelta(days=9),
        )
        db.session.add(ord1)
        db.session.flush()

        ord1_item = OrderItem(
            order_id=ord1.id,
            product_id=p_calc.id,
            quantity=1,
            unit_price=p_calc.price,
            subtotal=p_calc.price,
        )
        db.session.add(ord1_item)

        txn1 = Transaction(
            transaction_number="TXN-20261101-C9921E",
            order_id=ord1.id,
            buyer_id=student3.id,
            seller_id=student1.id,
            amount=p_calc.price,
            payment_method="Campus UPI",
            payment_status="Completed",
            is_simulated=True,
            transaction_date=datetime.utcnow() - timedelta(days=10),
        )
        db.session.add(txn1)

        # Rating for Order 1
        rating1 = Rating(
            product_id=p_calc.id,
            order_id=ord1.id,
            buyer_id=student3.id,
            score=5,
            review_text="Calculator is in mint condition, exactly as described! Handover was on time.",
            created_at=datetime.utcnow() - timedelta(days=9),
        )
        db.session.add(rating1)

        # Order 2: Ready for Pickup (student4 bought Lab Coat from student2)
        p_coat = created_products[9]
        ord2 = Order(
            order_number="ORD-20261108-F482D1",
            buyer_id=student4.id,
            seller_id=student2.id,
            total_amount=p_coat.price,
            status="Ready for Pickup",
            pickup_location="Student Activity Center (SAC Plaza)",
            notes="Please bring it between 4 PM and 5 PM.",
            created_at=datetime.utcnow() - timedelta(days=3),
            updated_at=datetime.utcnow() - timedelta(days=2),
        )
        db.session.add(ord2)
        db.session.flush()

        ord2_item = OrderItem(
            order_id=ord2.id,
            product_id=p_coat.id,
            quantity=1,
            unit_price=p_coat.price,
            subtotal=p_coat.price,
        )
        db.session.add(ord2_item)

        txn2 = Transaction(
            transaction_number="TXN-20261108-88A31C",
            order_id=ord2.id,
            buyer_id=student4.id,
            seller_id=student2.id,
            amount=p_coat.price,
            payment_method="Cash on Pickup",
            payment_status="Pending",
            is_simulated=True,
            transaction_date=datetime.utcnow() - timedelta(days=3),
        )
        db.session.add(txn2)

        # Order 3: Pending Order (student3 ordered Arduino Kit from student1)
        p_ard = created_products[2]
        ord3 = Order(
            order_number="ORD-20261111-92B10F",
            buyer_id=student3.id,
            seller_id=student1.id,
            total_amount=p_ard.price,
            status="Pending",
            pickup_location="Campus Central Library (Ground Floor Helpdesk)",
            notes="Available anytime tomorrow morning.",
            created_at=datetime.utcnow() - timedelta(days=1),
            updated_at=datetime.utcnow() - timedelta(days=1),
        )
        db.session.add(ord3)
        db.session.flush()

        ord3_item = OrderItem(
            order_id=ord3.id,
            product_id=p_ard.id,
            quantity=1,
            unit_price=p_ard.price,
            subtotal=p_ard.price,
        )
        db.session.add(ord3_item)

        txn3 = Transaction(
            transaction_number="TXN-20261111-47A119",
            order_id=ord3.id,
            buyer_id=student3.id,
            seller_id=student1.id,
            amount=p_ard.price,
            payment_method="Campus UPI",
            payment_status="Completed",
            is_simulated=True,
            transaction_date=datetime.utcnow() - timedelta(days=1),
        )
        db.session.add(txn3)

        print("Seeding sample ERP complaints and resolution tickets...")
        comp1 = Complaint(
            ticket_number="TKT-20261105-E381A2",
            order_id=ord1.id,
            student_id=student3.id,
            subject="Inquiry regarding battery cover on Casio calculator",
            description="Just confirming if the original battery cover was replaced or if it is original manufacturer.",
            status="Resolved",
            admin_notes="Verified with seller student1: Battery was replaced last month with original Maxell CR2032 cell. Student satisfied.",
            created_at=datetime.utcnow() - timedelta(days=8),
            updated_at=datetime.utcnow() - timedelta(days=7),
        )
        db.session.add(comp1)

        comp2 = Complaint(
            ticket_number="TKT-20261110-B183C9",
            order_id=ord2.id,
            student_id=student4.id,
            subject="Pickup timing coordination request",
            description="Seller requested meeting after 5:30 PM due to extra classes; updating record.",
            status="Under Review",
            admin_notes="Advised both parties to use the SAC Plaza security desk as a safe drop point if timings conflict.",
            created_at=datetime.utcnow() - timedelta(days=2),
            updated_at=datetime.utcnow() - timedelta(days=1),
        )
        db.session.add(comp2)

        db.session.commit()
        print("Database successfully seeded with realistic campus demonstration data!")


if __name__ == "__main__":
    seed_database()
