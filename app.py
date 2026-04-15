import os
from dotenv import load_dotenv
from flask import Flask
from extensions import db, login_manager, bcrypt

load_dotenv()


def create_app():
    app = Flask(__name__)

    # Config
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///nutritrack.db"
    )
    # Render usa 'postgres://' mas SQLAlchemy precisa de 'postgresql://'
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgres://"):
        app.config["SQLALCHEMY_DATABASE_URI"] = app.config["SQLALCHEMY_DATABASE_URI"].replace(
            "postgres://", "postgresql://", 1
        )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Extensões
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "warning"

    # Blueprints
    from auth import auth_bp
    from routes import main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # Criar tabelas + seed
    with app.app_context():
        from models import User, Food, DietDay, Meal, MealItem
        db.create_all()
        _seed_foods()

    return app


def _seed_foods():
    from models import Food
    if Food.query.filter_by(user_id=None).count() == 0:
        foods = [
            # (nome, kcal/100g, prot/100g, categoria)
            ("Banana", 89, 1.1, "Frutas"),
            ("Maçã", 52, 0.3, "Frutas"),
            ("Laranja", 47, 0.9, "Frutas"),
            ("Morango", 32, 0.7, "Frutas"),
            ("Manga", 60, 0.8, "Frutas"),
            ("Abacate", 160, 2.0, "Frutas"),
            ("Melancia", 30, 0.6, "Frutas"),
            ("Mamão", 43, 0.5, "Frutas"),
            ("Uva", 69, 0.7, "Frutas"),
            ("Pera", 57, 0.4, "Frutas"),
            ("Arroz Branco Cozido", 130, 2.7, "Cereais"),
            ("Arroz Integral Cozido", 111, 2.6, "Cereais"),
            ("Feijão Cozido", 77, 4.8, "Cereais"),
            ("Lentilha Cozida", 116, 9.0, "Cereais"),
            ("Grão de Bico Cozido", 164, 8.9, "Cereais"),
            ("Aveia", 389, 17.0, "Cereais"),
            ("Massa Cozida", 131, 5.0, "Cereais"),
            ("Pão Francês", 300, 9.4, "Cereais"),
            ("Pão Integral", 247, 9.7, "Cereais"),
            ("Milho Cozido", 86, 3.2, "Cereais"),
            ("Frango Peito Grelhado", 165, 31.0, "Carnes"),
            ("Carne Bovina Patinho", 219, 20.0, "Carnes"),
            ("Ovo Cozido", 155, 13.0, "Carnes"),
            ("Atum em Lata", 116, 25.5, "Carnes"),
            ("Salmão Grelhado", 208, 28.0, "Carnes"),
            ("Tilápia Grelhada", 128, 26.0, "Carnes"),
            ("Camarão Cozido", 99, 24.0, "Carnes"),
            ("Carne Suína Lombo", 182, 27.0, "Carnes"),
            ("Peru Peito", 157, 30.0, "Carnes"),
            ("Leite Integral", 61, 3.2, "Laticínios"),
            ("Leite Desnatado", 35, 3.6, "Laticínios"),
            ("Iogurte Natural", 61, 3.5, "Laticínios"),
            ("Iogurte Grego", 97, 9.0, "Laticínios"),
            ("Queijo Minas", 264, 17.4, "Laticínios"),
            ("Queijo Mussarela", 300, 22.2, "Laticínios"),
            ("Queijo Cottage", 98, 11.1, "Laticínios"),
            ("Whey Protein", 370, 75.0, "Laticínios"),
            ("Alface", 14, 1.4, "Vegetais"),
            ("Tomate", 18, 0.9, "Vegetais"),
            ("Cenoura", 41, 0.9, "Vegetais"),
            ("Brócolis", 34, 2.8, "Vegetais"),
            ("Espinafre", 23, 2.9, "Vegetais"),
            ("Batata Inglesa Cozida", 77, 2.0, "Vegetais"),
            ("Batata Doce Cozida", 86, 1.6, "Vegetais"),
            ("Cebola", 40, 1.1, "Vegetais"),
            ("Abobrinha", 17, 1.2, "Vegetais"),
            ("Beterraba Cozida", 44, 1.7, "Vegetais"),
            ("Pepino", 15, 0.7, "Vegetais"),
            ("Couve", 28, 3.0, "Vegetais"),
            ("Azeite de Oliva", 884, 0.0, "Gorduras"),
            ("Amendoim", 567, 25.8, "Gorduras"),
            ("Castanha do Pará", 659, 14.3, "Gorduras"),
            ("Amêndoa", 579, 21.2, "Gorduras"),
            ("Pasta de Amendoim", 588, 25.1, "Gorduras"),
            ("Mel", 304, 0.3, "Outros"),
            ("Açúcar", 387, 0.0, "Outros"),
            ("Chocolate 70%", 598, 7.8, "Outros"),
            ("Tapioca", 345, 0.2, "Outros"),
            ("Granola", 471, 10.4, "Outros"),
        ]
        for name, kcal, prot, cat in foods:
            db.session.add(Food(name=name, kcal_per_100g=kcal,
                                protein_per_100g=prot, category=cat, user_id=None))
        db.session.commit()


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
