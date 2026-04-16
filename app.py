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

    # Context Processor para ambiente
    @app.context_processor
    def inject_env():
        return dict(app_env=os.environ.get("APP_ENV", "production").lower())

    # Blueprints
    from auth import auth_bp
    from routes import main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # Criar tabelas + seed + migrações manuais
    with app.app_context():
        from models import User, Food, DietDay, Meal, MealItem
        db.create_all()
        # Migração manual de colunas novas (caso existam)
        _run_manual_migrations()
        _seed_foods()
    
    return app

def _run_manual_migrations():
    from extensions import db
    from sqlalchemy import text
    try:
        # Tenta adicionar as colunas se não existirem (Postgres/SQLite)
        # O 'IF NOT EXISTS' não funciona no SQLite antigo, então usamos try/except
        try:
            db.session.execute(text("ALTER TABLE foods ADD COLUMN unit_name VARCHAR(50)"))
        except:
            db.session.rollback()
        
        try:
            db.session.execute(text("ALTER TABLE foods ADD COLUMN g_per_unit FLOAT"))
        except:
            db.session.rollback()
        
        db.session.commit()
    except Exception as e:
        print("Migração automática ignorada ou já realizada:", str(e))


def _seed_foods():
    from models import Food
    foods = [
        # (nome, kcal/100g, prot/100g, categoria, unit_name, g_per_unit)
        ("Banana Prata", 89, 1.1, "Frutas", "Unidade", 85),
        ("Banana", 89, 1.1, "Frutas", "Unidade", 85),
        ("Maçã Fugji", 52, 0.3, "Frutas", "Unidade", 130),
        ("Maçã", 52, 0.3, "Frutas", "Unidade", 130),
        ("Ovo Cozido", 155, 13.0, "Carnes", "Unidade", 50),
        ("Ovo de Galinha Cozido", 155, 13.0, "Carnes", "Unidade", 50),
        ("Ovo Frito", 196, 13.6, "Carnes", "Unidade", 50),
        ("Pão Francês", 300, 9.4, "Cereais", "Unidade", 50),
        ("Pão Integral", 247, 9.7, "Cereais", "Fatia", 25),
        ("Requeijão Cremoso", 257, 9.3, "Laticínios", "Colher (sopa)", 20),
        ("Requeijão Light", 170, 12.0, "Laticínios", "Colher (sopa)", 20),
        ("Arroz Branco Cozido", 130, 2.7, "Cereais", "Colher (sopa)", 25),
        ("Feijão Carioca Cozido", 76, 4.8, "Cereais", "Colher (sopa)", 25),
        ("Feijão Cozido", 76, 4.8, "Cereais", "Colher (sopa)", 25),
        ("Azeite de Oliva", 884, 0.0, "Gorduras", "Colher (sopa)", 13),
        ("Mel", 304, 0.3, "Outros", "Colher (sopa)", 15),
    ]
    
    for item in foods:
        name, kcal, prot, cat = item[0], item[1], item[2], item[3]
        unit = item[4]
        grams = item[5]
        
        # Procura tanto pelo nome exato quanto por versões globais (user_id=None)
        food = Food.query.filter_by(name=name, user_id=None).first()
        if not food:
            food = Food(name=name, kcal_per_100g=kcal, protein_per_100g=prot, 
                        category=cat, unit_name=unit, g_per_unit=grams, user_id=None)
            db.session.add(food)
        else:
            # FORÇA a atualização se estiver vazio
            if not food.unit_name: food.unit_name = unit
            if not food.g_per_unit: food.g_per_unit = grams
                
    db.session.commit()


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
