from datetime import datetime
from flask_login import UserMixin
from extensions import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Perfil nutricional salvo
    weight_kg = db.Column(db.Float)
    height_cm = db.Column(db.Float)
    age = db.Column(db.Integer)
    sex = db.Column(db.String(1))
    activity_level = db.Column(db.String(100))
    goal = db.Column(db.String(100))
    goal_kcal = db.Column(db.Float)
    protein_goal = db.Column(db.Float)

    # Relacionamentos
    foods = db.relationship("Food", backref="owner", lazy=True,
                            foreign_keys="Food.user_id")
    diet_days = db.relationship("DietDay", backref="user", lazy=True)


class Food(db.Model):
    __tablename__ = "foods"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    name = db.Column(db.String(150), nullable=False)
    kcal_per_100g = db.Column(db.Float, nullable=False)
    protein_per_100g = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(60), default="Outros")
    unit_name = db.Column(db.String(50), nullable=True)
    g_per_unit = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DietDay(db.Model):
    __tablename__ = "diet_days"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD
    meals = db.relationship("Meal", backref="diet_day", lazy=True,
                            cascade="all, delete-orphan")

    __table_args__ = (db.UniqueConstraint("user_id", "date"),)


MEAL_TYPES = [
    "Café da Manhã",
    "Lanche da Manhã",
    "Almoço",
    "Lanche da Tarde",
    "Jantar",
    "Ceia",
]


class Meal(db.Model):
    __tablename__ = "meals"
    id = db.Column(db.Integer, primary_key=True)
    diet_day_id = db.Column(db.Integer, db.ForeignKey("diet_days.id"), nullable=False)
    meal_type = db.Column(db.String(50), nullable=False)
    items = db.relationship("MealItem", backref="meal", lazy=True,
                            cascade="all, delete-orphan")


class MealItem(db.Model):
    __tablename__ = "meal_items"
    id = db.Column(db.Integer, primary_key=True)
    meal_id = db.Column(db.Integer, db.ForeignKey("meals.id"), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey("foods.id"), nullable=False)
    quantity_g = db.Column(db.Float, nullable=False)
    food = db.relationship("Food")
