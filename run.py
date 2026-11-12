import os
from app import create_app, db

app = create_app(os.environ.get("FLASK_ENV", "development"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    port = int(os.environ.get("PORT", 5000))
    print("\n" + "=" * 65)
    print("   CAMPUS MARKETPLACE – AN E-COMMERCE ERP SYSTEM")
    print("=" * 65)
    print(f" * Public Marketplace:   http://127.0.0.1:{port}/")
    print(f" * Student Login:        http://127.0.0.1:{port}/auth/login")
    print(f" * ERP Administrator:    http://127.0.0.1:{port}/auth/admin-login")
    print(" * Default Admin Email:  admin@campus.edu  | Pass: Admin@123")
    print(" * Demo Student Email:   student1@campus.edu | Pass: Student@123")
    print("=" * 65 + "\n")
    app.run(host="0.0.0.0", port=port, debug=True)
