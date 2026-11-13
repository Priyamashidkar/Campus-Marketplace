# Campus Marketplace – An E-Commerce ERP System

A full-stack, college-level web platform that integrates a campus-specific peer-to-peer e-commerce marketplace with an **Enterprise Resource Planning (ERP)** management system. Designed specifically for university students to safely buy, sell, exchange, and track academic essentials (textbooks, lab kits, calculators, stationery, dorm furniture) with complete administrator audit trails, real-time inventory management, dispute mediation, and visual analytics.

---

## 1. Key Features

### A. Student / Buyer Features
- **Campus Verified Registration**: Sign up with Full Name, Student ID (alphanumeric), university email, campus residence/hostel block, and password.
- **Product Catalog & Search**: Instant keyword search across title and description with category filtering (Books, Electronics, Hostel Essentials, Lab Equipment, Furniture, etc.), price bounds, condition filter (Brand New, Like New, Good, Fair), and multiple sort options.
- **Detailed Product Inspection**: High-resolution image preview, seller identity card, condition badge, verified buyer ratings, and real-time inventory availability.
- **Stock-Aware Shopping Cart**: Dynamic quantity updates with real-time stock limits, subtotal calculations, and item removals.
- **Atomic Checkout & Pickup Points**: Select designated campus handover hubs (Central Library, Student Activity Center, Hostel Common Rooms) with simulated payment options (Campus UPI, Cash on Campus Pickup, Campus SmartCard).
- **Order Tracking & Lifecycle**: Visual 4-step progress tracker (`Pending` → `Accepted` → `Ready for Pickup` → `Completed`), order cancellation with automated inventory replenishment, and post-purchase review ratings.
- **Dispute Resolution**: Lodge complaints referencing specific orders with direct administrator mediation and resolution notes.
- **Student Profile**: Maintain contact information and view comprehensive statistics on placed orders, active listings, and dispute tickets.

### B. Student Seller Features
- **Dual Role Capability**: Any registered student can act as both buyer and seller seamlessly from the same account.
- **Seller Hub Dashboard**: Visual overview of active listings, pending incoming orders, completed sales, and lifetime gross earnings.
- **Product Listing & Image Upload**: List products with secure image uploads, category tags, price, initial inventory quantity, item condition, and detailed descriptions.
- **Catalog Management**: Edit listings, adjust prices, toggle listing visibility (active vs. deactivated), or delete items.
- **Order Fulfillment Workflow**: Accept incoming orders, mark items as "Ready for Pickup", and finalize completed handovers.
- **Sales History**: Audit log of all completed transactions and revenue breakdown.

### C. Administrator ERP Control Center
- **Executive ERP Dashboard**: 6 KPI cards tracking total registered students, active sellers, total listings, pending vs. completed orders, gross transaction volume, and open dispute tickets.
- **Interactive Chart.js Visualizations**:
  - Monthly Marketplace Order Volume & Revenue trends.
  - Product Category Distribution breakdown (doughnut chart).
  - Inventory Stock Health breakdown (healthy vs. low-stock vs. out-of-stock).
- **Inventory Management**: Real-time stock audit, low-stock threshold triggers, out-of-stock alerts, and inline administrative stock adjustments.
- **User Management**: Central registry to search students/sellers and activate or suspend accounts.
- **Product Moderation**: Review and moderate listings across all categories to maintain campus policy compliance.
- **Category Taxonomy Management**: Create, edit, and toggle categories dynamically.
- **Order Orchestration**: Centralized supervisory view of all orders with filtering and administrative status overrides.
- **Financial Audit Log**: Complete ledger of simulated transactions with payment methods and audit numbers.
- **Dispute Ticket Resolution**: Review student complaints, inspect linked orders, record administrative resolution notes, and update ticket statuses (`Under Review`, `Resolved`, `Rejected`).
- **ERP Reports & Analytics**: Printable, exportable executive summary report with top-selling items and category performance tables.

---

## 2. Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons, Chart.js 4.4, Jinja2 templating.
- **Backend**: Python 3.12, Flask 3.0.3, Flask-Login 0.6.3, Werkzeug 3.0.3 (Secure password hashing), Python-Dotenv.
- **Database & ORM**: SQLAlchemy 2.0 (Flask-SQLAlchemy 3.1.1), PyMySQL 1.1.0 (MySQL support) with automatic zero-configuration fallback to SQLite (`sqlite:///campus_marketplace.db`).
- **Image Processing**: Pillow 10.3.0.
- **Testing**: pytest 8.2.2.
- **Version Control**: Git.

---

## 3. Project Directory Structure

