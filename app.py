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
    # Lista expandida de alimentos brasileiros e globais
    foods = [
        # Frutas
        ("Banana Prata", 89, 1.1, "Frutas"),
        ("Maçã Fugji", 52, 0.3, "Frutas"),
        ("Laranja Pera", 47, 0.9, "Frutas"),
        ("Morango", 32, 0.7, "Frutas"),
        ("Manga Palmer", 60, 0.8, "Frutas"),
        ("Abacate", 160, 2.0, "Frutas"),
        ("Melancia", 30, 0.6, "Frutas"),
        ("Mamão Papaia", 43, 0.5, "Frutas"),
        ("Uva Thompson", 69, 0.7, "Frutas"),
        ("Abacaxi", 48, 0.5, "Frutas"),
        ("Limão", 29, 1.1, "Frutas"),
        ("Pera", 57, 0.4, "Frutas"),
        ("Melão", 34, 0.8, "Frutas"),
        
        # Cereais e Grãos
        ("Arroz Branco Cozido", 130, 2.7, "Cereais"),
        ("Arroz Integral Cozido", 111, 2.6, "Cereais"),
        ("Feijão Carioca Cozido", 76, 4.8, "Cereais"),
        ("Feijão Preto Cozido", 77, 4.5, "Cereais"),
        ("Lentilha Cozida", 116, 9.0, "Cereais"),
        ("Grão de Bico Cozido", 164, 8.9, "Cereais"),
        ("Aveia em Flocos", 389, 17.0, "Cereais"),
        ("Massa (Macarrão) Cozida", 131, 5.0, "Cereais"),
        ("Cuscuz Nordestino", 112, 2.3, "Cereais"),
        ("Tapioca (Goma)", 240, 0.0, "Cereais"),
        ("Pão Francês", 300, 9.4, "Cereais"),
        ("Pão Integral", 247, 9.7, "Cereais"),
        ("Pão de Queijo", 250, 5.0, "Cereais"),
        ("Milho Verde Cozido", 108, 3.2, "Cereais"),
        ("Pipoca (sem óleo)", 375, 11.0, "Cereais"),
        
        # Carnes e Proteínas
        ("Frango Peito Grelhado", 165, 31.0, "Carnes"),
        ("Frango Sobrecoxa Assada", 232, 25.0, "Carnes"),
        ("Carne Bovina Patinho Grelhado", 219, 35.0, "Carnes"),
        ("Carne Bovina Alcatra", 241, 31.0, "Carnes"),
        ("Ovo de Galinha Cozido", 155, 13.0, "Carnes"),
        ("Ovo Frito", 196, 13.6, "Carnes"),
        ("Ovo Mexido", 166, 10.0, "Carnes"),
        ("Atum ao Natural", 116, 25.5, "Carnes"),
        ("Salmão Grelhado", 208, 28.0, "Carnes"),
        ("Tilápia Grelhada", 128, 26.0, "Carnes"),
        ("Presunto Cozido", 145, 16.5, "Carnes"),
        ("Peito de Peru Defumado", 107, 24.0, "Carnes"),
        ("Patinho Moído", 212, 26.0, "Carnes"),
        ("Coxão Mole", 219, 28.0, "Carnes"),
        
        # Laticínios
        ("Leite Desnatado", 35, 3.6, "Laticínios"),
        ("Leite Semidesnatado", 45, 3.4, "Laticínios"),
        ("Leite Integral", 61, 3.2, "Laticínios"),
        ("Requeijão Cremoso", 257, 9.3, "Laticínios"),
        ("Requeijão Light", 170, 12.0, "Laticínios"),
        ("Queijo Mussarela", 300, 22.2, "Laticínios"),
        ("Queijo Minas Frescal", 264, 17.4, "Laticínios"),
        ("Queijo Prato", 350, 25.0, "Laticínios"),
        ("Queijo Cottage", 98, 11.1, "Laticínios"),
        ("Iogurte Natural Integral", 61, 3.5, "Laticínios"),
        ("Iogurte Grego", 97, 9.0, "Laticínios"),
        ("Whey Protein Concentrado", 400, 80.0, "Laticínios"),
        ("Manteiga", 717, 0.8, "Laticínios"),
        
        # Vegetais
        ("Alface Crespa", 15, 1.3, "Vegetais"),
        ("Tomate Cereja", 18, 0.9, "Vegetais"),
        ("Cenoura Crua", 41, 0.9, "Vegetais"),
        ("Brócolis Cozido", 34, 2.8, "Vegetais"),
        ("Abóbora Cabotiá Cozida", 48, 1.0, "Vegetais"),
        ("Batata Inglesa Cozida", 77, 2.0, "Vegetais"),
        ("Batata Doce Cozida", 86, 1.6, "Vegetais"),
        ("Beterraba Crua", 43, 1.6, "Vegetais"),
        ("Abobrinha Refogada", 25, 1.1, "Vegetais"),
        ("Chuchu Cozido", 19, 0.4, "Vegetais"),
        ("Espinafre Cozido", 23, 2.9, "Vegetais"),
        ("Cebola", 40, 1.1, "Vegetais"),
        
        # Outros / Gorduras
        ("Azeite de Oliva Extra Virgem", 884, 0.0, "Gorduras"),
        ("Manteiga com Sal", 717, 0.8, "Gorduras"),
        ("Margarina", 717, 0.5, "Gorduras"),
        ("Pasta de Amendoim Integral", 588, 25.1, "Gorduras"),
        ("Castanha de Caju", 553, 18.2, "Gorduras"),
        ("Nozes", 654, 15.0, "Gorduras"),
        ("Mel de Abelha", 304, 0.3, "Outros"),
        ("Granola Tradicional", 471, 10.4, "Outros"),
        ("Chocolate Meio Amargo", 546, 4.9, "Outros"),
        ("Açúcar Branco", 387, 0.0, "Outros"),
        ("Maionese Tradicional", 680, 1.0, "Outros"),
        ("Catchup", 112, 1.2, "Outros"),
        ("Mostarda", 66, 4.4, "Outros"),
    ]
    
    # Repopulamos apenas o que falta (evita duplicatas)
    for name, kcal, prot, cat in foods:
        exists = Food.query.filter_by(name=name, user_id=None).first()
        if not exists:
            db.session.add(Food(name=name, kcal_per_100g=kcal,
                                protein_per_100g=prot, category=cat, user_id=None))
    db.session.commit()


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
