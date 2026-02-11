# setup_db.py
from app import app, db
from models import  Subscription

subscriptions = [
    {"name": "Daily", "price": 400.0, "duration_days": 1},
    {"name": "Weekly", "price": 1500.0, "duration_days": 7},
    {"name": "2 Weeks", "price": 2500.0, "duration_days": 14},
    {"name": "Monthly", "price": 4000.0, "duration_days": 30},
    {"name": "Stdents Monthly", "price": 3000.0, "duration_days": 30},
    {"name": "Quarterly", "price": 10000.0, "duration_days": 90},
    {"name": "Personal Trainer" } 

]

def create_tables_and_seed():
    with app.app_context():
        # 1️⃣ Create all tables
        db.create_all()
        print("✅ Tables created.")

        # 4️⃣ Seed Subscriptions
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
        print("🎉 Database seeding completed!")

if __name__ == "__main__":
    create_tables_and_seed()