```
Campus_Marketplace/
├── app/
│   ├── __init__.py                 # Application factory & context processors
│   ├── models/                     # Normalized SQLAlchemy Database Models
│   │   ├── __init__.py
│   │   ├── user.py                 # User (Student & Admin)
│   │   ├── product.py              # Product & Category
│   │   ├── inventory.py            # ERP Stock Tracking
│   │   ├── cart.py                 # Cart & CartItem
│   │   ├── order.py                # Order & OrderItem
│   │   ├── transaction.py          # Simulated Financial Audit Log
│   │   ├── complaint.py            # Student Grievance Tickets
│   │   └── rating.py               # Product Reviews & Ratings
│   ├── routes/                     # Modular MVC Blueprints
│   │   ├── __init__.py
│   │   ├── auth_routes.py          # Student & Admin Authentication
│   │   ├── public_routes.py        # Landing & About Pages
│   │   ├── student_routes.py       # Catalog, Cart, Checkout, Orders, Tracking
│   │   ├── seller_routes.py        # Seller Hub, Inventory & Fulfillment
│   │   └── admin_routes.py         # ERP Dashboard, Inventory, Orders, Reports
│   ├── services/                   # Business Logic & Integrations
│   │   ├── __init__.py
│   │   ├── email_verifier.py       # Campus ID & Domain Validation
│   │   ├── inventory_service.py    # Atomic Stock Operations & Replenishment
│   │   ├── order_service.py        # Transaction-Safe Checkout & State Machine
│   │   └── erp_service.py          # KPI Aggregations & Chart.js Live Data
│   ├── static/
│   │   ├── css/custom.css          # Navy blue & teal campus theme
│   │   ├── js/main.js              # Client interactions & alerts
│   │   ├── js/erp_charts.js        # Dynamic Chart.js dashboard integration
│   │   └── uploads/                # Product images & placeholder
│   └── templates/                  # Responsive Jinja2 Templates
│       ├── base.html
│       ├── auth/                   # login.html, register.html, admin_login.html
│       ├── public/                 # index.html, about.html
│       ├── student/                # marketplace.html, cart.html, checkout.html...
│       ├── seller/                 # dashboard.html, manage_products.html...
│       └── admin/                  # base_admin.html, dashboard.html, inventory.html...
├── database/
│   ├── __init__.py
│   └── seed.py                     # Demo data generator (users, products, orders)
├── tests/                          # Automated Pytest Suite (20 tests)
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures & in-memory database
│   ├── test_auth.py                # Auth, hashing, role restrictions
│   ├── test_catalog.py             # Product listing, search, category filter
│   ├── test_cart_order.py          # Cart operations, checkout, transactions
│   ├── test_inventory.py           # Atomic stock deduction & overselling safety
│   └── test_erp.py                 # ERP metrics, status toggles, complaints
├── config.py                       # Configuration classes & database fallback
├── run.py                          # Application entry point
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore patterns
└── README.md                       # Project documentation
```

---

## 4. Setup and Installation

### Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- Git

### Step 1: Clone or Navigate to the Project Directory
```bash
cd /path/to/Campus_Marketplace
```

### Step 2: Create and Activate a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate        # On macOS/Linux
# .\venv\Scripts\activate      # On Windows
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

**Database Configuration:**
- **Zero-Configuration SQLite (Default)**: Leave `DATABASE_URL=` empty in `.env`. The system will automatically use a local SQLite database (`campus_marketplace.db`).
- **MySQL Configuration (Optional)**: If you have a local or remote MySQL server:
  ```env
  DATABASE_URL=mysql+pymysql://username:password@localhost:3306/campus_marketplace
  ```

---

## 5. Seed Demonstration Data

The project includes an automated database seeder that creates realistic categories, student accounts, pre-owned campus products with inventory, orders, transactions, and dispute tickets for an immediate demonstration:

```bash
python database/seed.py
```

### Pre-Configured Demo Accounts:

| Role | Email | Password | Student ID | Purpose |
|------|-------|----------|------------|---------|
| **ERP Administrator** | `admin@campus.edu` | `Admin@123` | `ADMIN001` | Accesses the ERP Control Center |
| **Student 1 (Seller/Buyer)** | `student1@campus.edu` | `Student@123` | `CS2024001` | Active seller with listed books & electronics |
| **Student 2 (Seller/Buyer)** | `student2@campus.edu` | `Student@123` | `EC2024045` | Active seller with lab gear & hostel items |
| **Student 3 (Buyer)** | `student3@campus.edu` | `Student@123` | `ME2024012` | Has completed orders & reviews |
| **Student 4 (Buyer)** | `student4@campus.edu` | `Student@123` | `IT2024089` | Has pickup-ready order & dispute ticket |

