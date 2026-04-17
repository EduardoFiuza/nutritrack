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

    # Criar tabelas + seed
    with app.app_context():
        from models import User, Food, DietDay, Meal, MealItem
        db.create_all()
        _seed_foods()
    
    return app


# _run_manual_migrations foi removido pois os modelos agora estão atualizados.



def _seed_foods():
    from models import Food
    foods = [
        # (nome, kcal/100g, prot, carb, gord, categoria, unit_name, g_per_unit)
        ("Alface Crespa", 15, 1.3, 1.7, 0.2, "Vegetais", "Maço", 250),
        ("Arroz Branco Cozido", 128, 2.5, 28.1, 0.2, "Cereais", "Colher (sopa)", 25),
        ("Arroz Integral Cozido", 124, 2.6, 25.8, 1.0, "Cereais", "Colher (sopa)", 25),
        ("Aveia em Flocos", 394, 13.9, 66.6, 8.5, "Cereais", "Colher (sopa)", 10),
        ("Azeite de Oliva", 884, 0.0, 0.0, 100.0, "Gorduras", "Colher (sopa)", 13),
        ("Banana Prata", 98, 1.3, 26.0, 0.3, "Frutas", "Unidade", 85),
        ("Banana Nanica", 92, 1.4, 23.8, 0.1, "Frutas", "Unidade", 90),
        ("Batata Doce Cozida", 77, 0.6, 18.4, 0.1, "Cereais", "Unidade", 150),
        ("Batata Inglesa Cozida", 52, 1.2, 11.9, 0.0, "Cereais", "Unidade", 120),
        ("Brócolis Cozido", 25, 2.1, 4.4, 0.5, "Vegetais", "Ramo", 30),
        ("Café sem Açúcar", 1, 0.1, 0.0, 0.0, "Bebidas", "Xícara", 50),
        ("Carne Moída (Patinho)", 219, 35.9, 0.0, 7.3, "Proteínas", "Colher (sopa)", 25),
        ("Cenoura Crua", 34, 1.3, 7.7, 0.2, "Vegetais", "Unidade", 100),
        ("Cuscuz de Milho", 112, 2.2, 24.8, 0.1, "Cereais", "Colher (sopa)", 25),
        ("Feijão Carioca Cozido", 76, 4.8, 13.6, 0.5, "Cereais", "Concha média", 130),
        ("Feijão Preto Cozido", 77, 4.5, 14.0, 0.5, "Cereais", "Concha média", 130),
        ("Filé de Frango Grelhado", 159, 32.0, 0.0, 2.5, "Proteínas", "Filé médio", 100),
        ("Filé de Tilápia Grelhado", 128, 26.0, 0.0, 2.7, "Proteínas", "Filé médio", 100),
        ("Iogurte Natural", 51, 4.1, 5.0, 3.0, "Laticínios", "Copo", 170),
        ("Laranja", 46, 0.9, 11.5, 0.1, "Frutas", "Unidade", 130),
        ("Leite Desnatado", 35, 3.3, 5.0, 0.1, "Laticínios", "Copo", 200),
        ("Leite Integral", 60, 3.2, 4.8, 3.3, "Laticínios", "Copo", 200),
        ("Maçã Fuji", 56, 0.3, 15.2, 0.0, "Frutas", "Unidade", 130),
        ("Macarrão Cozido", 158, 5.8, 30.7, 0.9, "Cereais", "Pegador", 60),
        ("Mamão Formosa", 45, 0.8, 11.6, 0.1, "Frutas", "Fatia", 100),
        ("Mandioca Cozida", 125, 0.6, 30.1, 0.3, "Cereais", "Pedaço", 100),
        ("Manteiga com Sal", 726, 0.4, 0.0, 81.6, "Gorduras", "Ponta de faca", 5),
        ("Mel", 304, 0.3, 82.4, 0.0, "Doces", "Colher (sopa)", 15),
        ("Ovo de Galinha Cozido", 155, 13.3, 0.6, 11.2, "Proteínas", "Unidade", 50),
        ("Ovo Frito", 196, 13.6, 0.6, 15.4, "Proteínas", "Unidade", 50),
        ("Pão de Queijo", 348, 5.1, 34.2, 21.6, "Outros", "Unidade", 30),
        ("Pão Francês", 300, 9.4, 58.7, 3.1, "Cereais", "Unidade", 50),
        ("Pão Integral", 253, 9.4, 49.9, 3.7, "Cereais", "Fatia", 25),
        ("Peito de Peru", 111, 21.0, 2.0, 2.1, "Proteínas", "Fatia", 15),
        ("Presunto Cozido", 145, 16.5, 2.1, 7.9, "Proteínas", "Fatia", 15),
        ("Queijo Mussarela", 280, 22.6, 3.0, 20.1, "Laticínios", "Fatia", 20),
        ("Queijo Minas Frescal", 243, 17.4, 3.2, 17.8, "Laticínios", "Fatia", 30),
        ("Requeijão Cremoso", 257, 9.3, 3.5, 23.4, "Laticínios", "Colher (sopa)", 20),
        ("Suco de Laranja Natural", 45, 0.7, 10.4, 0.2, "Bebidas", "Copo", 200),
        ("Tapioca (Goma)", 241, 0.0, 60.0, 0.0, "Cereais", "Colher (sopa)", 20),
        ("Tomate Cru", 15, 1.1, 3.1, 0.2, "Vegetais", "Unidade", 80),
        ("Whey Protein (Média)", 380, 80.0, 5.0, 4.0, "Suplementos", "Scoop", 30),
    ]
    
    for item in foods:
        name, kcal, prot, carb, fat, cat, unit, grams = item
        
        # Procura tanto pelo nome exato quanto por versões globais (user_id=None)
        food = Food.query.filter_by(name=name, user_id=None).first()
        if not food:
            food = Food(name=name, kcal_per_100g=kcal, 
                        protein_per_100g=prot, 
                        carbs_per_100g=carb,
                        fat_per_100g=fat,
                        category=cat, 
                        unit_name=unit, 
                        g_per_unit=grams, 
                        user_id=None)
            db.session.add(food)
        else:
            # Atualiza os valores se necessário
            food.kcal_per_100g = kcal
            food.protein_per_100g = prot
            food.carbs_per_100g = carb
            food.fat_per_100g = fat
            food.category = cat
            food.unit_name = unit
            food.g_per_unit = grams
                
    db.session.commit()



if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

