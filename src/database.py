"""
Configuração do banco de dados com SQLAlchemy (compatível com SQLAlchemy 2.x)
"""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ==========================================================
# BASE
# ==========================================================
Base = declarative_base()

# ==========================================================
# ENGINE
# ==========================================================
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DEBUG,
        future=True,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=settings.DEBUG,
        future=True,
    )

# ==========================================================
# SESSION
# ==========================================================
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
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


# ==========================================================
# INIT / DROP
# ==========================================================
def init_db() -> None:
    logger.info("Inicializando banco de dados...")

    from src.models import post, lead, interaction, metrics  # noqa

    Base.metadata.create_all(bind=engine)

    logger.info("Banco de dados inicializado com sucesso!")


def drop_db() -> None:
    if settings.is_production:
        raise RuntimeError("Não é permitido dropar banco em produção!")

    logger.warning("Removendo todas as tabelas do banco...")
    Base.metadata.drop_all(bind=engine)
    logger.info("Tabelas removidas!")


# ==========================================================
# HEALTH CHECK
# ==========================================================
class DatabaseHealthCheck:
    """Verifica saúde da conexão com o banco"""

    @staticmethod
    def check() -> bool:
        try:
            with get_db_context() as db:
                db.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error("Health check do banco falhou", error=str(e))
            return False

    @staticmethod
    def get_status() -> dict:
        try:
            with get_db_context() as db:
                # ⚠️ SQLAlchemy 2.x exige text()
                db.execute(text("SELECT 1"))

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
                    },
                }

        except Exception as e:
            logger.error("Erro no banco de dados", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
            }


# ==========================================================
# TESTE LOCAL
# ==========================================================
if __name__ == "__main__":
    init_db()

    health = DatabaseHealthCheck()
    print(f"Database healthy: {health.check()}")
    print(f"Database status: {health.get_status()}")
