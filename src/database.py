"""
Configuração do banco de dados com SQLAlchemy
"""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Base para os models
Base = declarative_base()

# Configuração da engine
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite: configurações específicas
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DEBUG,
    )
    
    # Habilitar foreign keys no SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # PostgreSQL: configurações de pool
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=settings.DEBUG,
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency para obter sessão do banco de dados
    Usado com FastAPI Depends
    
    Yields:
        Session do SQLAlchemy
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager para usar sessão do banco
    
    Uso:
        with get_db_context() as db:
            db.query(Model).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Erro no banco de dados", error=str(e))
        raise
    finally:
        db.close()


def init_db() -> None:
    """
    Inicializa o banco de dados
    Cria todas as tabelas definidas nos models
    """
    logger.info("Inicializando banco de dados...")
    
    # Import todos os models aqui para que sejam registrados
    from src.models import post, lead, interaction, metrics
    
    # Criar todas as tabelas
    Base.metadata.create_all(bind=engine)
    
    logger.info("Banco de dados inicializado com sucesso!")


def drop_db() -> None:
    """
    Remove todas as tabelas do banco
    ⚠️ CUIDADO: Apenas para desenvolvimento/testes
    """
    if settings.is_production:
        raise RuntimeError("Não é permitido dropar banco em produção!")
    
    logger.warning("Removendo todas as tabelas do banco...")
    Base.metadata.drop_all(bind=engine)
    logger.info("Tabelas removidas!")


class DatabaseHealthCheck:
    """Verifica saúde da conexão com o banco"""
    
    @staticmethod
    def check() -> bool:
        """
        Verifica se o banco está acessível
        
        Returns:
            True se conectado, False caso contrário
        """
        try:
            with get_db_context() as db:
                db.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error("Health check do banco falhou", error=str(e))
            return False
    
    @staticmethod
    def get_status() -> dict:
        """
        Retorna status detalhado do banco
        
        Returns:
            Dict com informações do banco
        """
        try:
            with get_db_context() as db:
                # Verificar conexão
                db.execute("SELECT 1")
                
                # Obter algumas estatísticas
                from src.models.post import Post
                from src.models.lead import Lead
                
                total_posts = db.query(Post).count()
                total_leads = db.query(Lead).count()
                
                return {
                    "status": "healthy",
                    "database": settings.DATABASE_URL.split("://")[0],
                    "stats": {
                        "total_posts": total_posts,
                        "total_leads": total_leads,
                    }
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Exemplo de uso
if __name__ == "__main__":
    # Inicializar banco
    init_db()
    
    # Verificar saúde
    health = DatabaseHealthCheck()
    print(f"Database healthy: {health.check()}")
    print(f"Database status: {health.get_status()}")