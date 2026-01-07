from app import app, db
from models import Subscription


subscriptions = [
    {"name": "Monthly", "price": 3000.0, "duration_days": 30},
    {"name": "Quarterly", "price": 8000.0, "duration_days": 90},
    {"name": "Annual", "price": 30000.0, "duration_days": 365}
]



# ---------- Seeding ---------- #

with app.app_context():
    print("🔄 Resetting database...")
    db.drop_all()
    db.create_all()

    print("📦 Seeding subscriptions...")
    subscription_map = {}
    for s in subscriptions:
        sub = Subscription(
            name=s["name"],
            price=s["price"],
            duration_days=s["duration_days"]
        )
        db.session.add(sub)
        db.session.flush()
        subscription_map[s["name"]] = sub.id

    db.session.commit()
    print("✅ Seeding complete.")
