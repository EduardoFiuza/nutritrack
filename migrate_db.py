import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# Pegando a URl do banco (SQLite local ou PostgreSQL do Supabase)
# O Render usa postgres://, o SQLAlchemy exige postgresql://
db_url = os.environ.get("DATABASE_URL", "sqlite:///nutritrack.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

print("Conectando ao Banco de Dados...")
engine = create_engine(db_url)

with engine.connect() as conn:
    print("Adicionando colunas `unit_name` e `g_per_unit` na tabela `foods`...")
    
    try:
        if "sqlite" in db_url:
            conn.execute(text("ALTER TABLE foods ADD COLUMN unit_name VARCHAR(50)"))
            conn.execute(text("ALTER TABLE foods ADD COLUMN g_per_unit FLOAT"))
        else:
            # Sintaxe do Postgres
            conn.execute(text("ALTER TABLE foods ADD COLUMN IF NOT EXISTS unit_name VARCHAR(50)"))
            conn.execute(text("ALTER TABLE foods ADD COLUMN IF NOT EXISTS g_per_unit FLOAT"))
        
        conn.commit()
        print("Migracao concluida com sucesso!")
    except Exception as e:
        print("Erro (possivelmente as colunas ja existem):", str(e))