---

## 6. Running the Application

Start the Flask application:
```bash
python run.py
```

Open your browser and navigate to:
- **Public Marketplace**: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
- **Student Login**: [http://127.0.0.1:5000/auth/login](http://127.0.0.1:5000/auth/login)
- **ERP Administrator Console**: [http://127.0.0.1:5000/auth/admin-login](http://127.0.0.1:5000/auth/admin-login)

---

## 7. Running Automated Tests

Run the complete test suite using `pytest`:
```bash
pytest tests/ -v
```

All 20 test cases will execute against an isolated in-memory test database, validating:
1. `test_auth.py`: Student registration, duplicate prevention, password hashing, login/logout, and role-based page restrictions.
2. `test_catalog.py`: Product listing, inventory initialization, keyword searching, category/price filters, and product detail rendering.
3. `test_cart_order.py`: Cart item additions, quantity modifications, cart clearing, atomic checkout, and transaction generation.
4. `test_inventory.py`: Atomic stock deduction, out-of-stock transitions, overselling prevention, inventory restoration on order cancellation, and admin stock updates.
5. `test_erp.py`: Executive KPI computations, student account suspension/activation, dispute ticket submission & admin resolution notes, and Chart.js API JSON integrity.

---

## 8. Academic Project Demonstration Flow

For an effective viva/evaluation presentation, follow this sequence:
1. **Explore the Public Landing Page**:
   - Show the hero section, campus stats, category grid, and recently listed items.
2. **Student Buyer Journey**:
   - Log in as `student3@campus.edu` (`Student@123`).
   - Search for "Mathematics" or filter by "Electronics".
   - View product details (condition badge, seller student ID, available inventory).
   - Add to cart, view cart quantity modifiers, and proceed to checkout.
   - Select "Campus Central Library" as the pickup point and place the order with "Campus UPI".
   - View the order confirmation with its unique `ORD-...` and `TXN-...` reference numbers.
   - Track progress in "Order Tracking" timeline.
3. **Student Seller Fulfillment**:
   - Log in as `student1@campus.edu` (`Student@123`).
   - Open "Seller Hub" to see active listings, incoming orders, and earnings.
   - Open "Incoming Orders" and click "Accept Order" or "Mark Ready for Pickup".
   - Add a new product listing with image upload and observe inventory creation.
4. **ERP Control Center Demonstration**:
   - Log in as `admin@campus.edu` (`Admin@123`) at `/auth/admin-login`.
   - Show the 6 summary cards and dynamic Chart.js visualizations (Monthly trends & category distribution).
   - Navigate to "Inventory Management": show real-time stock levels, low-stock warnings, and test adjusting a product's stock.
   - Navigate to "Orders" and show global campus order tracking.
   - Navigate to "Complaints": review an open student ticket, submit administrator resolution notes, and mark it as "Resolved".
   - Navigate to "Reports & KPIs": view the executive analytics report ready for printing/exporting.

---

## 9. Security & Architecture Highlights

- **Password Security**: Passwords are encrypted using Werkzeug's modern Scrypt/PBKDF2 hashing before database storage.
- **Referential Integrity**: Cascading relationships, foreign keys, and unique indexes guarantee database consistency.
- **Race Condition Prevention**: Atomic transactions with row-level locks protect inventory decrements during concurrent student checkouts.
- **Role Isolation**: Strict custom decorators (`@admin_required`, `@student_required`) protect ERP administrative views and seller features.
- **File Upload Protection**: Filenames are sanitized via Werkzeug `secure_filename`, restricted to image extensions (PNG, JPG, WEBP), and limited to 5MB.


## 📸 Project Screenshots

### 1. Homepage
![Homepage](screenshots/Homepage.png)

### 2. Marketplace
![Marketplace](screenshots/Marketplace.png)

### 3. Shopping Cart
![Cart](screenshots/Cart.png)

### 4. Order Success
![Order Success](screenshots/Order%20Success.png)

### 5. Pickup Location
![Pickup Location](screenshots/Pickup%20location.png)

### 6. Seller Dashboard
![Seller Dashboard](screenshots/Seller%20Dashboard.png)

### 7. Seller Listing Product
![Seller Listing Product](screenshots/Seller%20listing%20product.png)

### 8. ERP Dashboard
![ERP Dashboard](screenshots/ERP%20Dashboard.png)

### 9. ERP Inventory
![ERP Inventory](screenshots/ERP%20Inventory.png)
